#!/usr/bin/env python2

import sys

#Load config file
import config
from config import load_test as load_value

#Load OpenERP Client Library
import openerplib

#from tests import *
from tests.openerplib import db

from scripts.common import Synchro, HQ, Coordo, Project

#Load tests procedures
if sys.version_info >= (2, 7):
    import unittest
else:
    import unittest27 as unittest

from threading import Thread
from timeit import Timer
from math import ceil
from datetime import datetime

try:
    import ipdb as pdb
except:
    import pdb


test_cases = []


class synchronize(object):
    databases = (HQ, Coordo, Project)

    def sync(self, db):
        if not db.get('sync.client.entity').sync():
            monitor = db.get('sync.monitor')
            ids = monitor.search([], 0, 1, '"end" desc')
            self.fail('Synchronization process of database "%s" failed!\n%s' % (db.db_name,monitor.read(ids, ['error'])[0]['error']))

    def sync_all(self):
        for db in self.databases:
            db.connect('admin')
            self.sync(db)


class make_records(unittest.TestCase):
    created_records = []
    id = datetime.now().strftime('%m%d%H%M')
    template = {
        'name' : 'TEST_%s_' % id,
        'amount' : 400.00,
        'amount_currency' : 1.0,
        'document_date' : datetime.now().strftime('%Y-%m-%d'),
    }
    journal = {
        'name' : 'TEST_%s' % id,
    }

    def test_20_make_records(self):
        Project.connect('admin')
        journal_id = Project.get('account.analytic.journal').create(self.journal)
        self.assertTrue(journal_id,
                   "Cannot create journal: %s in db %s" % (self.journal, Project.name))
        self.__class__.created_records.append( ('account.analytic.journal', self.journal) )
        for i in range(load_value):
            data = dict(self.template)
            data['name'] += str(i)
            self.__class__.created_records.append( ('account.analytic.line', dict(data)) )
            data.update({
                'journal_id' : journal_id,
                'currency_id' : Project.get('res.currency').search([('name','=','EUR')], 0, 1)[0],
                'account_id' : Project.get('account.analytic.account').search([('name','=','Dummy')], 0, 1)[0],
                'general_account_id' : Project.get('account.account').search([('name','=','Medical')], 0, 1)[0],
            })
            self.assertTrue(Project.get('account.analytic.line').create(data),
                       "Cannot create record: %s in db %s" % (data, Project.name))


class clean(synchronize, unittest.TestCase):
    def test_10_synchronize(self):
        self.sync_all()

    test_11_synchronize_twice = test_10_synchronize


class check_records(unittest.TestCase):
    def test_10_check_record_existence(self):
        if not make_records.created_records:
            self.skipTest("It seems no record has been created!")
        for model, rec in make_records.created_records:
            for db in (Coordo, HQ):
                self.assertTrue(db.test(model, rec),
                           "Cannot find record: %s in db %s" % (rec, db.name))


class load(synchronize, unittest.TestCase):
    logs = ""

    def measure_synchronize(self, db, message):
        t = Timer( lambda:self.sync(db) )
        delay = t.timeit(1)
        self.__class__.logs += (message+"\n") % (db.name, ceil(delay))

    def test_50_synchronize(self):
        for db in self.databases:
            db.connect('admin')
        self.measure_synchronize(Project, "%s pushed in %d seconds")
        threads = []
        for db in (Coordo, HQ):
            threads.append( Thread(target=lambda:self.measure_synchronize(db,
                "%s pulled in %d seconds")) )
            threads[-1].start()
        for t in threads:
            t.join()

    @classmethod
    def tearDownClass(cls):
        print cls.logs.strip()

test_cases = [clean,make_records,load,check_records]


def load_tests(loader, tests, pattern):
    suite = unittest.TestSuite()
    for test_class in test_cases:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    return suite

if __name__ == '__main__':
    unittest.main(failfast=True, verbosity=2)

