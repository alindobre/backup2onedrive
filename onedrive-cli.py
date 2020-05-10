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

def usage():
    print('OneDrive-CLI API Wrapper. Usage:')
    print('onedrive-cli.py COMMAND ARGS')
    print('COMMAND can be one of:')
    print('upload - Uploads the files received as arguments to the onedrive folder')
    print('         onedrive-cli.py upload file1 file2 ...')


def onedrive_upload(local_files, remote_destination):
    USIZE = 327680
    for fpath in local_files:
        fsize = os.stat(fpath).st_size
        fname = os.path.basename(fpath)
        with open(fpath, 'rb') as f:
            payload = '{"item": {"@microsoft.graph.conflictBehavior": "rename" }}'
            r = requests.post(f'https://graph.microsoft.com/v1.0/me/drive/root:{remote_destination}/{fname}:/createUploadSession', data=payload,
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
                if verbose:
                    print(f'Uploading {fname}. Bytes {start}-{end}/{fsize} {int(end*100/fsize)}%')
                r = requests.put(uploadUrl, headers = headers, data = data)
                if http.client.HTTPConnection.debuglevel:
                    print(json.dumps(json.loads(r.content.decode('latin1')), indent=4))


def onedrive_list(remote_folder, stdout=False):
    if not stdout:
        listing = {}
    link = f'https://graph.microsoft.com/v1.0/me/drive/root:{remote_folder}:/children'
    while link:
        r = requests.get(link, headers={'Authorization': 'bearer ' + access_token})
        j = json.loads(r.content.decode('latin1'))
        for item in j['value']:
            if verbose:
                print('-> ' + item['name'] + ' ' + item['id'])
            elif stdout:
                print(item['name'])
            else:
                listing[item['name']] = item['id']
        link = j['@odata.nextLink'] if '@odata.nextLink' in j else None
    if not stdout:
        return listing


if __name__ == '__main__':
    if len(sys.argv) == 1:
        usage()
        exit(1)
    verbose = False
    if ('-v' in sys.argv):
        verbose = True
        sys.argv.remove('-v')
    elif ('--verbose' in sys.argv):
        verbose = True
        sys.argv.remove('--verbose')
    if ('-d' in sys.argv):
        http.client.HTTPConnection.debuglevel = 1
        sys.argv.remove('-d')
    elif ('--debug' in sys.argv):
        http.client.HTTPConnection.debuglevel = 1
        sys.argv.remove('--debug')

    config = json.load(open(os.sep.join([os.environ['HOME'], 'backup.json'])))
    access_token = get_access_token(
        'https://login.live.com/oauth20_token.srf',
        config['onedrive']['client_id'],
        config['onedrive']['client_secret'],
        config['onedrive']['refresh_token']
    )

    folder = None
    if 'root_folder' in config['onedrive']:
        folder = config['onedrive']['root_folder']

    if sys.argv[1] == 'upload':
        if folder:
            onedrive_upload(sys.argv[2:], folder)
        else:
            onedrive_upload(sys.argv[2:-1], sys.argv[-1])
    elif sys.argv[1] == 'list':
        if folder:
            onedrive_list(folder, stdout=True)
        else:
            for remote_folder in sys.argv[2:]:
                onedrive_list(remote_folder, stdout=True)
    elif sys.argv[1] == 'move':
        dst = sys.argv[-1]
        src = sys.argv[2:-1]
        link = f'https://graph.microsoft.com/v1.0/me/drive/root:{folder}:/children'
        l = {}
        while link:
            r = requests.get(link, headers={'Authorization': 'bearer ' + access_token})
            j = json.loads(r.content.decode('latin1'))
            for item in j['value']:
                l[item['name']]=item['id']
            link = j['@odata.nextLink'] if '@odata.nextLink' in j else None

        if dst not in l:
            print('Create folder:', folder + '/' + dst)
            payload = '{"name": "' + dst + '", "folder": { }, "@microsoft.graph.conflictBehavior": "rename" }'
            r = requests.post(f'https://graph.microsoft.com/v1.0/me/drive/root:{folder}:/children', data = payload,
                headers={'Authorization': 'bearer ' + access_token, 'Content-Type': 'application/json'})
            j = json.loads(r.content.decode('latin1'))
            dstid = j['id']
        else:
            dstid = l[dst]

        http.client.HTTPConnection.debuglevel = 1
        for item in l:
            if item in src:
                print('----------------> ' + item + ' ' + l[item])
                #payload = '{"parentReference": { "id": "{new-parent-folder-id}" }, "name": "new-item-name.txt"}'
                payload = '{"parentReference": { "id": "' + dstid + '" }}'
                r = requests.patch(f'https://graph.microsoft.com/v1.0/me/drive/items/{l[item]}', data = payload,
                    headers={'Authorization': 'bearer ' + access_token, 'Content-Type': 'application/json'})
                if http.client.HTTPConnection.debuglevel:
                    print(json.dumps(json.loads(r.content.decode('latin1')), indent=4))
            else:
                print('nothin to move')

    else:
        usage()
        exit(1)
