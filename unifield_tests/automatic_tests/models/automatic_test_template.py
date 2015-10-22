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

from os import path

from osv import osv
from osv import fields
from tools.translate import _

from unifield_tests import unifield_unittest


class automatic_test_template(osv.osv):
    _name = 'automatic.test.template'
    _description = 'Template of the automatic test'

    def update_automatic_test_template(self, cr, uid, *a, **b):
        """
        Create automatic test templates according to test in unifield_tests
        module.
        """
        tmpl_obj = self.pool.get('automatic.test.template')

        test_dir = '%s/../../tests/' % path.dirname(path.realpath(__file__))
        loader = unifield_unittest.\
            UnifieldTestLoader(self.pool, cr, uid, None, update_module=True)
        suite = loader.discover(test_dir, pattern='test*.py', from_update=True)

        tests = []

        def discover_tests(d_suite):
            for test in d_suite:
                if isinstance(test, unittest.suite.TestSuite):
                    discover_tests(test)
                elif isinstance(test, unittest.case.TestCase):
                    if test not in tests:
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
    }

automatic_test_template()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
