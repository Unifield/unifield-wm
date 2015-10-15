#!/usr/bin/env python
# -*- coding: utf8 -*-

__author__ = 'fabien'

from resourcing import ResourcingTest
import time
import sys


class SyncPerfomance(ResourcingTest):

    def setUp(self):
        """
        Create a PO at Project side to Coordo with
        two lines.
        :return:
        """

        super(SyncPerfomance, self).setUp()

        # C1
        self.c_so_obj = self.c1.get('sale.order')
        self.c_sol_obj = self.c1.get('sale.order.line')
        self.c_po_obj = self.c1.get('purchase.order')
        self.c_pol_obj = self.c1.get('purchase.order.line')
        self.c_partner_obj = self.c1.get('res.partner')
        self.c_lc_obj = self.c1.get('sale.order.leave.close')
        self.c_so_cancel_obj = self.c1.get('sale.order.cancelation.wizard')

        # P1
        self.p_so_obj = self.p1.get('sale.order')
        self.p_sol_obj = self.p1.get('sale.order.line')
        self.p_po_obj = self.p1.get('purchase.order')
        self.p_pol_obj = self.p1.get('purchase.order.line')
        self.p_partner_obj = self.p1.get('res.partner')
        self.p_lc_obj = self.p1.get('sale.order.leave.close')
        self.p_so_cancel_obj = self.p1.get('sale.order.cancelation.wizard')
        self.start_time = time.time()

    def tearDown(self):
        duration = time.time() - self.start_time
        #self.duration += duration

        # write time result to be able to bench
        #print "%s: %.3f" % (self.id(), duration)
        super(SyncPerfomance, self).tearDown()

    def createObject(self, object_number=1):
        for i in range(object_number):
            # Create a PO at P1 with two products to C1
            # Prepare values for the field order
            prod_log1_id = self.get_record(self.p1, 'prod_log_1')
            prod_log2_id = self.get_record(self.p1, 'prod_log_2')
            uom_pce_id = self.get_record(self.p1, 'product_uom_unit', module='product')
            location_id = self.get_record(self.p1, 'stock_location_stock', module='stock')

            partner_name = self.get_db_partner_name(self.c1)
            partner_ids = self.p_partner_obj.search([('name', '=', partner_name)])
            distrib_id = self.create_analytic_distribution(self.p1)

            order_values = {
                'order_type': 'regular',
                'partner_id': partner_ids[0],
                'rfq_ok': False,
                'location_id': location_id,
                'analytic_distribution_id': distrib_id,
            }

            change_vals = self.p_po_obj.\
                onchange_partner_id(None, partner_ids[0], time.strftime('%Y-%m-%d')).get('value', {})
            order_values.update(change_vals)

            self.p_po_id = self.p_po_obj.create(order_values)

            # Create order lines
            # First line
            line_values = {
                'order_id': self.p_po_id,
                'product_id': prod_log1_id,
                'product_uom': uom_pce_id,
                'product_qty': 10.0,
                'price_unit': 10.00,
                'type': 'make_to_order',
            }
            self.p_pol_obj.create(line_values)

            # Second line
            line_values.update({
                'product_id': prod_log2_id,
                'product_uom_qty': 20.0,
                'price_unit': 10.0,
            })
            self.p_pol_obj.create(line_values)

            # Validate the sale order, to have them synchronized
            self.p1.exec_workflow('purchase.order', 'purchase_confirm', self.p_po_id)

    def synchronizeInstances(self):

            # Synchronize
            self.synchronize(self.p1)
            self.synchronize(self.c1)


    def test_010_objectCreation(self):
        """Create object, synchronize, and check the synchronization was done
        correctly
        :return:
        """
        self.synchronizeInstances()
        self.createObject(object_number=10)

    def test_020_synchronisation(self):
        """Do the synchronization in a separate test as we want to improve
        synchronization performance, it is better to do it in a separate test.
        That's why the order of these tests is very important. They are
        launched with there alphabetical name priority.
        """
        self.synchronizeInstances()

    def test_030_100objectsCreation(self):
        self.synchronizeInstances()
        self.createObject(object_number=100)

    def test_040_100synchronisations(self):
        self.synchronizeInstances()


def get_test_class():
    return SyncPerfomance
