#!/usr/bin/env python2
"""
    To run the synchronization for a specific instance, just use this command:
    ./run_last_sync.py SPRINT5_HQ

    You can specifiy many instances:
    ./run_last_sync.py SPRINT5_HQ SPRINT5_COORDO

    With a bash expansion:
    ./run_last_sync.py SPRINT5_PROJECT_{01..3}  ## means actually SPRINT5_PROJECT_01 SPRINT5_PROJECT_02 SPRINT5_PROJECT_03

    Or in a more complicate way:
    ./run_last_sync.py SPRINT{5,6}_{HQ,COORDO_{01..2},PROJECT_{01..4}}

    Which actually means...
    SPRINT5_HQ SPRINT5_COORDO_01 SPRINT5_COORDO_02 SPRINT5_PROJECT_01 SPRINT5_PROJECT_02 SPRINT5_PROJECT_03 SPRINT5_PROJECT_04 SPRINT6_HQ SPRINT6_COORDO_01 SPRINT6_COORDO_02 SPRINT6_PROJECT_01 SPRINT6_PROJECT_02 SPRINT6_PROJECT_03 SPRINT6_PROJECT_04
"""

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
    print "Syncing %s ..." % db.db_name
    if not db.get('sync.client.entity').sync():
        monitor = db.get('sync.monitor')
        ids = monitor.search([], 0, 1, '"end" desc')
        print 'Synchronization process of database "%s" failed!\n%s' % (db.db_name,monitor.read(ids, ['error'])[0]['error'])

def sync_coordo():
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

def sync_projects():
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

def sync_all():
    sync(HQ)
    sync_coordo()
    sync_projects()

if __name__ == '__main__':
    if len(sys.argv) > 1:
        for name in sys.argv[1:]:
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
    else:
        sync_all()

