#!/usr/bin/env python2

import sys

from scripts.common import db_instance, client, Synchro, HQ
from config import project_count, coordo_count
import config

try:
    import ipdb as pdb
except:
    import pdb

def sync(db):
    db.connect('admin')
    print "Syncing %s..." % db.db_name
    if not db.get('sync.client.entity').sync():
        monitor = db.get('sync.monitor')
        ids = monitor.search([], 0, 1, '"end" desc')
        print 'Synchronization process of database "%s" failed!\n%s' % (db.db_name,monitor.read(ids, ['error'])[0]['error'])

def sync_all():
    sync(HQ)
    for i in range(1, coordo_count+1):
        name = "%s_COORDO_%02d" % (config.prefix, i)
        db = db_instance(
            server=client,
            name=name,
            synchro={
                'protocol' : 'netrpc',
                'host' : config.server_host,
                'port' : config.netrpc_port,
                'database' : Synchro.name,
                'login' : name,
                'password' : name,
            },
        )
        sync(db)
    for i in range(1, project_count+1):
        name = "%s_PROJECT_%02d" % (config.prefix, i)
        db = db_instance(
            server=client,
            name=name,
            synchro={
                'protocol' : 'netrpc',
                'host' : config.server_host,
                'port' : config.netrpc_port,
                'database' : Synchro.name,
                'login' : name,
                'password' : name,
            },
        )
        sync(db)

if __name__ == '__main__':
    if len(sys.argv) > 1:
        dbs = eval("(%s,)" % ",".join(sys.argv[1:]))
        for db in dbs:
            sync(db)
    else:
        sync_all()