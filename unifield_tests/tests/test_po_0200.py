#!/usr/bin/env python
# -*- coding: utf8 -*-

from __future__ import print_function
from supply import SupplyTest

import time


class TestPO0200(SupplyTest):

    def setUp(self):
        super(TestPO0200, self).setUp()

        # Launch a first synchronization
        self.synchronize(self.p1)
        self.synchronize(self.c1)
        self.synchronize(self.p1)

        self.c1_partner_id = self.get_sync_partner_id(self.p1, self.c1)
        self.c1_partner_name = self.get_db_partner_name(self.c1)
        self.p1_partner_id = self.get_sync_partner_id(self.c1, self.p1)
        self.p1_partner_name = self.get_db_partner_name(self.p1)

        # Project data / object browsers
        self.p1_po_obj = self.p1.get('purchase.order')
        self.p1_pol_obj = self.p1.get('purchase.order.line')
        self.p1_pick_obj = self.p1.get('stock.picking')
        self.p1_in_proc_obj = self.p1.get('stock.incoming.processor')

        self.p1_po_id = []
        self.p1_pol_ids = []
        self.p1_in_id = []

        # Coordination data / object browsers
        self.c1_fo_obj = self.c1.get('sale.order')
        self.c1_fol_obj = self.c1.get('sale.order.line')
        self.c1_pick_obj = self.c1.get('stock.picking')
        self.c1_out_proc_obj = self.c1.get('outgoing.delivery.processor')

        self.c1_fo_ids = []

    def tearDown(self):
        super(TestPO0200, self).tearDown()

        if self.p1_in_id:
            in_state = self.p1_pick_obj.read(self.p1_in_id, ['state'])['state']
            if in_state in ('cancel', 'done'):
                pass

            w_res = self.p1_pick_obj.enter_reason([self.p1_in_id], {
                'active_ids': [self.p1_in_id],
                'cancel_type': 'update_out',
            })
            self.p1.get(w_res['res_model']).write([w_res['res_id']], {
                'change_reason': 'tearDownTest',
            })
            self.p1.get(w_res['res_model']).do_cancel([w_res['res_id']], {
                'cancel_type': 'update_out',
                'active_ids': [self.p1_in_id],
            })

        if self.p1_po_id:
            po_state = self.p1_po_obj.browse(self.po_id).state
            if po_state in ('cancel', 'done'):
                pass
            elif po_state == 'draft':
                self.p1_po_obj.unlink(self.po_id)
            elif po_state == 'confirmed':
                self.p1_po_obj.purchase_cancel(self.po_id)

        return

    def create_po(self, o_categ='other', o_priority='normal'):
        """
        Create a new PO from scratch with 4 lines at Project side to
        Coordination

        :param o_categ: Order category
        :param o_priority: Order priority
        :param p_type: Partner type
        :return: ID of the new PO
        """
        order_data = {
            'partner_id': self.c1_partner_id,
            'location_id': self.get_record(self.p1,
                                           'stock_location_stock', 'stock'),
            'categ': o_categ,
            'priority': o_priority,
        }
        order_data.update(
            self.p1_po_obj.onchange_partner_id(
                None,
                self.c1_partner_id,
                time.strftime('%Y-%m-%d'),
            ).get('value', {})
        )
        self.po_id = self.p1_po_obj.create(order_data)

        po_brw = self.p1_po_obj.browse(self.po_id)

        # Make many checks
        self.assert_(
            po_brw.order_type == 'regular',
            """The default order type of the PO is not good :: Is %s,
should be 'regular'.""" % (po_brw.order_type,),
        )
        self.assert_(
            po_brw.categ == o_categ,
            """The order category is not kept at PO creation - Is %s,
should be %s.""" % (po_brw.categ, o_categ),
        )
        self.assert_(
            po_brw.priority == o_priority,
            """The order priority is not kept at PO creation - Is %s,
should be %s.""" % (po_brw.priority, o_priority),
        )

        return self.po_id

    def create_service_lines(self):
        """
        Add four lines on the PO. All lines contain service products.

        :return:
        """
         # New line with SRV product
        line_data = {
            'product_id': self.get_record(self.p1, 'prod_srv_1'),
            'product_uom': self.get_record(self.p1,
                                           'product_uom_unit', 'product'),
            'price_unit': 3.05,
            'product_qty': 150.00,
            'order_id': self.po_id,
        }
        self.p1_pol_ids.append(
            self.p1_pol_obj.create(line_data)
        )

        line_data = {
            'product_id': self.get_record(self.p1,
                                          'prod_srv_2'),
            'product_uom': self.get_record(self.p1,
                                           'product_uom_unit', 'product'),
            'price_unit': 4.18,
            'product_qty': 230.00,
            'order_id': self.po_id,
        }
        self.p1_pol_ids.append(
            self.p1_pol_obj.create(line_data)
        )

        line_data = {
            'product_id': self.get_record(self.p1, 'prod_srv_3'),
            'product_uom': self.get_record(self.p1,
                                           'product_uom_unit', 'product'),
            'price_unit': 3.05,
            'product_qty': 150.00,
            'order_id': self.po_id,
        }
        self.p1_pol_ids.append(
            self.p1_pol_obj.create(line_data)
        )

        line_data = {
            'product_id': self.get_record(self.p1, 'prod_srv_4'),
            'product_uom': self.get_record(self.p1,
                                           'product_uom_unit', 'product'),
            'price_unit': 18.00,
            'product_qty': 10.00,
            'order_id': self.po_id,
        }
        self.p1_pol_ids.append(
            self.p1_pol_obj.create(line_data)
        )

    def create_lines_from_scratch(self):
        """
        Add four lines on the PO. Two with a MED product and the two others
        with a LOG product.

        :return:
        """
        # New line with MED product
        line_data = {
            'product_id': self.get_record(self.p1, 'prod_med_1'),
            'product_uom': self.get_record(self.p1,
                                           'product_uom_unit', 'product'),
            'price_unit': 3.05,
            'product_qty': 150.00,
            'order_id': self.po_id,
        }
        self.p1_pol_ids.append(
            self.p1_pol_obj.create(line_data)
        )

        line_data = {
            'product_id': self.get_record(self.p1,
                                          'prod_med_2'),
            'product_uom': self.get_record(self.p1,
                                           'product_uom_unit', 'product'),
            'price_unit': 4.18,
            'product_qty': 230.00,
            'order_id': self.po_id,
        }
        self.p1_pol_ids.append(
            self.p1_pol_obj.create(line_data)
        )

        # New line with LOG product
        line_data = {
            'product_id': self.get_record(self.p1, 'prod_log_1'),
            'product_uom': self.get_record(self.p1,
                                           'product_uom_unit', 'product'),
            'price_unit': 3.05,
            'product_qty': 150.00,
            'order_id': self.po_id,
        }
        self.p1_pol_ids.append(
            self.p1_pol_obj.create(line_data)
        )

        line_data = {
            'product_id': self.get_record(self.p1, 'prod_log_2'),
            'product_uom': self.get_record(self.p1,
                                           'product_uom_unit', 'product'),
            'price_unit': 18.00,
            'product_qty': 10.00,
            'order_id': self.po_id,
        }
        self.p1_pol_ids.append(
            self.p1_pol_obj.create(line_data)
        )

    def generate_test(self, cat, prio, sp=False):
        """
        1. Create a new PO with these attributes:
            * Order type: Regular
            * Order category: Other
            * Priority: Normal

        2. Create four lines from scratch
        3. Check the printed report
        4. Fill the analytic distribution
        5. Validate the PO
        6. Launch the synchronization
        7. Check FO creation at Coordination side
        8. Validate and source the FO at Coordination side
        9. Synchronize and check the state of the PO at Project side
        10. Convert the Picking ticket to standard OUT
        11. Process all the standard OUT
        12. Check the state of the FO at Coordination side
        13. Synchronize and check the creation of IN at Project side
        14. Process the IN at Project side
        15. Check the state of the PO at Project side

        :return:
        """
        self.create_po(
            o_categ=cat,
            o_priority=prio,
        )

        if sp:
            self.create_service_lines()
        else:
            self.create_lines_from_scratch()

        # Try to print the PO report
        self.p1.report(
            'msf.purchase.order',
            'purchase.order',
            self.po_id,
        )

        # Add an analytic distribution
        distrib_id = self.get_record(self.p1, 'distrib_1')
        self.p1_po_obj.write([self.po_id], {
            'analytic_distribution_id': distrib_id,
        })

        # Check Order impact vs. Budget printable doc.
        self.p1.report(
            'msf.pdf.engagement',
            'purchase.order',
            self.po_id,
        )

        # Check allocation report
        self.p1.report(
            'po.line.allocation.report',
            'purchase.order',
            self.po_id,
        )

        # Validate the PO
        po_state = self.p1_po_obj.read(self.po_id, ['state'])['state']
        self.assert_(
            po_state == 'draft',
            msg="""The state of the generated PO is %s - Should be
'draft'""" % po_state,
        )
        self.p1.exec_workflow(
            'purchase.order',
            'purchase_confirm',
            self.po_id,
        )
        po_brw = self.p1_po_obj.browse(self.po_id)
        p1_po_name = po_brw.name
        self.assert_(
            po_brw.state == 'confirmed',
            msg="""The state of the generated PO is %s - Should be
'confirmed'""" % po_brw.state,
        )

        # Launch the synchronization
        self.synchronize(self.p1)
        self.synchronize(self.c1)

        # Check the FO creation at coordination side
        fo_client_ref = '%s%%%s' % (self.p1_partner_name, p1_po_name)
        self.c1_fo_ids = self.c1_fo_obj.search([
            ('client_order_ref', '=ilike', fo_client_ref),
        ])
        self.assert_(
            self.c1_fo_ids,
            msg="There is no FO found at Coordination side",
        )

        for fo in self.c1_fo_obj.browse(self.c1_fo_ids):
            self.c1.exec_workflow(
                'sale.order',
                'order_validated',
                fo.id,
            )

        fo_line_ids = self.c1_fol_obj.search([
            ('order_id', 'in', self.c1_fo_ids)
        ])

        # Source all lines on a Purchase Order to ext_supplier_1
        self.c1_fol_obj.write(fo_line_ids, {
            'type': 'make_to_stock',
            'location_id': self.get_record(self.c1,
                                           'stock_location_stock', 'stock'),
        })
        self.c1_fol_obj.confirmLine(fo_line_ids)

        # Run the scheduler
        self.c1_fo_id = \
             self.run_auto_pos_creation(self.c1,
                                        order_to_check=self.c1_fo_ids[0])
        #
        # line_ids = self.c1_fol_obj.search([('order_id', '=', self.c1_fo_id)])
        # not_sourced = True
        # while not_sourced:
        #     not_sourced = False
        #     for line in self.c1_fol_obj.browse(line_ids):
        #         if line.procurement_id and line.procurement_id.state != 'running':
        #             not_sourced = True
        #     if not_sourced:
        #         time.sleep(1)

        self.c1_pick_ids = self.c1_pick_obj.search([
            ('sale_id', '=', self.c1_fo_id),
        ])

        # Synchronize and check the state of the PO at Project side
        self.synchronize(self.c1)
        self.synchronize(self.p1)

        po_brw = self.p1_po_obj.read(self.po_id, ['state', 'name'])
        po_state = po_brw['state']
        po_name = po_brw['name']
        self.assert_(
            po_state == 'split',
            msg="The PO state is '%s' - Should be 'split'" % po_state,
        )
        po_ids = self.p1_po_obj.search([
            ('name', '=like', '%s%%' % po_name),
            ('state', '!=', 'split'),
        ])
        if po_ids:
            self.po_id = po_ids[0]

        # Convert the Picking ticket to standard OUT
        self.c1_pick_obj.convert_to_standard(self.c1_pick_ids)
        self.c1_pick_obj.force_assign(self.c1_pick_ids)

        # Process all the standard OUT
        wiz_res = self.c1_pick_obj.action_process(self.c1_pick_ids[0])
        self.c1_out_proc_obj.copy_all(wiz_res.get('res_id'))
        self.c1_out_proc_obj.do_partial(wiz_res.get('res_id'))

        # Check the state of the FO at Coordination side
        fo_state = self.c1_fo_obj.read(self.c1_fo_id, ['state'])['state']
        self.assert_(
            fo_state == 'done',
            msg="The FO state is '%s' - Should be 'done'" % fo_state,
        )

        # Synchronize and check the modification of the PO state and the
        # creation of IN at Project side
        self.synchronize(self.c1)
        self.synchronize(self.p1)

        po_brw = self.p1_po_obj.read(self.po_id, ['state', 'name'])
        po_state = po_brw['state']
        po_name = po_brw['name']
        self.assert_(
            po_state == 'approved',
            msg="The PO state is '%s' - Should be 'approved'" % po_state,
        )
        p1_po_ids = self.p1_po_obj.search([
            ('name', '=like', '%s%%' % po_name),
            ('state', '!=', 'split'),
        ])
        if po_ids:
            self.po_id = p1_po_ids[0]

        p1_in_ids = self.p1_pick_obj.search([
            ('purchase_id', '=', self.po_id),
            ('state', '=', 'shipped'),
        ])
        self.assert_(
            p1_in_ids,
            "There is no IN shipped available at Project side after sync.",
        )
        self.p1_in_id = p1_in_ids[0]

        # Process the IN at Project side
        wiz_res = self.p1_pick_obj.action_process(self.p1_in_id)
        self.p1_in_proc_obj.copy_all(wiz_res.get('res_id'))
        self.p1_in_proc_obj.do_incoming_shipment(wiz_res.get('res_id'))

        in_state = self.p1_pick_obj.read(self.p1_in_id, ['state'])['state']
        stop = 0
        while in_state != 'done' and stop < 10:
            stop += 1
            time.sleep(3)
            in_state = self.p1_pick_obj.read(self.p1_in_id, ['state'])['state']

        self.assert_(
            stop <= 10,
            msg="""The incoming shipment is not done""",
        )

        # Check the state of the PO at Project side
        po_state = self.p1_po_obj.read(self.po_id, ['state'])['state']
        self.assert_(
            po_state == 'done',
            msg="""The PO state is '%s' - Should be 'done'""" % po_state,
        )

    def test_po_0201_normal_other(self):
        """
        PO with these parameters:
          * Partner type: Internal
          * Order priority: Normale
          * Order category: Other

        :return:
        """
        self.generate_test('other', 'normal')

    def test_po_0202_priority_other(self):
        """
        PO with these parameters:
          * Partner type: Internal
          * Order priority: Priority
          * Order category: Other

        :return:
        """
        self.generate_test('other', 'priority')

    def test_po_0203_mergency_other(self):
        """
        PO with these parameters:
          * Partner type: Internal
          * Order priority: Emergency
          * Order category: Other

        :return:
        """
        self.generate_test('other', 'emergency')

    def test_po_0204_normal_log(self):
        """
        PO with these parameters:
          * Partner type: Internal
          * Order priority: Normale
          * Order category: Log

        :return:
        """
        self.generate_test('log', 'normal')

    def test_po_0205_priority_log(self):
        """
        PO with these parameters:
          * Partner type: Internal
          * Order priority: Priority
          * Order category: Log

        :return:
        """
        self.generate_test('log', 'priority')

    def test_po_0206_emergency_log(self):
        """
        PO with these parameters:
          * Partner type: Internal
          * Order priority: Emergency
          * Order category: Log

        :return:
        """
        self.generate_test('log', 'emergency')

    def test_po_0207_normal_medical(self):
        """
        PO with these parameters:
          * Partner type: Internal
          * Order priority: Normale
          * Order category: Medical

        :return:
        """
        self.generate_test('medical', 'normal')

    def test_po_0208_priority_medical(self):
        """
        PO with these parameters:
          * Partner type: Internal
          * Order priority: Priority
          * Order category: Medical

        :return:
        """
        self.generate_test('medical', 'priority',)

    def test_po_0209_emergency_medical(self):
        """
        PO with these parameters:
          * Partner type: Internal
          * Order priority: Emergency
          * Order category: Medical

        :return:
        """
        self.generate_test('medical', 'emergency')

    def test_po_0300_service_products(self):
        """
        PO with these parameters:
          * Partner type: Internal
          * Order priority: Emergency
          * Order category: Service

        Add only service products.

        :return:
        """
        self.generate_test('service', 'emergency', sp=True)

def get_test_class():
    return TestPO0200