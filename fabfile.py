import os
import time
import warnings

import fabric2 as fabric
import paramiko
import requests
import json


# Disable warnings coming from Paramiko package:
warnings.filterwarnings(action='ignore', module='.*paramiko.*')


SITENAME = os.environ['SITENAME']
VSCALE_TOKEN = os.environ['VSCALE_TOKEN']
VM_ROOT_PASS = os.environ['VM_ROOT_PASS']
VM_USER_NAME = os.environ['VM_USER_NAME']
VM_USER_PASS = os.environ['VM_USER_PASS']
USE_HTTPS = os.environ['USE_HTTPS']
CDN_FTP_SERVER = os.environ.get('CDN_FTP_SERVER', 'ftp.selcdn.ru')
CDN_USER = os.environ['CDN_USER']
CDN_PASS = os.environ['CDN_PASS']
CDN_CERT_PATH = os.environ['CDN_CERT_PATH']
REPO_URL = os.environ['REPO_URL']
BRANCH = os.environ['REPO_BRANCH']
DB_NAME = os.environ['DB_NAME']
DB_USER = os.environ['DB_USER']
DB_PASS = os.environ['DB_PASS']
CERT_YEAR = os.environ['HTTPS_CERT_YEAR']
MAX_BODY_SIZE = os.environ['MAX_BODY_SIZE']

####
# These vars are not used inside scripts, but being written into .env on
# deploy server:
# * SECRET_KEY (defined in local .env, not indexed by git)
####

DOMAIN = '.'.join(SITENAME.split('.')[-2:])

INSTALL_PACKAGES = (
    'python3.6', 'nginx', 'postgresql', 'sshpass', 'git', 'vim',
    'python3-venv',
)
DJANGO_PROJECT_NAME = 'ubio'


@fabric.task
def create_server(ctx, name):
    assert not isinstance(ctx, fabric.Connection)  # no support fo --host arg

    # 1) Create new scalet, bind DNS to it and add address to known_hosts:
    address = create_scalet(name)
    update_dns(address)

    # 2) Establish a connection with root access rights to install software,
    # create admin user and copy certificates:
    root = fabric.Connection(address, user='root', connect_kwargs={
        'password': VM_ROOT_PASS
    })
    root.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    install_system_packages(root)
    copy_certificates(root)
    create_user(root)

    # 3) Establish a connection on part of the non-root user (site admin),
    # prepare home folder, clone the repository and setup the database:
    user = fabric.Connection(address, user=VM_USER_NAME, connect_kwargs={
        'password': VM_USER_PASS
    })
    user.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    clone_repo(user)
    write_env(user)
    create_database(user)

    # 4) On part of root, create configuration files and services:
    create_gunicorn_service(root)
    create_nginx_config(root)

    # 5) Update the repository, make migrations, install python packages.
    # Then tart services (on part of root).
    update_repo(user)
    gunicorn_service(root, 'start')
    nginx_service(root, 'restart')


@fabric.task
def update(ctx):
    root = fabric.Connection(SITENAME, user='root', connect_kwargs={
        'password': VM_ROOT_PASS
    })
    user = fabric.Connection(SITENAME, user=VM_USER_NAME, connect_kwargs={
        'password': VM_USER_PASS
    })
    for conn in (root, user):
        conn.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    # Load changes, write .env:
    write_env(user)
    update_repo(user)

    # Update services configurations and restart them:
    gunicorn_service(root, 'stop')
    nginx_service(root, 'stop')
    create_gunicorn_service(root)
    create_nginx_config(root)
    gunicorn_service(root, 'start')
    nginx_service(root, 'start')


def vscale(url, method='get', data=None, token=VSCALE_TOKEN):
    fn = getattr(requests, method)
    headers = {'X-Token': token}
    if data:
        headers['Content-Type'] = 'application/json;charset=UTF-8'
        response = fn(url, headers=headers, data=json.dumps(data))
    else:
        response = fn(url, headers=headers)
    if 200 <= response.status_code <= 299:
        return response.json()
    raise RuntimeError(response)


def create_scalet(name, rplan='small', location='msk0', password=VM_ROOT_PASS):
    print('[FAB] * create_scalet()')
    response = vscale('https://api.vscale.io/v1/scalets', method='post', data={
        'make_from': 'ubuntu_18.04_64_001_master',
        'name': name,
        'rplan': rplan,
        'do_start': True,
        'password': password,
        'location': location,
    })
    ctid = response['ctid']
    while response['status'] != 'started':
        time.sleep(1)
        response = vscale(f'https://api.vscale.io/v1/scalets/{ctid}')
    return response['public_address']['address']


def update_dns(address, domain=DOMAIN, sitename=SITENAME, ttl=300):
    print('[FAB] * update_dns()')
    # 1) First we find the domain ID:
    response = vscale('https://api.vscale.io/v1/domains')
    dom_id = [rec['id'] for rec in response if rec['name'] == domain][0]

    # 2) Then we list all domain records related to this domain and try to find
    # the record related to our site:
    all_sites = vscale(f'https://api.vscale.io/v1/domains/{dom_id}/records')

    # 3) Since we need both sitename (e.g. example.com) and www.sitename,
    # we iterate through these names in cycle:
    for name in (sitename, f'www.{sitename}'):
        records = [rec for rec in all_sites
                   if rec['name'] == name and rec['type'] in {'A', 'CNAME'}]
        assert 0 <= len(records) <= 1

        data = {
            'content': address,
            'ttl': ttl,
            'type': 'A',
            'name': name
        }

        # 4) If there is no site records, we create one:
        if not records:
            vscale(f'https://api.vscale.io/v1/domains/{dom_id}/records/',
                   method='post', data=data)
            continue

        # 5) If name was already registered, we need to find this record and
        # make sure that its type is 'A'. If its type is 'CNAME', we need to
        # first delete that record (otherwise, Vscale API will return 400).
        # Otherwise, we issue PUT request to update the record.
        rid = records[0]['id']
        if records[0]['type'] != data['type']:
            vscale(f'https://api.vscale.io/v1/domains/{dom_id}/records/{rid}',
                   method='delete')
            vscale(f'https://api.vscale.io/v1/domains/{dom_id}/records/',
                   method='post', data=data)
        else:
            vscale(f'https://api.vscale.io/v1/domains/{dom_id}/records/{rid}',
                   method='put', data=data)


def copy_certificates(
        c, user=CDN_USER, password=CDN_PASS, ftp_server=CDN_FTP_SERVER,
        cert_path=CDN_CERT_PATH, sitename=SITENAME):
    ftp = f'SSHPASS={password} sshpass -e sftp {user}@{ftp_server}:/{cert_path}'
    local_path = f'/etc/ssl/'

    c.run('mkdir -p ~/.ssh', echo=True)
    c.run(f'ssh-keyscan -H {ftp_server} >> ~/.ssh/known_hosts', echo=True)
    c.run(f'mkdir -p {local_path}', echo=True)
    c.run(f'{ftp}/{sitename}*.crt /etc/ssl/certs/', echo=True)
    c.run(f'{ftp}/{sitename}*.key /etc/ssl/private/', echo=True)


def create_user(c, username=VM_USER_NAME, password=VM_USER_PASS):
    if c.run(f'adduser --quiet --disabled-password --gecos "" {username}',
             warn=True, echo=True).exited == 0:
        c.run(f'echo "{username}:{password}" | chpasswd')
        c.run(f'echo "{username} ALL=(postgres) NOPASSWD: ALL" >> /etc/sudoers')


def install_system_packages(c, packages=INSTALL_PACKAGES):
    packages_string = ' '.join(packages)
    c.run(f'apt update; apt-get -y install {packages_string}', echo=True)


def clone_repo(c, user=VM_USER_NAME, repo=REPO_URL, sitename=SITENAME):
    c.run(f'mkdir -p /home/{user}/sites', echo=True)
    with c.cd(f'/home/{user}/sites'):
        c.run(f'rm -rf {sitename}', echo=True)
        c.run(f'git clone {repo} {sitename}', echo=True)
        with c.cd(sitename):
            c.run(f'python3 -m venv --prompt {sitename} .venv', echo=True)


def update_repo(c, user=VM_USER_NAME, branch=BRANCH, sitename=SITENAME,
                proj=DJANGO_PROJECT_NAME):
    with c.cd(f'/home/{user}/sites/{sitename}'):
        c.run(f'git branch --set-upstream-to origin/{branch}', echo=True)
        c.run(f'git fetch', echo=True)
        c.run(f'git checkout --force {branch}', echo=True)
        c.run(f'git reset --hard `git log -n 1 --format=%H {branch}`',
              echo=True)
        c.run(f'.venv/bin/pip install --upgrade pip', echo=True)
        c.run(f'.venv/bin/pip install -r requirements.txt', echo=True)
        with c.cd(proj):
            # TODO: set STATIC_ROOT in deployment and uncomment:
            # c.run('../.venv/bin/python manage.py collectstatic --noinput')
            c.run('../.venv/bin/python manage.py migrate --noinput', echo=True)


def create_database(c, db=DB_NAME, user=DB_USER, password=DB_PASS):
    def psql(cmd):
        return f'sudo -u postgres psql -qc "{cmd};"'

    # noinspection SqlNoDataSourceInspection,SqlDialectInspection
    c.run(psql(f"CREATE DATABASE {db}"), warn=True, echo=True)
    c.run(psql(f"CREATE USER {user} WITH PASSWORD '{password}'"), warn=True,
          echo=True)
    c.run(psql(f"ALTER ROLE {user} SET client_encoding TO 'utf-8'"), echo=True)
    c.run(psql(f"ALTER ROLE {user} SET default_transaction_isolation TO "
               "'read committed'"), echo=True)
    c.run(psql(f"ALTER ROLE {user} SET timezone TO 'Europe/Moscow'"), echo=True)
    c.run(psql(f"GRANT ALL PRIVILEGES ON DATABASE {db} TO {user}"), echo=True)


def create_gunicorn_service(c, user=VM_USER_NAME, sitename=SITENAME):
    assignments = {
        'SITENAME': sitename,
        'USERNAME': user,
        'PROJNAME': DJANGO_PROJECT_NAME,
    }
    pattern = ";".join([f's/{k}/{v}/g' for k, v in assignments.items()])
    c.run(f'cat /home/{user}/sites/{sitename}/deploy/gunicorn.service | '
          f'sed "{pattern}" > /etc/systemd/system/gunicorn-{sitename}.service',
          echo=True)
    c.run(f'systemctl daemon-reload; systemctl enable gunicorn-{sitename}',
          echo=True)


def create_nginx_config(c, user=VM_USER_NAME, sitename=SITENAME,
                        cert_year=CERT_YEAR, max_body_size=MAX_BODY_SIZE):
    assignments = {
        'SITENAME': sitename,
        'MAX_BODY_SIZE': max_body_size,
        'YEAR': cert_year,
    }
    pattern = ";".join([f's/{k}/{v}/g' for k, v in assignments.items()])
    c.run(f'cat /home/{user}/sites/{sitename}/deploy/sitename.nginx |'
          f'sed "{pattern}" > /etc/nginx/sites-available/{sitename}',
          echo=True)
    c.run(f'cat /home/{user}/sites/{sitename}/deploy/www.sitename.nginx |'
          f'sed "{pattern}" > /etc/nginx/sites-available/www.{sitename}',
          echo=True)
    with c.cd('/etc/nginx/sites-available'):
        c.run(f'ln -frs {sitename} ../sites-enabled/{sitename}', echo=True)
        c.run(f'ln -frs www.{sitename} ../sites-enabled/www.{sitename}',
              echo=True)
        c.run(f'rm -f ../sites-enabled/default', echo=True)


def gunicorn_service(c, cmd, sitename=SITENAME):
    c.run(f'systemctl {cmd} gunicorn-{sitename}', echo=True)


def nginx_service(c, cmd):
    c.run(f'systemctl {cmd} nginx', echo=True)


def write_env(c, user=VM_USER_NAME, sitename=SITENAME):
    assignments = {
        'DJANGO_REMOTE': 1,
        'SITENAME': SITENAME,
        'SECRET_KEY': f'\'{os.environ["SECRET_KEY"]}\'',
    }
    with c.cd(f'/home/{user}/sites/{sitename}'):
        c.run('rm -f .env && touch .env', echo=True)
        for var, value in assignments.items():
            c.run(f'echo {var}={value} >> .env')
