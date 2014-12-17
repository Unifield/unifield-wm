#!/usr/bin/env python
# -*- coding: utf8 -*-

from __future__ import print_function
from unifield_test import UnifieldTest

import time


class TestPO0100(UnifieldTest):

    def shortDescription(self):
        """
        Give a short description of the test.

        :return: Short description of the test
        """
        res = super(TestPO0100, self).shortDescription()
        res = """Create a PO from scratch with different products, then
validate it. After that, check if the printable documents are available. Then,
confirm the PO and check if the IN has been created. Process the IN and check
that the PO is now closed."""
        return res

    def setUp(self):
        """
        Prepare data for testing.

        The database used for all these tests are the Coordination database.

        :return:
        """
        super(TestPO0100, self).setUp()

        # DB parameters
        self.used_db = self.c1

        # Object browsers
        self.po_obj = self.used_db.get('purchase.order')
        self.pol_obj = self.used_db.get('purchase.order.line')
        self.pick_obj = self.used_db.get('stock.picking')
        self.in_proc_obj = self.used_db.get('stock.incoming.processor')

        # Data
        self.po_id = None
        self.pol_ids = []

    def tearDown(self):
        """
        Cancel or close the remaining open PO

        :return:
        """
        super(TestPO0100, self).tearDown()

        if self.in_id:
            in_state = self.pick_obj.read(self.in_id, ['state'])['state']
            if in_state in ('cancel', 'done'):
                pass

            w_res = self.pick_obj.enter_reason([self.in_id], {
                'active_ids': [self.in_id],
                'cancel_type': 'update_out',
            })
            self.used_db.get(w_res['res_model']).write([w_res['res_id']], {
                'change_reason': 'tearDownTest',
            })
            self.used_db.get(w_res['res_model']).do_cancel([w_res['res_id']], {
                'cancel_type': 'update_out',
                'active_ids': [self.in_id],
            })

        if self.po_id:
            po_state = self.po_obj.browse(self.po_id).state
            if po_state in ('cancel', 'done'):
                pass
            elif po_state == 'draft':
                self.po_obj.unlink(self.po_id)
            elif po_state == 'confirmed':
                self.po_obj.purchase_cancel(self.po_id)

        return

    def get_record(self, object_ref, module=None):
        """
        Override the get_record() method to avoid to give the db values.

        :param object_ref: XML ID of the record we are looking for
        :param module: Name of the module on which the record can be found
        :return: ID of the record
        """
        return super(TestPO0100, self).\
            get_record(self.used_db, object_ref, module)

    def create_po(self, o_categ='other', o_priority='normal',
                  p_type='external'):
        """
        Create a new PO from scratch with 4 lines

        :param o_categ: Order category
        :param o_priority: Order priority
        :param p_type: Partner type
        :return: ID of the new PO
        """
        if p_type == 'esc':
            partner_id = self.get_record('esc_supplier_1')
        else:
            partner_id = self.get_record('ext_supplier_1')

        order_data = {
            'partner_id': partner_id,
            'location_id': self.get_record('stock_location_stock', 'stock'),
            'categ': o_categ,
            'priority': o_priority,
        }
        order_data.update(
            self.po_obj.onchange_partner_id(
                None,
                partner_id,
                time.strftime('%Y-%m-%d'),
            ).get('value', {})
        )
        self.po_id = self.po_obj.create(order_data)

        po_brw = self.po_obj.browse(self.po_id)

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
            'product_id': self.get_record('prod_srv_1'),
            'product_uom': self.get_record('product_uom_unit', 'product'),
            'price_unit': 3.05,
            'product_qty': 150.00,
            'order_id': self.po_id,
        }
        self.pol_ids.append(
            self.pol_obj.create(line_data)
        )

        line_data = {
            'product_id': self.get_record('prod_srv_2'),
            'product_uom': self.get_record('product_uom_unit', 'product'),
            'price_unit': 4.18,
            'product_qty': 230.00,
            'order_id': self.po_id,
        }
        self.pol_ids.append(
            self.pol_obj.create(line_data)
        )

        line_data = {
            'product_id': self.get_record('prod_srv_3'),
            'product_uom': self.get_record('product_uom_unit', 'product'),
            'price_unit': 3.05,
            'product_qty': 150.00,
            'order_id': self.po_id,
        }
        self.pol_ids.append(
            self.pol_obj.create(line_data)
        )

        line_data = {
            'product_id': self.get_record('prod_srv_4'),
            'product_uom': self.get_record('product_uom_unit', 'product'),
            'price_unit': 18.00,
            'product_qty': 10.00,
            'order_id': self.po_id,
        }
        self.pol_ids.append(
            self.pol_obj.create(line_data)
        )

    def create_lines_from_scratch(self):
        """
        Add two lines on the PO. One with a MED product and the other
        with a LOG product.

        :return:
        """
        # New line with MED product
        line_data = {
            'product_id': self.get_record('prod_med_1'),
            'product_uom': self.get_record('product_uom_unit', 'product'),
            'price_unit': 3.05,
            'product_qty': 150.00,
            'order_id': self.po_id,
        }
        self.pol_ids.append(
            self.pol_obj.create(line_data)
        )

        # New line with LOG product
        line_data = {
            'product_id': self.get_record('prod_log_1'),
            'product_uom': self.get_record('product_uom_unit', 'product'),
            'price_unit': 3.05,
            'product_qty': 150.00,
            'order_id': self.po_id,
        }
        self.pol_ids.append(
            self.pol_obj.create(line_data)
        )

        self.assertEqual(
            len(self.po_obj.read(self.po_id, ['order_line'])['order_line']),
            2,
            "There aren't 2 PO lines on the PO."
        )

    def create_multiple_lines(self):
        """
        Add two lines on the PO with the add multiple lines wizard.

        :return:
        """
        impl_obj = self.used_db.get('wizard.common.import.line')
        nb_pol = len(self.po_obj.read(self.po_id, ['order_line'])['order_line'])

        wiz_res = self.po_obj.add_multiple_lines(self.po_id)
        self.assert_(
            wiz_res['res_model'] == 'wizard.common.import.line',
            "The 'Add multiple line' button on PO doesn't return the good view",
        )

        line_data = {
            'product_ids': [(6, 0, [
                    self.get_record('prod_med_2'),
                    self.get_record('prod_log_2'),
                ]),
            ]
        }
        impl_obj.write([wiz_res['res_id']], line_data)
        impl_obj.fill_lines(wiz_res['res_id'])

        self.assertEqual(
            len(self.po_obj.read(self.po_id, ['order_line'])['order_line']),
            nb_pol + 2,
            "There aren't 2 more line on the PO."
        )

        for pol in self.po_obj.browse(self.po_id).order_line:
            if pol.id not in self.pol_ids:
                self.assert_(
                    pol.product_qty == 0,
                    "The quantity of the new created line is not 0.00",
                )
                self.pol_ids.append(pol.id)
                self.pol_obj.write([pol.id], {'product_qty': 3.0*pol.id})

    def generate_test(self, cat, prio, part_type, sp=False):
        """
        1. Create a new PO with these attributes:
            * Order type: Regular
            * Order category: Other
            * Priority: Normal

        2. Create two lines from scratch
        3. Create two lines with the 'Add multiple lines' wizard
        4. Check the printed report
        5. Fill the analytic distribution
        6. Validate the PO
        7. Add a delivery confirmed date and confirm the PO
        8. Process the incoming shipment
        9. Check state of all documents

        :return:
        """
        self.create_po(
            o_categ=cat,
            o_priority=prio,
            p_type=part_type,
        )

        if sp:
            self.create_service_lines()
        else:
            self.create_lines_from_scratch()
            self.create_multiple_lines()

        # Try to print the PO report
        self.used_db.report(
            'msf.purchase.order',
            'purchase.order',
            self.po_id,
        )

        # Add an analytic distribution
        distrib_id = self.get_record('distrib_1')
        self.po_obj.write([self.po_id], {
            'analytic_distribution_id': distrib_id,
        })

        # Check Order impact vs. Budget printable doc.
        self.used_db.report(
            'msf.pdf.engagement',
            'purchase.order',
            self.po_id,
        )

        # Check allocation report
        self.used_db.report(
            'po.line.allocation.report',
            'purchase.order',
            self.po_id,
        )

        # Validate the PO
        po_state = self.po_obj.read(self.po_id, ['state'])['state']
        self.assert_(
            po_state == 'draft',
            msg="""The state of the generated PO is %s - Should be
'draft'""" % po_state,
        )
        self.used_db.exec_workflow(
            'purchase.order',
            'purchase_confirm',
            self.po_id,
        )
        po_state = self.po_obj.browse(self.po_id).state
        self.assert_(
            po_state == 'confirmed',
            msg="""The state of the generated PO is %s - Should be
'confirmed'""" % po_state,
        )

        # Set a delivery confirmed date
        self.po_obj.write([self.po_id], {
            'delivery_confirmed_date': time.strftime('%Y-%m-%d'),
        })

        # Confirm the PO
        po_state = self.po_obj.read(self.po_id, ['state'])['state']
        self.assert_(
            po_state == 'confirmed',
            msg="""The state of the generated PO is %s - Should be
'confirmed'""" % po_state,
        )
        self.po_obj.confirm_button([self.po_id])
        po_state = self.po_obj.read(self.po_id, ['state'])['state']
        self.assert_(
            po_state == 'approved',
            msg="""The state of the geerated Po is %s - Should be
'approved'""" % po_state,
        )

        # Get the Incoming shipment
        in_ids = self.pick_obj.search([
            ('type', '=', 'in'),
            ('purchase_id', '=', self.po_id),
        ])
        self.assert_(
            len(in_ids) == 1,
            msg="""There are %s Incoming shipment for the PO -
Should be 1""" % len(in_ids),
        )
        self.in_id = in_ids[0]

        moves = self.pick_obj.read(self.in_id, ['move_lines'])['move_lines']
        self.assert_(
            len(moves) == 4,
            msg="""There are %s moves in the Incoming shipment -
Should be 4""" % len(moves),
        )

        in_state = self.pick_obj.read(self.in_id, ['state'])['state']
        self.assert_(
            in_state == 'assigned',
            msg="""The state of the incoming sihpment is '%s' - Should
be 'assigned'""" % in_state,
        )

        # Process the incoming shipment
        in_proc_id = self.pick_obj.action_process(self.in_id)['res_id']
        self.in_proc_obj.copy_all(in_proc_id)
        wiz_res = self.in_proc_obj.do_incoming_shipment([in_proc_id])

        in_state = self.pick_obj.read(self.in_id, ['state'])['state']
        stop = 0
        while in_state != 'done' and stop < 10:
            stop += 1
            time.sleep(3)
            in_state = self.pick_obj.read(self.in_id, ['state'])['state']

        self.assert_(
            stop <= 10,
            msg="""The incoming shipment is not done""",
        )

        po_state = self.po_obj.read(self.po_id, ['state'])['state']
        self.assert_(
            po_state == 'done',
            msg="""The PO state is '%s' - Should be 'done'""" % po_state,
        )

    def test_po_0101_esc_normal_other(self):
        """
        PO with these parameters:
          * Partner type: ESC
          * Order priority: Normale
          * Order category: Other

        :return:
        """
        self.generate_test('other', 'normal', 'esc')

    def test_po_0102_esc_priority_other(self):
        """
        PO with these parameters:
          * Partner type: ESC
          * Order priority: Priority
          * Order category: Other

        :return:
        """
        self.generate_test('other', 'priority', 'esc')

    def test_po_0103_esc_emergency_other(self):
        """
        PO with these parameters:
          * Partner type: ESC
          * Order priority: Emergency
          * Order category: Other

        :return:
        """
        self.generate_test('other', 'emergency', 'esc')

    def test_po_0104_esc_normal_log(self):
        """
        PO with these parameters:
          * Partner type: ESC
          * Order priority: Normale
          * Order category: Log

        :return:
        """
        self.generate_test('log', 'normal', 'esc')

    def test_po_0105_esc_priority_log(self):
        """
        PO with these parameters:
          * Partner type: ESC
          * Order priority: Priority
          * Order category: Log

        :return:
        """
        self.generate_test('log', 'priority', 'esc')

    def test_po_0106_esc_emergency_log(self):
        """
        PO with these parameters:
          * Partner type: ESC
          * Order priority: Emergency
          * Order category: Log

        :return:
        """
        self.generate_test('log', 'emergency', 'esc')

    def test_po_0107_esc_normal_medical(self):
        """
        PO with these parameters:
          * Partner type: ESC
          * Order priority: Normale
          * Order category: Medical

        :return:
        """
        self.generate_test('medical', 'normal', 'esc')

    def test_po_0108_esc_priority_medical(self):
        """
        PO with these parameters:
          * Partner type: ESC
          * Order priority: Priority
          * Order category: Medical

        :return:
        """
        self.generate_test('medical', 'priority', 'esc')

    def test_po_0109_esc_emergency_medical(self):
        """
        PO with these parameters:
          * Partner type: ESC
          * Order priority: Emergency
          * Order category: Medical

        :return:
        """
        self.generate_test('medical', 'emergency', 'esc')

    def test_po_0110_external_normal_other(self):
        """
        PO with these parameters:
          * Partner type: External
          * Order priority: Normale
          * Order category: Other

        :return:
        """
        self.generate_test('other', 'normal', 'external')

    def test_po_0111_external_priority_other(self):
        """
        PO with these parameters:
          * Partner type: External
          * Order priority: Priority
          * Order category: Other

        :return:
        """
        self.generate_test('other', 'priority', 'external')

    def test_po_0112_external_emergency_other(self):
        """
        PO with these parameters:
          * Partner type: External
          * Order priority: Emergency
          * Order category: Other

        :return:
        """
        self.generate_test('other', 'emergency', 'external')

    def test_po_0113_external_normal_log(self):
        """
        PO with these parameters:
          * Partner type: External
          * Order priority: Normale
          * Order category: Log

        :return:
        """
        self.generate_test('log', 'normal', 'external')

    def test_po_0114_external_priority_log(self):
        """
        PO with these parameters:
          * Partner type: External
          * Order priority: Priority
          * Order category: Log

        :return:
        """
        self.generate_test('log', 'priority', 'external')

    def test_po_0115_external_emergency_log(self):
        """
        PO with these parameters:
          * Partner type: External
          * Order priority: Emergency
          * Order category: Log

        :return:
        """
        self.generate_test('log', 'emergency', 'external')

    def test_po_0116_external_normal_medical(self):
        """
        PO with these parameters:
          * Partner type: External
          * Order priority: Normale
          * Order category: Medical

        :return:
        """
        self.generate_test('medical', 'normal', 'external')

    def test_po_0117_external_priority_medical(self):
        """
        PO with these parameters:
          * Partner type: External
          * Order priority: Priority
          * Order category: Medical

        :return:
        """
        self.generate_test('medical', 'priority', 'external')

    def test_po_0118_external_emergency_medical(self):
        """
        PO with these parameters:
          * Partner type: External
          * Order priority: Emergency
          * Order category: Medical

        :return:
        """
        self.generate_test('medical', 'emergency', 'external')

    def test_po_0300_external_service(self):
        """
        PO with these parameters:
          * Partner type: External
          * Order priority: Emergency
          * Order category: Service

        With only service products
        :return:
        """
        self.generate_test('service', 'emergency', 'external', sp=True)

    def test_po_0301_esc_service(self):
        """
        PO with these parameters:
          * Partner type: ESC
          * Order priority: Emergency
          * Order category: Service

        With only service products
        :return:
        """
        self.generate_test('service', 'emergency', 'esc', sp=True)


def get_test_class():
    return TestPO0100

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: