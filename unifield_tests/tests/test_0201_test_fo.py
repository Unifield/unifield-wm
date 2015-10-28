#!/usr/bin/python
# -*- coding: utf8 -*-
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


from __future__ import print_function
from unifield_test import UnifieldTest
from oerplib.error import RPCError

import time


class FOTest(UnifieldTest):
    category = 'Supply'
    description = 'Some integrity checks on FO'
    no_auto = []
    yaml_file = 'test_0201_test_fo.yml'

    def setUp(self):
        self.used_db = self.hq1c1
        db = self.used_db
        self.fo_obj = db.get('sale.order')
        self.fol_obj = db.get('sale.order.line')

    def test_validation_no_price_unit(self):
        """
        Create a FO with two lines. One of these lines have no price unit.
        Expected result: An error must be raised
        """
        partner_id = self.get_record(self.used_db, 'fo_test_ext_cust')
        order_type = 'regular'

        # Get the analytic distribution
        distrib_id = self.get_record(self.used_db, 'distrib_1')

        order_values = self.fo_obj.\
            onchange_partner_id(None, partner_id, order_type).get('value', {})
        order_values.update({
            'order_type': order_type,
            'procurement_request': False,
            'partner_id': partner_id,
            'ready_to_ship_date': time.strftime('%Y-%m-%d'),
            'analytic_distribution_id': distrib_id,
        })
        order_id = self.fo_obj.create(order_values)

        # Create order lines
        prod_log1_id = self.get_record(self.used_db, 'prod_log_1')
        prod_log2_id = self.get_record(self.used_db, 'prod_log_2')
        uom_pce_id = self.get_record(
            self.used_db,
            'product_uom_unit',
            module='product'
        )

        line_values = {
            'order_id': order_id,
            'product_id': prod_log1_id,
            'product_uom': uom_pce_id,
            'product_uom_qty': 10.0,
            'type': 'make_to_order',
            'price_unit': 10.0,
        }
        self.fol_obj.create(line_values)

        line_values.update({
            'product_id': prod_log2_id,
            'price_unit': 0.0,
        })
        self.fol_obj.create(line_values)

        try:
            self.hq1c1.exec_workflow('sale.order', 'order_validated', order_id)
            self.assert_(
                False,
                'No error message at FO validation with line with no price.',
            )
        except RPCError as e:
            return True

