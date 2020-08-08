#!/usr/bin/env python3

import onedrive_cli
import sys
import json
import os
import datetime
import http.client

if __name__ == '__main__':
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
    if len(sys.argv) > 1:
        config = json.load(open(sys.argv[1]))
    onedrive_cli.access_token = onedrive_cli.get_access_token(
        'https://login.live.com/oauth20_token.srf',
        config['onedrive']['client_id'],
        config['onedrive']['client_secret'],
        config['onedrive']['refresh_token']
    )

    folders = []
    if 'root_folder' in config['onedrive']:
        if (type(config['onedrive']['root_folder']) == list):
            folders.extend(config['onedrive']['root_folder'])
        elif (type(config['onedrive']['root_folder']) == str):
            folders = [ config['onedrive']['root_folder'] ]
        else:
            sys.stderr.write('ERROR: the root_folder JSON object is neither string nor list')
            exit(1)
    else:
        sys.stderr.write('ERROR: could not find the root_folder JSON object')
        exit(1)

    for folder in folders:
        listing = onedrive_cli.onedrive_list(folder)
        destinations = {}
        for item in listing:
            if item.startswith('docroot-') and item.endswith('.vcdiff'):
                if not item.startswith('docroot-' + datetime.date.today().strftime('%Y-%V-%u')):
                    if item[:15] not in destinations:
                        destinations[item[:15]] = []
                    destinations[item[:15]].append(item)
            if item.startswith('mysql-') and item.endswith('.vcdiff'):
                if not item.startswith('mysql-' + datetime.date.today().strftime('%Y-%V-%u')):
                    if item[:13] not in destinations:
                        destinations[item[:13]] = []
                    destinations[item[:13]].append(item)
            if item.startswith('mysql-') and item.endswith('.dump.xz'):
                if not item.startswith('mysql-' + datetime.date.today().strftime('%Y-%V')):
                    if item[:13] not in destinations:
                        destinations[item[:13]] = []
                    destinations[item[:13]].append(item)
        for dest in destinations:
            if dest not in listing:
                folder_id = onedrive_cli.onedrive_mkdir(folder, dest)
            else:
                folder_id = listing[dest]
            for item in destinations[dest]:
                if verbose:
                    print(f'{folder}/{item} -> {dest}')
                onedrive_cli.onedrive_move(listing[item], folder_id)
