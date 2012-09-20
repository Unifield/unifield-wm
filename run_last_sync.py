#!/usr/bin/env python2

import sys

from scripts.common import Synchro, HQ, Coordo, Project, Project2

try:
    import ipdb as pdb
except:
    import pdb

import config
from config import coordo_count, project_count

def sync(db):
    db.connect('admin')
    print "Syncing %s..." % db.db_name
    if not db.get('sync.client.entity').sync():
        monitor = db.get('sync.monitor')
        ids = monitor.search([], 0, 1, '"end" desc')
        print 'Synchronization process of database "%s" failed!\n%s' % (db.db_name,monitor.read(ids, ['error'])[0]['error'])

def sync_all():
    test_cases = ["HQ", ]
    for i in range(1, coordo_count+1):
        test_cases.append("COORDO%02d" % i)
        
    for i in range(1, project_count+1):
        test_cases.append("PROJECT%02d" % i)
    
    for db in test_cases:
        sync(db)

if __name__ == '__main__':
    if len(sys.argv) > 1:
        dbs = eval("(%s,)" % ",".join(sys.argv[1:]))
        for db in dbs:
            sync(db)
    else:
        sync_all()

