#!/usr/bin/env python2
# -*- coding: utf-8 -*-

#Load common script tests
from scripts.common import Synchro, HQ, Coordo, Project

#Load config file
import config

#Load OpenERP Client Library
import openerplib
from tests.openerplib import *

#Other stuffs
from datetime import datetime
from random import choice

#Load tests procedures
if sys.version_info >= (2, 7):
    import unittest
else:
    # Needed for setUpClass and skipIf methods
    import unittest27 as unittest

try:
    import ipdb as pdb
except:
    import pdb

class finance(unittest.TestCase):

    models = ('res.currency','res.currency.table','res.currency.rate')

    def sync(self, db=None):
        if db is None: db = self.db
        if not db.get('sync.client.entity').sync():
            monitor = db.get('sync.monitor')
            ids = monitor.search([], 0, 1, '"end" desc')
            self.fail('Synchronization process of database "%s" failed!\n%s' % (db.db_name,monitor.read(ids, ['error'])[0]['error']))

    def clean(self):
        for db in (HQ, Coordo, Project):
            db.clean('res.currency.rate', self.rate_data)
            db.clean('res.currency', self.currency_data, active='both', domain=['|','!',('currency_table_id','=',False),('currency_table_id','=',False)])
            db.clean('res.currency.table', self.hq_data)
        for db in (Coordo, Project):
            db.clean('res.currency.table', self.coordo_data)

    def setUp(self):
        Synchro.connect('admin')
        HQ.connect('admin')
        Coordo.connect('admin')
        Project.connect('admin')

    def test_20_currency(self):
        # Make data
        self.id = datetime.now().strftime('%m%d%H%M')
        self.hq_data = {
            'code':'TEST_%s' % self.id,
            'name':'TEST_%s' % self.id,
        }
        self.coordo_data = {
            'code':'TEST_%s_X' % self.id,
        }
        self.currency_data = {
            'accuracy' : 4,
            'currency_name' : 'TEST_%s' % self.id,
            'name' : 'TEST_%s' % self.id,
            'rounding' : 0.01,
            'symbol' : 'T%s' % self.id,
        }
        self.rate_data = {
            'name' : datetime.now().strftime('%Y-%m-%d'),
            'rate' : '0.9999',
        }
        self.clean()
        # Activate rule
        #Synchro.desactivate('sync_server.sync_rule', [])
        n = Synchro.activate('sync_server.sync_rule', [('model_id','in',self.models)])
        #self.assertTrue(n >= len(self.models), "Cannot enable sync rules!")
        # Create & Synchronize
        cur = dict(self.currency_data)
        rate = dict(self.rate_data)
        cur['currency_table_id'] = HQ.get('res.currency.table').create(self.hq_data)
        self.assertTrue(cur['currency_table_id'], "Cannot create currency table!")
        rate['currency_id'] = HQ.get('res.currency').create(cur)
        self.assertTrue(rate['currency_id'], "Cannot create currency!")
        rate_id = HQ.get('res.currency.rate').create(rate)
        self.assertTrue(rate_id, "Cannot create currency rate!")
        HQ.get('res.currency').write(rate['currency_id'], {'active':1})
        for db in (HQ, Coordo, Project,):
            self.sync(db)
        # Check
        for db in (HQ, Coordo, Project,):
            self.assertTrue(db.test('res.currency.table', self.hq_data),
                "The currency table created in HQ is not present in database %s! data=%s" % (db.db_name,self.hq_data))
            self.assertTrue(db.test('res.currency', self.currency_data, active='both', domain=['|','!',('currency_table_id','=',False),('currency_table_id','=',False)]),
                "The currency created in HQ is not present in database %s! data=%s" % (db.db_name,self.currency_data,))
            self.assertTrue(db.test('res.currency.rate', self.rate_data),
                "The currency rate created in HQ is not present in database %s! data=%s" % (db.db_name,self.rate_data))
        # Modify & Synchronize
        n = Coordo.write('res.currency.table', self.hq_data, self.coordo_data)
        self.assertTrue(n == 1,
            "Cannot write coordo data! hq_data=%s, coordo_data=%s" % (self.hq_data, self.coordo_data))
        for db in (Coordo, HQ, Project,):
            self.sync(db)
        # Check
        self.assertFalse(HQ.test('res.currency.table', self.coordo_data),
            "The currency table created in Coordo has been modified in database HQ!")
        self.assertTrue(Project.test('res.currency.table', self.coordo_data),
            "The currency table created in Coordo has not been properly modified in database Project!")

test_cases = (finance,)

def load_tests(loader, tests, pattern):
    suite = unittest.TestSuite()
    for test_class in test_cases:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    return suite

if __name__ == '__main__':
    unittest.main(failfast=True, verbosity=2)

