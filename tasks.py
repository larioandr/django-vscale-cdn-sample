import os
import time

import invoke
import requests
import json

SITENAME = os.environ['SITENAME']
VSCALE_TOKEN = os.environ['VSCALE_TOKEN']
VM_ROOT_PASS = os.environ['VM_ROOT_PASS']

DOMAIN = '.'.join(SITENAME.split('.')[-2:])


@invoke.task
def create_server(c, name):
    address = create_scalet(name)
    update_dns(address)
    c.run(f'ssh-keyscan -H {address} >> ~/.ssh/known_hosts')
    print('[=] scalet address: ', address)


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
