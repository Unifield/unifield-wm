#!/usr/bin/env python
#-*- coding:utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2014 TeMPO Consulting, MSF. All Rights Reserved
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import unittest
import traceback
import os
import sys
import time


class UnifieldTestSuite(unittest.suite.TestSuite):

    def __init__(self, tests=(), loader=False):
        self.loader = loader
        super(UnifieldTestSuite, self).__init__(tests)


class UnifieldTestLoader(unittest.loader.TestLoader):
    suiteClass = UnifieldTestSuite
    _top_level_dir = None

    def __init__(self, pool, cr, uid, cid, update_module=False):
        """
        Give information the the sync. DB connection
        """
        self.pool = pool
        self.cr = cr
        self.uid = uid
        self.cid = cid
        self.update_module = update_module

    def filter_tests(self, tests):
        """
        Filter discovered tests according to test selected in campaign
        """
        res = []
        for t in tests:
            if isinstance(t, unittest.case.TestCase):
                t_ids = self.pool.get('automatic.test').search(self.cr, self.uid, [
                    ('template_id.test_class', '=', t.__class__.__name__),
                    ('campaign_id', '=', self.cid),
                ], limit=1)
                if t_ids:
                    t.test_id = t_ids
                    for t_id in t_ids:
                        self.pool.get('automatic.test.method').create(
                            self.cr,
                            self.uid,
                            {
                                'test_id': t_id,
                                'name': t._testMethodName,
                            },
                        )
                    res.append(t)
            elif isinstance(t, unittest.suite.TestSuite):
                if t._tests:
                    flt = self.filter_tests(t)
                    if flt:
                        res.append(self.suiteClass(flt, self))

        return res

    def discover(self, start_dir, pattern='test*.py', top_level_dir=None, from_update=False):
        """
        Discover all tests in the tests directory
        """
        set_implicit_top = False
        if top_level_dir is None and self._top_level_dir is not None:
            # make top_level_dir optional if called from load_tests in a package
            top_level_dir = self._top_level_dir
        elif top_level_dir is None:
            set_implicit_top = True
            top_level_dir = start_dir

        top_level_dir = os.path.abspath(top_level_dir)

        if not top_level_dir in sys.path:
            # all test modules must be importable from the top level directory
            # should we *unconditionally* put the start directory in first
            # in sys.path to minimise likelihood of conflicts between installed
            # modules and development versions?
            sys.path.insert(0, top_level_dir)
        self._top_level_dir = top_level_dir

        is_not_importable = False
        if os.path.isdir(os.path.abspath(start_dir)):
            start_dir = os.path.abspath(start_dir)
            if start_dir != top_level_dir:
                is_not_importable = not os.path.isfile(os.path.join(start_dir, '__init__.py'))
        else:
            # support for discovery from dotted module names
            try:
                __import__(start_dir)
            except ImportError:
                is_not_importable = True
            else:
                the_module = sys.modules[start_dir]
                top_part = start_dir.split('.')[0]
                start_dir = os.path.abspath(os.path.dirname((the_module.__file__)))
                if set_implicit_top:
                    self._top_level_dir = self._get_directory_containing_module(top_part)
                    sys.path.remove(top_level_dir)

        if is_not_importable:
            raise ImportError('Start directory is not importable: %r' % start_dir)

        base_tests = list(self._find_tests(start_dir, pattern))
        if not from_update:
            tests = self.filter_tests(base_tests)
            return self.suiteClass(tests, self)

        return self.suiteClass(base_tests, self)

    def loadTestsFromTestCase(self, testCaseClass):
        """Return a suite of all tests cases contained in testCaseClass"""
        if issubclass(testCaseClass, unittest.suite.TestSuite):
            raise TypeError("Test cases should not be derived from TestSuite."
                                " Maybe you meant to derive from TestCase?")
        testCaseNames = self.getTestCaseNames(testCaseClass)
        if not testCaseNames and hasattr(testCaseClass, 'runTest'):
            testCaseNames = ['runTest']
        testCases = []
        for tcn in testCaseNames:
            testCases.append(testCaseClass(
                tcn,
                cr=self.cr,
                uid=self.uid,
                cid=self.cid,
                update_module=self.update_module,
            ))

        loaded_suite = self.suiteClass(testCases)
        loaded_suite.loadder = self
        return loaded_suite


def format_error(error):
    """
    Format error message
    """
    if not isinstance(error, (tuple, list)):
        raise TypeError('error parameter must be a list')

    if not error:
        return ''

    if len(error) > 1:
        return '%s: %s' % (
            error[0],
            error[1],
        )
    else:
        return error[0]


class UnifieldTestResult(unittest.runner.TextTestResult):
    """
    Override of a TextTestResult to write information on the sync. database
    at each test done/error/failure.
    """

    def __init__(self, stream=None, descriptions=None, verbosity=None, pool=None, cr=None, uid=None, cid=None):
        super(UnifieldTestResult, self).__init__(stream, descriptions, verbosity)
        self.pool = pool
        self.cr = cr
        self.uid = uid
        self.cid = cid
        self.test_obj = None
        self.method_obj = None
        if self.pool:
            self.test_obj = self.pool.get('automatic.test')
            self.method_obj = self.pool.get('automatic.test.method')

    def write_test_method(self, test, data=None):
        """
        Return the ID of the automatic test
        """
        if data is None:
            data = {}

        if self.method_obj and data:
            t_ids = self.method_obj.search(self.cr, self.uid, [
                ('test_id', '=', test.test_id),
                ('name', '=', test._testMethodName),
            ])
            return self.method_obj.write(self.cr, self.uid, t_ids, data)

        return False

    def startTest(self, test):
        self.write_test_method(test, {
            'start_date': time.strftime('%Y-%m-%d %H:%M:%S'),
            'state': 'progress',
        })
        if self.test_obj:
            m_id = self.test_obj.search(self.cr, self.uid, [
                ('id', '=', test.test_id),
                ('start_date', '=', False),
            ])
            if m_id:
                self.test_obj.write(self.cr, self.uid, m_id, {
                    'start_date': time.strftime('%Y-%m-%d %H:%M:%S'),
                })
        return super(UnifieldTestResult, self).startTest(test)

    def stopTest(self, test):
        self.write_test_method(test, {'end_date': time.strftime('%Y-%m-%d %H:%M:%S')})
        return super(UnifieldTestResult, self).stopTest(test)

    def addError(self, test, err):
        self.write_test_method(test, {
            'message': format_error(err),
            'state': 'error',
            'traceback': traceback.format_exc(err[2]),
        })
        return super(UnifieldTestResult, self).addError(test, err)

    def addFailure(self, test, err):
        self.write_test_method(test, {
            'message': format_error(err),
            'state': 'fail',
            'traceback': traceback.format_exc(err[2]),
        })
        return super(UnifieldTestResult, self).addFailure(test, err)

    def addSuccess(self, test):
        self.write_test_method(test, {
            'state': 'done',
        })
        return super(UnifieldTestResult, self).addSuccess(test)

    def addSkip(self, test, reason):
        self.write_test_method(test, {
            'message': reason,
            'state': 'skip',
        })
        return super(UnifieldTestResult, self).addSkip(test, reason)

    def addExpectedFailure(self, test, err):
        self.write_test_method(test, {
            'message': format_error(err),
            'state': 'done',
            'traceback': traceback.format_exc(err[2]),
        })
        return super(UnifieldTestResult, self).addExpectedFailure(test, err)

    def addUnexpectedSuccess(self, test):
        self.write_test_method(test, {
            'message': 'Test succeed but should failed',
            'state': 'fail',
        })
        return super(UnifieldTestResult, self).addUnexpectedSuccess(test)

