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

from osv import osv
from osv import fields


class automatic_test(osv.osv):
    _name = 'automatic.test'
    _description = 'A functional test to launch or launched'
    _rec_name = 'template_id'

    def _get_end_date(self, cr, uid, ids, field_name, args, context=None):
        """
        Compute the end date as the max end date of the tests.
        """
        if context is None:
            context = {}

        if isinstance(ids, (int, long)):
            ids = [ids]

        res = {}
        for test in self.browse(cr, uid, ids, context=context):
            edate = False
            for method in test.method_ids:
                if not edate or edate < method.end_date:
                    edate = method.end_date

            res[test.id] = edate

        return res

    def _get_state(self, cr, uid, ids, field_name, args, context=None):
        """
        Compute the state of the test according to result of Test methods.
        """
        if context is None:
            context = {}

        if isinstance(ids, (int, long)):
            ids = [ids]

        res = {}
        for test in self.browse(cr, uid, ids, context=context):
            tc = test.campaign_id
            draft_tc = tc and tc.state in ('draft', 'not_run')
            res[test.id] = draft_tc and 'draft' or 'not_run'
            done = 0
            progress = 0
            fail = 0

            for method in test.method_ids:
                if method.state == 'done':
                    done += 1
                elif method.state == 'progress':
                    progress += 1
                elif method.state == 'fail':
                    fail += 1
                elif method.state == 'error':
                    res[test.id] = 'error'
                    break

            if done and done == len(test.method_ids):
                res[test.id] = 'done'
            elif fail:
                res[test.id] = 'fail'
            elif progress:
                res[test.id] = 'progress'

        return res

    _columns = {
        'template_id': fields.many2one(
            'automatic.test.template',
            string='Template',
            required=True,
            ondelete='cascade',
        ),
        'campaign_id': fields.many2one(
            'automatic.test.campaign',
            string='Campaign',
            required=True,
            ondelete='cascade',
        ),
        'test_file': fields.binary(
            string='Test file',
        ),
        'state': fields.function(
            _get_state,
            method=True,
            type='selection',
            selection=[
                ('draft', 'Draft'),
                ('not_run', 'Not run'),
                ('progress', 'In progress'),
                ('done', 'Done'),
                ('fail', 'Failed'),
                ('error', 'Error'),
            ],
            string='Status',
            readonly=True,
        ),
        'method_ids': fields.one2many(
            'automatic.test.method',
            'test_id',
            string='Test methods',
            readonly=True,
        ),
        'start_date': fields.datetime(
            string='Start date',
            readonly=True,
        ),
        'end_date': fields.function(
            _get_end_date,
            method=True,
            type='datetime',
            string='End date',
            readonly=True,
        ),
    }

automatic_test()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
