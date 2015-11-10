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


class automatic_test_key_value(osv.osv):
    """
    Key/Value store for automated test
    - key is unique
    - best practice: prefix the key by the test # followed by .
        => example of prefix: test_0110.
    """
    _name = 'automatic.test.key.value'
    _description = 'Automated test: key/value store'
    _rec_name = 'key'

    _sql_constraints = [
        ('key_key', 'UNIQUE (KEY)', 'You can not have 2 values with same key'),
    ]

    _columns = {
        'key': fields.char(
            string='Keyword',
            size=80,
            required=True,
            readonly=True,
            select=True,
        ),

        'val': fields.char(
            size=512,
            string='Value',
        ),
    }

    def get_val(self, cr, uid, key_or_id, default=None, context=None):
        """
        get val by db id or key
        """
        if isinstance(key_or_id, (int, long, )):
            ids = [key_or_id, ]
        else:
            ids = self.search(cr, uid, [ ('key', '=', key_or_id), ],
                context=context)

        if ids:
            return self.read(cr, uid,
                [ids[0]], ['val'], context=context)[0]['val'] or default
        return default

automatic_test_key_value()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
