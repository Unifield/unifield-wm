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

    _columns = {
        'keyword': fields.char(
            string='Keyword',
            size=64,
            required=True,
            readonly=True,
        ),
        'instance_id': fields.many2one(
            'sync.server.entity',
            string='Linked instance',
        ),
        'db_to_use': fields.char(
            size=512,
            string='Name of the DB to use',
        ),
    }

    _defaults = {
        'instance_id': False,
        'db_to_use': False,
    }

    def on_change_instance(self, cr, uid, ids, instance_id, context=None):
        """
        Fill the DB to use field with the name of the selected instance.
        """
        inst_obj = self.pool.get('sync.server.entity')

        if context is None:
            context = {}

        if instance_id:
            inst_name = inst_obj.\
                read(cr, uid, instance_id, ['name'], context=context)
            return {
                'value': {
                    'db_to_use': inst_name['name'],
                },
            }

        return {}

    def create(self, cr, uid, vals, context=None):
        """
        Check if there is no other DB mapping with the same db_to_use value
        """
        if context is None:
            context = {}

        if vals.get('db_to_use'):
            same_maps = self.search(cr, uid, [
                ('db_to_use', '=', vals.get('db_to_use')),
            ], limit=1, context=context)
            if same_maps:
                raise osv.except_osv(
                    _('Error'),
                    _('You cannot have a DB name mapped twice.'),
                )

        return super(test_db_mapping, self).\
            create(cr, uid, vals, context=context)

    def write(self, cr, uid, ids, vals, context=None):
        """
        Check if there is no other DB mapping with the same db_to_use value
        """
        if context is None:
            context = {}

        if vals.get('db_to_use'):
            same_maps = self.search(cr, uid, [
                ('id', 'not in', ids),
                ('db_to_use', '=', vals.get('db_to_use')),
            ], limit=1, context=context)
            if same_maps:
                raise osv.except_osv(
                    _('Error'),
                    _('You cannot have a DB name mapped twice.'),
                )

        return super(test_db_mapping, self).\
            write(cr, uid, ids, vals, context=context)

test_db_mapping()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
