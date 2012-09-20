#!/usr/bin/env python2

import sys

from scripts.common import Synchro, HQ, Coordo, Project, Project2

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
    for db in (HQ, Coordo, Project, Project2):
        sync(db)

if __name__ == '__main__':
    if len(sys.argv) > 1:
        dbs = eval("(%s,)" % ",".join(sys.argv[1:]))
        for db in dbs:
            sync(db)
    else:
        sync_all()