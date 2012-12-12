import os
import requests
import sys
from getopt import getopt, GetoptError
from urlparse import urlparse

'''
heroku-pgpy
===========
Lightweight Heroku pgbackups implementation for Python.

https://github.com/BigglesZX/heroku-pgpy
'''


''' We unfortunately have to ape the Heroku client gem in order to access the API '''
HEROKU_GEM_VERSION = '2.33.3'


def _build_auth():
    ''' Construct the requests auth tuple from the environment config '''
    if 'PGBACKUPS_URL' in os.environ:
        url = urlparse(os.environ['PGBACKUPS_URL'])
        return (url.username, url.password)
    raise Exception("Couldn't determine pgbackups url, is the pgbackups addon installed?")


def _build_base_url():
    ''' Construct the base pgbackups url from the environment config '''
    if 'PGBACKUPS_URL' in os.environ:
        url = urlparse(os.environ['PGBACKUPS_URL'])
        return '%s://%s' % (url.scheme, url.hostname)
    raise Exception("Couldn't determine pgbackups url, is the pgbackups addon installed?")
    

def _build_db_name():
    for key in os.environ:
        if key.startswith('HEROKU_POSTGRESQL_'):
            return key.replace('_URL', '')
    raise Exception("Couldn't determine database name from environment, is a database installed?")


def _build_headers():
    ''' Build the custom headers dict for a request '''
    return {
        'X-Heroku-Gem-Version': HEROKU_GEM_VERSION,
    }
    

def _build_request_url(path):
    ''' Join the base pgbackups url with a REST endpoint '''
    return _build_base_url() + path
    
    
def _get_db_url():
    if 'DATABASE_URL' in os.environ:
        return os.environ['DATABASE_URL']
    raise Exception("Couldn't determine database url from environment, is a database installed?")
    

def show_latest_backup():
    r = requests.get(_build_request_url('/client/latest_backup'),
                     auth=_build_auth(),
                     headers=_build_headers())
    if r.ok:
        if 'from_name' in r.json:
            print "Latest backup: %s (%s)" % (r.json['from_name'], r.json['created_at'])
        else:
            print "No backups created yet."
    else:
        print "Request failed: %s" % r.reason
        print "If the server said 'need Heroku client version x', please update pgpy."
    return r
    

def capture_backup():
    payload = {
        'from_url': _get_db_url(),
        'from_name': _build_db_name() + ' (DATABASE_URL*)',
        'to_url': '',
        'to_name': 'BACKUP',
        'expire': '',
    }
    r = requests.post(_build_request_url('/client/transfers'),
                      auth=_build_auth(),
                      headers=_build_headers(),
                      data=payload)
    if r.ok:
        print "Initiating backup..."
    else:
        print "Request failed: %s" % r.reason
        print "If the server said 'need Heroku client version x', please update pgpy."
    

def main():
    try:
        opts, args = getopt(sys.argv[1:], '', ['show', 'capture',])
        mode = False
        if opts:
            for o, a in opts:
                if o == '--show':
                    mode = 'show'
                elif o == '--capture':
                    mode = 'capture'
        if not opts or not mode:
            raise GetoptError('')
            
        if mode == 'show':
            show_latest_backup()
        elif mode == 'capture':
            capture_backup()
            
    except GetoptError:
        print "No function specified."
        print "Usage: python pg.py [--show | --capture]"
    

if __name__ == "__main__":
    main()