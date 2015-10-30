#!/usr/bin/env python
# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2011 TeMPO Consulting, MSF. All Rights Reserved
#    Developer: Olivier DOSSMANN
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


class automatic_test_add_file(osv.osv_memory):
    _name = 'automatic.test.add.file'
    _description = 'Wizard to select a data file for unit tests'

    _columns = {
        'test_id': fields.many2one(
            'automatic.test',
            string='Test',
            required=True,
            readonly=True,
        ),
        'data_file': fields.binary(
            string='Data file',
            required=True,
        ),
        'data_filename': fields.char(
            string='Data filename',
            size=256,
        ),
    }

    def add_file(self, cr, uid, ids, context=None):
        """
        Add the selected file on the test
        """
        if context is None:
            context = {}

        if isinstance(ids, (int, long)):
            ids = [ids]

        # TODO: Add a first parsing of the file to check good format
        for wiz in self.browse(cr, uid, ids, context=context):
            self.pool.get('automatic.test').write(cr, uid, [wiz.test_id.id], {
                'data_file': wiz.data_file,
            }, context=context)

        return {
            'type': 'ir.actions.act_window_close',
        }

automatic_test_add_file()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
