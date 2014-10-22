#!/usr/bin/env python
# -*- coding: utf8 -*-

__author__ = 'qt'

from resourcing import ResourcingTest

import time


class UFTP344Test(ResourcingTest):

    def setUp(self):
        """
        Create a PO at Project side to Coordo with
        two lines.
        :return:
        """
        super(UFTP344Test, self).setUp()

        self.pr = True

        self.synchronize(self.c1)
        self.synchronize(self.p1)

        # C1
        self.c_so_obj = self.c1.get('sale.order')
        self.c_sol_obj = self.c1.get('sale.order.line')
        self.c_po_obj = self.c1.get('purchase.order')
        self.c_pol_obj = self.c1.get('purchase.order.line')
        self.c_partner_obj = self.c1.get('res.partner')
        self.c_lc_obj = self.c1.get('sale.order.leave.close')
        self.c_so_cancel_obj = self.c1.get('sale.order.cancelation.wizard')
        self.c_pick_obj = self.c1.get('stock.picking')
        self.c_move_obj = self.c1.get('stock.move')
        self.c_in_proc_obj = self.c1.get('stock.incoming.processor')
        self.c_in_move_obj = self.c1.get('stock.move.in.processor')

        # P1
        self.p_so_obj = self.p1.get('sale.order')
        self.p_sol_obj = self.p1.get('sale.order.line')
        self.p_po_obj = self.p1.get('purchase.order')
        self.p_pol_obj = self.p1.get('purchase.order.line')
        self.p_partner_obj = self.p1.get('res.partner')
        self.p_lc_obj = self.p1.get('sale.order.leave.close')
        self.p_so_cancel_obj = self.p1.get('sale.order.cancelation.wizard')
        self.p_pick_obj = self.p1.get('stock.picking')

        # Prepare values for the field order
        prod_log1_id = self.get_record(self.p1, 'prod_log_1')
        prod_log2_id = self.get_record(self.p1, 'prod_log_2')
        prod_log3_id = self.get_record(self.p1, 'prod_log_2')
        prod_log4_id = self.get_record(self.p1, 'prod_log_2')
        uom_pce_id = self.get_record(self.p1, 'product_uom_unit', module='product')
        stock_id = self.get_record(self.p1, 'stock_location_stock', module='stock')

        p_partner_name = self.get_db_partner_name(self.p1)
        self.p_partner_ids = self.c_partner_obj.search([('name', '=', p_partner_name)])
        self.assert_(
            self.p_partner_ids,
            "No partner found for %s" % self.p1.db_name,
        )

        c_partner_name = self.get_db_partner_name(self.c1)
        self.c_partner_ids = self.p_partner_obj.search([('name', '=', c_partner_name)])
        self.assert_(
            self.c_partner_ids,
            "No partner found for %s" % self.c1.db_name,
        )

        self.p_so_id, self.p_sol_ids, self.p_po_ids, self.p_pol_ids = self.order_source_all_one_po(self.p1, self.c_partner_ids[0])

        self.p_po_id = self.p_po_ids and list(self.p_po_ids)[0] or False
        self.p_po_name = self.p_po_obj.read(self.p_po_id, ['name'])['name']

        # Validate PO
        self._validate_po(self.p1, [self.p_po_id])

        self.synchronize(self.p1)
        self.synchronize(self.c1)
        self.synchronize(self.p1)
        self.synchronize(self.c1)

        self.c_so_id = None
        c_so_ids = self.c_so_obj.search([('client_order_ref', 'like', self.p_po_name)])
        for c_so_id in c_so_ids:
            self.assert_(
                self.c_so_obj.read(c_so_id, ['state'])['state'] == 'draft',
                "The FO at Coordo is not 'Draft'.",
            )
            self.c_so_id = c_so_id

        # Validate the Field Order
        self.c1.exec_workflow('sale.order', 'order_validated', self.c_so_id)

        # Source the FO at coordo side to an external partner
        partner_id = self.get_record(self.c1, 'ext_supplier_1')
        line_ids = self.c_sol_obj.search([('order_id', '=', self.c_so_id)])
        self.c_sol_obj.write(line_ids, {
            'type': 'make_to_order',
            'po_cft': 'po',
            'supplier': partner_id,
        })
        self.c_sol_obj.confirmLine(line_ids)

        # Run scheduler
        new_order_id = self.run_auto_pos_creation(self.c1, order_to_check=self.c_so_id)
        self.assert_(
            new_order_id,
            "No new order created at coordo side.",
        )
        self.c_so_id = new_order_id

        line_ids = self.c_sol_obj.search([('order_id', '=', new_order_id)])
        not_sourced = True
        while not_sourced:
            not_sourced = False
            for line in self.c_sol_obj.browse(line_ids):
                if line.procurement_id and line.procurement_id.state != 'running':
                    not_sourced = True
                if not_sourced:
                    time.sleep(1)

        # Get the PO at coordo side.
        po_line_ids = []
        for line in self.c_sol_obj.browse(line_ids):
            if line.procurement_id:
                po_line_ids.extend(self.c_pol_obj.search([
                    ('procurement_id', '=', line.procurement_id.id),
                ]))

        for po_line in self.c_pol_obj.read(po_line_ids, ['order_id']):
            self.c_po_id = po_line['order_id'][0]

    def test_receive_and_cancel_pick(self):
        """
        Receive the IN in two times, then cancel the available PICK and
        ship all available quantities in draft picking.
        """
        # Validate and confirm the PO
        self._validate_po(self.c1, [self.c_po_id])
        self._confirm_po(self.c1, [self.c_po_id])

        # Get the IN from the PO
        in_ids = self.c_pick_obj.search([('purchase_id', '=', self.c_po_id)])

        # Process partially the IN
        proc_res = self.c_pick_obj.action_process(in_ids[0])
        self.assert_(
            proc_res['res_model'] == 'stock.incoming.processor' and proc_res['res_id'],
            "The wizard to process the incoming shipment is not displayed well",
        )

        in_move_ids = self.c_in_move_obj.search([('wizard_id', '=', proc_res['res_id'])])
        self.c_in_move_obj.write([in_move_ids[0]], {'quantity': 5.0})
        wiz_res = self.c_in_proc_obj.do_incoming_shipment([proc_res['res_id']])

        # Get picking ticket
        pick_ids = self.c_pick_obj.search([('sale_id', '=', self.c_so_id), ('state', '=', 'assigned')])
        self.assert_(
            len(pick_ids) == 1,
            "The number of available picking ticket is %s - Should be 1" % len(pick_ids),
        )
        for pt in self.c_pick_obj.browse(pick_ids):
            self.c1.exec_workflow('stock.picking', 'button_cancel', pt.id)

        # Pick/Pack/Ship the available quantities
        pick_ids = self.c_pick_obj.search([('sale_id', '=', self.c_so_id), ('state', '=', 'draft')])
        self.assert_(
            pick_ids,
            "No Draft picking ticket found",
        )
        # PICK
        p_res = self.c_pick_obj.create_picking([pick_ids[0]])
        self.assert_(
            p_res['res_id'] and p_res['res_model'] == 'create.picking.processor',
            "No wizard to process picking ticket",
        )
        self.c1.get('create.picking.processor').copy_all(p_res['res_id'])
        vpt_res = self.c1.execute('create.picking.processor', 'do_create_picking', p_res['res_id'])
        self.assert_(
            vpt_res['res_id'] and vpt_res['res_model'] == 'stock.picking',
            "No Available picking ticket displayed",
        )
        vpt_wiz = self.c_pick_obj.validate_picking([vpt_res['res_id']])
        self.assert_(
            vpt_wiz['res_id'] and vpt_wiz['res_model'] == 'validate.picking.processor',
            "No wizard displayed for processing teh picking ticket",
        )
        self.c1.get('validate.picking.processor').copy_all(vpt_wiz['res_id'])
        ppl_res = self.c1.get('validate.picking.processor').do_validate_picking([vpt_wiz['res_id']])

        # PACK
        self.assert_(
            ppl_res['res_id'] and ppl_res['res_model'] == 'stock.picking',
            "No PPL displayed",
        )
        ppl_wiz1 = self.c_pick_obj.ppl([ppl_res['res_id']])
        self.assert_(
            ppl_wiz1['res_id'] and ppl_wiz1['res_model'] == 'ppl.processor',
            "No PPL processor (step 1) displayed",
        )
        self.c1.get('ppl.processor').do_ppl_step1([ppl_wiz1['res_id']])
        # Update family's weigth
        fam_ids = self.c1.get('ppl.family.processor').search([('wizard_id', '=', ppl_wiz1['res_id'])])
        self.c1.get('ppl.family.processor').write(fam_ids, {'weight': 1.00})
        ship_res = self.c1.get('ppl.processor').do_ppl_step2([ppl_wiz1['res_id']])

        # SHIP
        self.assert_(
            ship_res['res_id'] and ship_res['res_model'] == 'shipment',
            "No shipment displayed",
        )
        ship_wiz = self.c1.get('shipment').create_shipment([ship_res['res_id']])
        self.assert_(
            ship_wiz['res_id'] and ship_wiz['res_model'] == 'shipment.processor',
            "No shipment processor displayed",
        )
        ship2_res = self.c1.get('shipment.processor').do_create_shipment([ship_wiz['res_id']])
        self.assert_(
            ship2_res['res_id'] and ship2_res['res_model'] == 'shipment',
            "No shipped shipment displayed",
        )
        self.c1.get('shipment').validate([ship2_res['res_id']])

        # Synchronize
        self.synchronize(self.c1)
        self.synchronize(self.p1)

        # Check state of IN at Project side
        p_po_ids = self.p_po_obj.search([('name', '!=', self.p_po_name), ('name', 'like', self.p_po_name)])
        self.assert_(
            len(p_po_ids) == 1,
            "The PO at project side has been split",
        )
        self.p_po_id = p_po_ids[0]
        in_ids = self.p_pick_obj.search([('purchase_id', '=', self.p_po_id), ('type', '=', 'in')])
        shipped_ok = False
        wait_ok = False
        self.assert_(
            len(in_ids) == 2,
            "There is %s IN - Should be 2" % len(in_ids),
        )
        for in_obj in self.p_pick_obj.browse(in_ids):
            if in_obj.state == 'shipped':
                shipped_ok = True
            elif in_obj.state == 'assigned':
                wait_ok = True

        self.assert_(
            shipped_ok and wait_ok,
            "There is no one IN shipped and one IN available at Project side",
        )


def get_test_class():
    return UFTP344Test
