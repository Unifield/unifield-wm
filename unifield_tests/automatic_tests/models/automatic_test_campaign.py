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

import threading
import time

import pooler

from os import path

from osv import osv
from osv import fields
from tools.translate import _

from unifield_tests import unifield_unittest


class automatic_test_campaign(osv.osv):
    _name = 'automatic.test.campaign'
    _description = 'A test campaigne'

    _columns = {
        'name': fields.char(
            string='Nane',
            size=256,
            required=True,
        ),
        'test_template_ids': fields.many2many(
            'automatic.test.template',
            'campaign_id',
            'test_template_id',
            'auto_test_campaign_template_rel',
            string='Test cases',
        ),
        'test_ids': fields.one2many(
            'automatic.test',
            'campaign_id',
            string='Tests',
        ),
        'state': fields.selection(
            selection=[
                ('draft', 'Draft'),
                ('not_run', 'Not Run'),
                ('progress', 'In progress'),
                ('done', 'Done'),
            ],
            string='Status',
            required=True,
            readonly=True,
        ),
        'start_date': fields.datetime(
            string='Start date',
            readonly=True,
        ),
        'end_date': fields.datetime(
            string='End date',
            readonly=True,
        ),
    }

    _defaults = {
        'state': lambda *a: 'draft',
    }

    def copy(self, cr, uid, copy_id, defaults, context=None):
        """
        Re-set start and end dates on copy
        """
        if defaults is None:
            defaults = {}

        if 'start_date' not in defaults:
            defaults['start_date'] = False
        if 'end_date' not in defaults:
            defaults['end_date'] = False
        if 'test_ids' not in defaults:
            defaults['test_ids'] = []

        return super(automatic_test_campaign, self).\
            copy(cr, uid, copy_id, defaults, context=context)

    def generate_tests(self, cr, uid, ids, context=None):
        """
        Check if the campaign as only one test case choosen.
        Create the functional tests.
        """
        test_obj = self.pool.get('automatic.test')

        if context is None:
            context = {}

        if isinstance(ids, (int, long)):
            ids = [ids]

        test_to_run = []
        for campaign in self.browse(cr, uid, ids, context=context):
            if not campaign.test_template_ids:
                raise osv.except_osv(
                    _('Error'),
                    _('You have to select test cases before generate tests.'),
                )

            for tmp in campaign.test_template_ids:
                test_to_run.append(test_obj.create(cr, uid, {
                    'template_id': tmp.id,
                    'campaign_id': campaign.id,
                    'state': 'draft',
                }, context=context))

        self.write(cr, uid, ids, {'state': 'not_run'}, context=context)

        return self.update(cr, uid, ids, context=context)

    def run_campaign(self, cr, uid, ids, context=None):
        """
        Check if the campaign as only one test generated and run them.
        """
        test_obj = self.pool.get('automatic.test')

        if context is None:
            context = {}

        if isinstance(ids, (int, long)):
            ids = [ids]

        # TODO: Add a check to get all DB mappings good before running campaign

        test_ids = test_obj.search(cr, uid, [
            ('campaign_id', 'in', ids),
            ('state', '=', 'draft'),
        ], limit=1, context=context)
        if not test_ids:
            raise osv.except_osv(
                _('Error'),
                _('You cannot run a campaign without tests'),
            )
        else:
            import pdb
            pdb.set_trace()
            test_obj.write(cr, uid, test_ids, {
                'state': 'not_run',
            }, context=context)

        self.write(cr, uid, ids, {
            'state': 'progress',
            'start_date': time.strftime('%Y-%m-%d %H:%M:%S'),
        }, context=context)

        self.run_tests(cr, uid, ids, context=context)
#        cr.commit()
#        thread = threading.Thread(
#            target=self.run_tests,
#            args=(cr, uid, ids, context, True),
#        )
#        thread.start()

        return self.update(cr, uid, ids, context=context)


    def update(self, cr, uid, ids, context=None):
        """
        Update the view
        """
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': ids[0],
            'view_type': 'form',
            'view_mode': 'form,tree',
            'target': 'crush',
            'context': context,
        }

    def run_tests(self, cr, uid, ids, context=None, use_new_cursor=False):
        """
        Run the test campaign
        """
        if context is None:
            context = {}

        if isinstance(ids, (int, long)):
            ids = [ids]

        if use_new_cursor:
            cr = pooler.get_db(cr.dbname).cursor()

        try:
            test_dir = '%s/../../tests/' % path.dirname(path.realpath(__file__))
            for camp in self.browse(cr, uid, ids, context=context):
                # Discover and filter test cases
                loader = unifield_unittest.\
                    UnifieldTestLoader(self.pool, cr, uid, camp.id)
                suite = loader.discover(test_dir, pattern='test*.py')

                # Create a runner linked to the campaign
                result = unifield_unittest.UnifieldTestResult(
                    pool=self.pool,
                    cr=cr,
                    uid=uid,
                    cid=camp.id)
                # Launch tests
                suite(result)

                self.write(cr, uid, [camp.id], {
                    'state': 'done',
                    'end_date': time.strftime('%Y-%m-%d %H:%M:%S'),
                })
            if use_new_cursor:
                cr.commit()
        except:
            if use_new_cursor:
                cr.rollback()
        finally:
            if use_new_cursor:
                cr.close()

        return True

automatic_test_campaign()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
