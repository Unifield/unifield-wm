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


class automatic_test_method(osv.osv):
    _name = 'automatic.test.method'
    _description = 'A test method for a functional test case'

    _columns = {
        'name': fields.char(
            string='Name',
            size=256,
        ),
        'test_id': fields.many2one(
            'automatic.test',
            string='Test Case',
            readonly=True,
            ondelete='cascade',
        ),
        'state': fields.selection(
            selection=[
                ('not_run', 'Not started'),
                ('progress', 'In progress'),
                ('done', 'Done'),
                ('fail', 'Failed'),
                ('error', 'Error'),
                ('skip', 'Skip'),
            ],
            string='Status',
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
        'message': fields.text(
            string='Message',
            readonly=True,
        ),
        'traceback': fields.text(
            string='Traceback',
            readonly=True,
        ),
    }

    _defaults = {
        'state': lambda *a: 'not_run',
    }

automatic_test_method()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
