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


import sys
import base64

import unittest

from os import path
from os import walk

from osv import osv
from osv import fields
from tools.translate import _

from unifield_tests.lib import unifield_unittest


class automatic_test_template(osv.osv):
    _name = 'automatic.test.template'
    _description = 'Template of the automatic test'

    def update_automatic_test_template(self, cr, uid, *a, **b):
        """
        Create automatic test templates according to test in unifield_tests
        module.
        """
        tmpl_obj = self.pool.get('automatic.test.template')

        test_dir = '%s/../../' % path.dirname(path.realpath(__file__))
        sys.path.append('%stests' % test_dir)

        suite = unifield_unittest.UnifieldTestSuite()
        test_modules = []
        added_paths = []

        loader = unifield_unittest.\
            UnifieldTestLoader(self.pool, cr, uid, None, update_module=True)

        for racine, _, files in walk(test_dir):
            directory = path.basename(racine)
            if directory == 'tests':
                for f in files:
                    if (f.startswith('test') and f.endswith('.py') and f != 'test.py'):
                        mod_name = f[:-3]
                        name = path.join(racine, f)
                        test_modules.append((name, mod_name))

        for module_info in sorted(test_modules, key=lambda x: x[1]):
            module_path = path.dirname(module_info[0])
            if module_path not in sys.path:
                sys.path.append(module_path)
                added_paths.append(module_path)

            module = __import__(module_info[1])
            if 'get_test_class' in module.__dict__:
                class_type = module.get_test_class()
                test_suite = loader.loadTestsFromTestCase(class_type)
                suite.addTest(test_suite)

            if 'get_test_suite' in module.__dict__:
                suite_type = module.get_test_suite()
                for class_type in suite_type:
                    test_suite = loader.loadTestsFromTestCase(class_type)
                    suite.addTest(test_suite)

        tests = []

        def discover_tests(d_suite):
            for test in d_suite:
                if isinstance(test, unittest.TestSuite):
                    discover_tests(test)
                elif isinstance(test, unittest.TestCase):
                    if test not in tests and (not hasattr(test, 'no_auto') or test._testMethodName not in test.no_auto):
                        tests.append(test)

        discover_tests(suite)

        for t in tests:
            # Don't import Test that failed to be imported
            if t.__class__.__name__ == 'ModuleImportFailure':
                continue
            tmpl_id = tmpl_obj.search(cr, uid, [
                ('test_class', '=', t.__class__.__name__),
            ])
            if not tmpl_id:
                desc = hasattr(t, 'description') and t.description
                cat = hasattr(t, 'category') and t.category or False
                tmpl_obj.create(cr, uid, {
                    'name': desc or t.__class__.__name__,
                    'test_class': t.__class__.__name__,
                    'test_type': cat,
                    'data_file': t.yaml_file and base64.encodestring(file('%s/tests/data/%s' % (test_dir, t.yaml_file)).read()) or False,
                    'data_filename': t.yaml_file,
                })

        return True

    _columns = {
        'name': fields.char(
            string='Name',
            size=256,
            required=True,
        ),
        'test_type': fields.char(
            string='Type',
            size=256,
            required=False,
        ),
        'test_class': fields.char(
            string='Model',
            size=256,
            required=True,
        ),
        'data_file': fields.binary(
            string='Data file',
        ),
        'data_filename': fields.char(
            string='Data filename',
            size=256,
        ),
    }

automatic_test_template()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
