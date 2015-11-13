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


class test_model_data(osv.osv):
    _name = 'test.model.data'
    _description = 'Model data to be used in unifield tests'

    _columns = {
        'name': fields.char(
            size=256,
            string='Name',
            required=True,
        ),
        'module': fields.char(
            size=256,
            string='Module',
            required=True,
        ),
        'model': fields.char(
            size=256,
            string='Model',
            required=True,
        ),
        'res_id': fields.integer(
            string='ID',
        ),
    }

    def get_object_reference(self, cr, uid, module, xml_id):
        """
        Return ID, model and res ID of the test.model.data if exists
        or the same field of the ir.model.data
        """
        data_ids = self.search(cr, uid, [('module', '=', module), ('name', '=', xml_id)])
        if data_ids:
            data_id = data_ids[0]
        else:
            data_ids = self.pool.get('ir.model.data').search(cr, uid, [
                ('module', '=', module),
                ('name', '=', xml_id),
            ])
            # Check if the data is synchronized
            if not data_ids:
                data_ids = self.pool.get('ir.model.data').search(cr, uid, [
                    ('module', '=', 'sd'),
                    ('name', '=', '%s_%s' % (module, xml_id)),
                ])
            if data_ids:
                data_brw = self.pool.get('ir.model.data').browse(cr, uid, data_ids[0])
                data_id = self.create(cr, uid, {
                    'module': data_brw.module,
                    'name': data_brw.name,
                    'res_id': data_brw.res_id,
                    'model': data_brw.model,
                })
            else:
                raise ValueError('No reference to %s.%s' % (module, xml_id))

        res = self.read(cr, uid, data_id, ['model', 'res_id'])
        return (res['id'], res['model'], res['res_id'])

test_model_data()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
