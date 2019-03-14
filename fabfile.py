import json

import fabric2 as fabric
import requests
import warnings
import os
import time


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

DOMAIN = '.'.join(SITENAME.split('.')[-2:])

INSTALL_PACKAGES = (
    'python3.6', 'nginx', 'postgresql', 'sshpass', 'git', 'vim',
    'python3-venv',
)
DJANGO_PROJECT_NAME = 'ubio'


@fabric.task
def create_server(ctx, address):
    # 1) Establish a connection with root access rights to install software,
    # create admin user and copy certificates:
    root = fabric.Connection(address, user='root', connect_kwargs={
        'password': VM_ROOT_PASS
    })
    install_system_packages(root)
    copy_certificates(root)
    create_user(root)

    # 2) Establish a connection on part of the non-root user (site admin),
    # prepare home folder, clone the repository and setup the database:
    user = fabric.Connection(address, user=VM_USER_NAME, connect_kwargs={
        'password': VM_USER_PASS
    })
    clone_repo(user)
    write_env(user)
    create_database(user)

    # 3) On part of root, create configuration files and services:
    create_gunicorn_service(root)
    create_nginx_config(root)

    # 4) Update the repository, make migrations, install python packages.
    # Then tart services (on part of root).
    update_repo(user)
    start_gunicorn(root)
    start_nginx(root)


def copy_certificates(
        c, user=CDN_USER, password=CDN_PASS, ftp_server=CDN_FTP_SERVER,
        cert_path=CDN_CERT_PATH, sitename=SITENAME):
    print('[FAB] * copy_certificates()')
    ftp = f'SSHPASS={password} sshpass -e sftp {user}@{ftp_server}:/{cert_path}'
    local_path = f'/etc/ssl/'

    c.run('mkdir -p ~/.ssh')
    c.run(f'ssh-keyscan -H {ftp_server} >> ~/.ssh/known_hosts')
    c.run(f'mkdir -p {local_path}')
    c.run(f'{ftp}/{sitename}*.crt /etc/ssl/certs/')
    c.run(f'{ftp}/{sitename}*.key /etc/ssl/private/')
    # c.run(f'{ftp}/{sitename}*.pem {local_path}/')


def create_user(c, username=VM_USER_NAME, password=VM_USER_PASS):
    print('[FAB] * create_user()')
    if c.run(f'adduser --quiet --disabled-password --gecos "" {username}',
             warn=True).exited == 0:
        c.run(f'echo "{username}:{password}" | chpasswd')
        c.run(f'echo "{username} ALL=(postgres) NOPASSWD: ALL" >> /etc/sudoers')


def install_system_packages(c, packages=INSTALL_PACKAGES):
    print('[FAB] * install_system_packages()')
    packages_string = ' '.join(packages)
    c.run(f'apt update; apt-get -y install {packages_string}')


def clone_repo(c, user=VM_USER_NAME, repo=REPO_URL, sitename=SITENAME):
    print('[FAB] * clone_repo()')
    c.run(f'mkdir -p /home/{user}/sites')
    with c.cd(f'/home/{user}/sites'):
        c.run(f'rm -rf {sitename}')
        c.run(f'git clone {repo} {sitename}')
        with c.cd(sitename):
            c.run(f'python3 -m venv --prompt {sitename} .venv')


def update_repo(c, user=VM_USER_NAME, branch=BRANCH, sitename=SITENAME,
                proj=DJANGO_PROJECT_NAME):
    print('[FAB] * update_repo()')
    with c.cd(f'/home/{user}/sites/{sitename}'):
        c.run(f'git fetch')
        c.run(f'git checkout {branch}')
        c.run(f'git reset --hard `git log -n 1 --format=%H {branch}`')
        c.run(f'echo "------"; pwd; ls -al')
        c.run(f'.venv/bin/pip install --upgrade pip')
        c.run(f'.venv/bin/pip install -r requirements.txt')
        with c.cd(proj):
            # TODO: set STATIC_ROOT in deployment and uncomment:
            # c.run('../.venv/bin/python manage.py collectstatic --noinput')
            c.run('../.venv/bin/python manage.py migrate --noinput')


def create_database(c, db=DB_NAME, user=DB_USER, password=DB_PASS):
    print('[FAB] * create_database()')

    def psql(cmd):
        return f'sudo -u postgres psql -qc "{cmd};"'

    # noinspection SqlNoDataSourceInspection,SqlDialectInspection
    c.run(psql(f"CREATE DATABASE {db}"), warn=True)
    c.run(psql(f"CREATE USER {user} WITH PASSWORD '{password}'"), warn=True)
    c.run(psql(f"ALTER ROLE {user} SET client_encoding TO 'utf-8'"))
    c.run(psql(f"ALTER ROLE {user} SET default_transaction_isolation TO "
               "'read committed'"))
    c.run(psql(f"ALTER ROLE {user} SET timezone TO 'Europe/Moscow'"))
    c.run(psql(f"GRANT ALL PRIVILEGES ON DATABASE {db} TO {user}"))


def create_gunicorn_service(c, user=VM_USER_NAME, sitename=SITENAME):
    print('[FAB] * create_gunicorn_service()')
    assignments = {
        'SITENAME': sitename,
        'USERNAME': user,
        'PROJNAME': DJANGO_PROJECT_NAME,
    }
    pattern = ";".join([f's/{k}/{v}/g' for k, v in assignments.items()])
    c.run(f'cat /home/{user}/sites/{sitename}/deploy/gunicorn.service | '
          f'sed "{pattern}" > /etc/systemd/system/gunicorn-{sitename}.service')
    c.run(f'systemctl daemon-reload; systemctl enable gunicorn-{sitename}')


def create_nginx_config(c, user=VM_USER_NAME, sitename=SITENAME,
                        cert_year=CERT_YEAR, max_body_size=MAX_BODY_SIZE):
    print('[FAB] * create_nginx_config()')
    assignments = {
        'SITENAME': sitename,
        'MAX_BODY_SIZE': max_body_size,
        'YEAR': cert_year,
    }
    pattern = ";".join([f's/{k}/{v}/g' for k, v in assignments.items()])
    c.run(f'cat /home/{user}/sites/{sitename}/deploy/sitename.nginx |'
          f'sed "{pattern}" > /etc/nginx/sites-available/{sitename}')
    c.run(f'cat /home/{user}/sites/{sitename}/deploy/www.sitename.nginx |'
          f'sed "{pattern}" > /etc/nginx/sites-available/www.{sitename}')
    with c.cd('/etc/nginx/sites-available'):
        c.run(f'ln -frs {sitename} ../sites-enabled/{sitename}')
        c.run(f'ln -frs www.{sitename} ../sites-enabled/www.{sitename}')
        c.run(f'rm -f default')


def start_gunicorn(c, sitename=SITENAME):
    print('[FAB] * start_gunicorn()')
    c.run(f'systemctl start gunicorn-{sitename}')


def start_nginx(c):
    print('[FAB] * start_nginx()')
    c.run(f'systemctl start nginx')


def write_env(c, user=VM_USER_NAME, sitename=SITENAME):
    with c.cd(f'/home/{user}/sites/{sitename}'):
        c.run('rm -f .env && touch .env')
        c.run(f'echo DJANGO_REMOTE={os.environ["DJANGO_REMOTE"]} >> .env')
        c.run(f'echo SITENAME={os.environ["SITENAME"]} >> .env')
