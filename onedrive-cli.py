#!/usr/bin/env python3

import http.client
import requests
import json
import os
import sys

def get_access_token(auth_url, client_id, secret, refresh_token):
    """ Query onedrive api, return an oauth access token """
    payload = {
        'client_id': client_id,
        'client_secret': secret,
        'refresh_token': refresh_token,
        'grant_type': 'refresh_token',
        'redirect_uri': 'https://localhost:8080'
        }

    try:
        r = requests.post(auth_url, data=payload)
        r = json.loads(r.content.decode('latin1'))
        r = r['access_token']
    except:
        print("Could not get access tokens from {0}".format(auth_url))
        if (r):
            print(r)
        raise

    return r

#http.client.HTTPConnection.debuglevel = 1
config = json.load(open(os.sep.join([os.environ['HOME'], 'backup.json'])))
access_token = get_access_token(
    'https://login.live.com/oauth20_token.srf',
    config['onedrive']['client_id'],
    config['onedrive']['client_secret'],
    config['onedrive']['refresh_token']
)

folder = config['onedrive']['root_folder']

"""
print('Create folder:')
payload = '{"name": "New Folder", "folder": { }, "@microsoft.graph.conflictBehavior": "rename" }'
r = requests.post(f'https://graph.microsoft.com/v1.0/me/drive/root:{folder}:/children', data = payload,
    headers={'Authorization': 'bearer ' + access_token, 'Content-Type': 'application/json'})
print(json.dumps(json.loads(r.content.decode('latin1')), indent=4))
print('-> ' + json.loads(r.content.decode('latin1'))['webUrl'])

print('File listing:')
r = requests.get(f'https://graph.microsoft.com/v1.0/me/drive/root:{folder}:/children',
    headers={'Authorization': 'bearer ' + access_token})
for item in json.loads(r.content.decode('latin1'))['value']:
    print('-> ' + item['name'] + ' ' + item['id'])

print('Delete items:')
for item in json.loads(r.content.decode('latin1'))['value']:
    print('-> ' + item['name'] + ' ' + item['id'])
    r = requests.delete(f'https://graph.microsoft.com/v1.0/me/drive/items/{item["id"]}',
        headers={'Authorization': 'bearer ' + access_token})
"""

print('Upload items:')
USIZE = 327680
for fpath in sys.argv[1:]:
    fsize = os.stat(fpath).st_size
    fname = os.path.basename(fpath)
    with open(fpath, 'rb') as f:
        payload = '{"item": {"@microsoft.graph.conflictBehavior": "rename" }}'
        r = requests.post(f'https://graph.microsoft.com/v1.0/me/drive/root:{folder}/{fname}:/createUploadSession', data=payload,
            headers={'Authorization': 'bearer ' + access_token, 'Content-Type': 'application/x-www-form-urlencoded'})
        if http.client.HTTPConnection.debuglevel:
            print(json.dumps(json.loads(r.content.decode('latin1')), indent=4))
        uploadUrl = json.loads(r.content.decode('latin1'))['uploadUrl']
        while f.tell() < fsize:
            start = f.tell()
            data = b''
            while len(data) < USIZE and f.tell() < fsize:
                data += f.read(USIZE)
            end = start + len(data) - 1
            headers = {
                'Content-Length': f'{len(data)}',
                'Content-Range': f'bytes {start}-{end}/{fsize}'
            }
            print(f'{fname} bytes {start}-{end}/{fsize} {int(end*100/fsize)}%')
            r = requests.put(uploadUrl, headers = headers, data = data)
            if http.client.HTTPConnection.debuglevel:
                print(json.dumps(json.loads(r.content.decode('latin1')), indent=4))