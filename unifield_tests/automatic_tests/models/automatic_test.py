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

import base64

from osv import osv
from osv import fields

from unifield_tests.lib import yaml_import


class automatic_test(osv.osv):
    _name = 'automatic.test'
    _description = 'A functional test to launch or launched'
    _rec_name = 'template_id'
    _order = 'sequence_nb'

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
        'data_file': fields.binary(
            string='Data file',
        ),
        'data_filename': fields.char(
            string='Data filename',
            size=256,
        ),
        'sequence_nb': fields.integer(
            string='Sequence',
            readonly=True,
        ),
        'state': fields.function(
            _get_state,
            method=True,
            type='selection',
            selection=[
                ('draft', 'Draft'),
                ('not_run', 'Not started'),
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

    def name_get(self, cr, uid, ids, context=None):
        """
        Return the name of the template instead of this ID
        """
        if context is None:
            context = {}

        if not ids:
            return []

        if isinstance(ids, (int, long)):
            ids = [ids]

        return [(r['id'], r['template_id'][1]) for r in self.read(
            cr, uid, ids, ['template_id'], context, load='_classic_read')]

    def parse_file(self, cr, uid, ids, context=None):
        """
        Parse Yaml file
        """
        if context is None:
            context = {}

        if isinstance(ids, (int, long)):
            ids = [ids]

        for test in self.browse(cr, uid, ids, context=context):
            yaml_interpreter = yaml_import.UnifieldYamlInterpreter(cr, 'unifield_tests', {}, 'init', filename='test_fo.yml',)
            yaml_interpreter.process(base64.decodestring(test.data_file))
#            yaml_import(cr, 'unifield_tests', base64.decodestring(test.data_file))

        return True

    def add_file(self, cr, uid, ids, context=None):
        """
        Run a wizard to select a file
        """
        if context is None:
            context = {}

        if isinstance(ids, (int, long)):
            ids = [ids]

        wiz_model = 'automatic.test.add.file'
        test = self.browse(cr, uid, ids[0], context=context)
        wiz_id = self.pool.get(wiz_model).create(cr, uid, {
            'test_id': test.id,
            'data_file': test.data_file,
            'data_filename': test.data_filename,
        }, context=context)

        return {
            'type': 'ir.actions.act_window',
            'res_model': wiz_model,
            'res_id': wiz_id,
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
            'context': context,
        }

    def load_data_from_yml(self, cr, uid, filename, yaml_string):
        """
        Generic method to load data from Yaml files if the tests are run
        manually by the CLI
        """
        yaml_interpreter = yaml_import.UnifieldYamlInterpreter(cr, 'unifield_tests_data', {}, 'init', filename=filename,)
        yaml_interpreter.process(yaml_string)

        return True

automatic_test()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
