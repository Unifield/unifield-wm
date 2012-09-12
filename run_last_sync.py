#!/usr/bin/env python2

import sys

#Load config file
import config

#Load OpenERP Client Library
import openerplib

#from tests import *
from tests.openerplib import db

from scripts.common import Synchro, HQ, Coordo, Project, Project2

#Load tests procedures
if sys.version_info >= (2, 7):
    import unittest
else:
    import unittest27 as unittest

try:
    import ipdb as pdb
except:
    import pdb

skipCreation = False
skipModules = False
skipModuleData = False
skipModuleUpdate = False
skipGroups = False
skipCostCenter = False
skipPropInstance = False
skipConfig = False
skipRegister = False
skipSync = False
skipUniUser = False
skipPartner = False

class base_sync(object):

    db = None

    def sync(self, db=None):
        if db is None: db = self.db
        if not db.get('sync.client.entity').sync():
            monitor = db.get('sync.monitor')
            ids = monitor.search([], 0, 1, '"end" desc')
            self.fail('Synchronization process of database "%s" failed!\n%s' % (db.db_name,monitor.read(ids, ['error'])[0]['error']))

class client_creation(base_sync):
    @unittest.skipIf(skipSync, "Synchronization desactivated")
    def test_50_synchronize(self):
        self.db.connect('admin')
        self.sync()

class sync_hq(client_creation, unittest.TestCase):
    db = HQ

class sync_coordo(client_creation, unittest.TestCase):
    db = Coordo

class sync_project(client_creation, unittest.TestCase):
    db = Project

class sync_project2(client_creation, unittest.TestCase):
    db = Project2

test_cases = (sync_hq, sync_coordo, sync_project)
#test_cases = (sync_coordo,)

def load_tests(loader, tests, pattern):
    suite = unittest.TestSuite()
    for test_class in test_cases:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    return suite

if __name__ == '__main__':
    unittest.main(failfast=True, verbosity=2)
