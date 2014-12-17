#!/usr/bin/env python
# -*- coding: utf8 -*-
from __future__ import print_function
from unifield_test import UnifieldTest

import time


class SupplyTest(UnifieldTest):

    def setUp(self):
        super(SupplyTest, self).setUp()

    def tearDown(self):
        super(SupplyTest, self).tearDown()

    def run_auto_pos_creation(self, db, order_to_check=None):
        """
        Runs the Auto POs creation schedule.
        If 'order_to_check' is defined, check if all lines of the given
        order are confirmed.

        :param db: Cursor to the database
        :param order_to_checK: ID of the order to check

        :return True
        :rtype bool
        """
        order_obj = db.get('sale.order')
        proc_obj = db.get('procurement.order')

        pr = order_obj.browse(order_to_check).procurement_request

        new_order_id = None
        if pr:
            state = 'progress'
        else:
            state = 'done'

        order_state = order_obj.read(order_to_check, ['state'])['state']
        while order_state != state:
            time.sleep(0.5)
            order_state = order_obj.read(order_to_check, ['state'])['state']

        if pr:
            new_order_id = order_to_check
        else:
            new_order_ids = order_obj.search([
                ('original_so_id_sale_order', '=', order_to_check)
            ])

            self.assert_(len(new_order_ids) > 0, msg="""
No split of FO found !""")
            if new_order_ids:
                new_order_id = new_order_ids[0]

        proc_obj.run_scheduler()

        return new_order_id