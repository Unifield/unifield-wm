#!/usr/bin/env python2
"""
    ./run_last_sync.py
    ...will run synchronization for all instances

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
import os

from scripts.common import db_instance, client, Synchro, HQ
from config import project_count, coordo_count
import config

#Load tests procedures
if sys.version_info >= (2, 7):
    import unittest
else:
    # Needed for setUpClass and skipIf methods
    import unittest27 as unittest

from mkdb import test_cases, db_creation, client_creation

try:
    import ipdb as pdb
except:
    import pdb

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
            db.connect('admin')
            print "Syncing %s ..." % db.db_name
            db_creation.sync(db)
    else:
        for tc in test_cases:
            if issubclass(tc, client_creation):
                tc.setUpClass()
                tc.db.connect('admin')
                print "Syncing %s ..." % tc.db.db_name
                tc.sync()

