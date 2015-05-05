#!/usr/bin/env python
# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
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
from lxml import etree


class dimension_3a(osv.osv):
    _name = 'dimension.3a'
    _description = 'Dimension 3a'

    _columns = {
        'ontime': fields.integer('On time'),
        'totlines': fields.float("Total lines"),
        'pct_ontime': fields.float("Percentage ontime"),
        'po_id': fields.many2one('purchase.order', "Purchase Order"),
        'pol_id': fields.many2one('purchase.order.line', "Purchase Order Line"),
        'sp_id': fields.many2one('stock.picking', "Stock Picking"),
        'sm_id': fields.many2one('stock.move', "Stock Move"),
        'delivery_requested_date': fields.date("Delivery Requested Date"),
        'sp_expect_date': fields.date("Expected Date"),
        'sm_actual_receipt_date': fields.date("Actual Receipt Date"),
        'categ': fields.char('Order Category', size=128),
        'order_type': fields.char('Order Type', size=128),
        'priority':  fields.char('Priority', size=128),
        'partner_type': fields.char('Partner Type', size=128),
        'name': fields.char('Name', size=128),
        'zone': fields.char('Zone', size=128),
        'state': fields.char('State', size=128),
        'default_code': fields.char('Product', size=128),
        'pn_main_type': fields.char('Main Type', size=128),
        'pn_group': fields.char('Group', size=128),
        'pn_family': fields.char('Family', size=128),
        'pn_root': fields.char('Root', size=128),
        'cnt': fields.integer('Number on time')
    }

dimension_3a()
