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
from tools.translate import _


class test_db_mapping(osv.osv):
    _name = 'test.db.mapping'
    _description = 'Mapping between keyword used in test and DB name'
    _rec_name = 'keyword'

    def _get_db_to_use(self, cr, uid, ids, field_name, args, context=None):
        """
        If the mapping use a custom name, return the custom name entered,
        else, use the name of the instance.
        """
        if context is None:
            context = {}

        if isinstance(ids, (int, long)):
            ids = [ids]

        res = {}
        for db_map in self.browse(cr, uid, ids, context=context):
            if db_map.custom_name_ok:
                res[db_map.id] = db_map.custom_name
            else:
                res[db_map.id] = db_map.instance_id.name

            self._check_unique_name(cr, uid, res[db_map.id], context=context)

        return res

    _columns = {
        'keyword': fields.char(
            string='Keyword',
            size=64,
            required=True,
            readonly=True,
        ),
        'db_to_use': fields.function(
            _get_db_to_use,
            method=True,
            type='char',
            string='DB to use',
            size=512,
            readonly=True,
            store={
                'test.db.mapping': (
                    lambda self, cr, uid, ids, c=None: ids,
                    ['instance_id', 'custom_name', 'custom_name_ok'],
                    10,
                ),
            },
        ),
        'instance_id': fields.many2one(
            'sync.server.entity',
            string='Instance',
        ),
        'custom_name_ok': fields.boolean(
            string='Use a custom name ?',
        ),
        'custom_name': fields.char(
            size=512,
            string='Custom name',
        ),
    }

    _defaults = {
        'instance_id': False,
        'custom_name_ok': False,
        'custom_name': False,
    }

    def _check_unique_name(self, cr, uid, db_name, context=None):
        """
        Check that a DB name to use is not already set on a mapping.
        """
        if context is None:
            context = {}

        if db_name:
            same_maps = self.search(cr, uid, [
                ('db_to_use', '=', db_name),
            ], limit=2, context=context)
            if len(same_maps) > 1:
                raise osv.except_osv(
                    _('Error'),
                    _('You cannot have a DB name mapped twice.'),
                )

        return True

test_db_mapping()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
