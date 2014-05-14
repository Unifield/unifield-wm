#!/usr/bin/env python

import os
import sys
import functools
from itertools import chain
import string
import random
import pprint
import unittest2
import xmlrpclib
import datetime


def random_name(n=8):
    return ''.join(random.choice(string.ascii_uppercase + string.digits)
                   for _ in range(n))


def now():
    return datetime.datetime.now().strftime("%Y-%m-%d")


def catch_xmlrpc_errors(func):
    @functools.wraps(func)
    def wrapper(self, *a, **kw):
        try:
            return func(self, *a, **kw)
        except xmlrpclib.Fault, exc:
            # TODO retrieve the original stack
            if 'Traceback' in exc.faultString:
                _, _, traceback = sys.exc_info()
                raise Exception("XML-RPC call failed!\n" +
                        exc.faultString + "\nXML-RPC call failed!"), \
                    None, traceback
            raise
    return wrapper


class SynchronizePOfromCPtoRW(unittest2.TestCase):
    cp  = os.environ.get('DB_CP', "pilot3.0b6-P_2_1")
    rw  = os.environ.get('DB_RW', "pilot3.0b6-P_2_1_RW")
    url = os.environ.get('DB_URL', "http://localhost:8069/xmlrpc")
    debug = bool(os.environ.get('DEBUG', ''))

    def _execute(self, *args):
        return self.proxy.execute(*args)

    def _exec_workflow(self, *args):
        return self.proxy.exec_workflow(*args)

    def setUp(self):
        self.proxy = xmlrpclib.ServerProxy(self.url + '/object')

    def tearDown(self):
        if self.debug:
            print
            pprint.pprint(self.__dict__)

    @catch_xmlrpc_errors
    def test_10_cp_to_rw(self):
        # Check name of CP and RW entities
        cp_entity_id = self._execute(
            self.cp, 1, 'admin', 'sync.client.entity', 'search', []).pop()
        self.cp_name = self._execute(self.cp, 1, 'admin', 'sync.client.entity',
            'read', cp_entity_id, ['name'])['name']
        rw_entity_id = self._execute(
            self.rw, 1, 'admin', 'sync.client.entity', 'search', []).pop()
        self.rw_name = self._execute(self.rw, 1, 'admin', 'sync.client.entity',
            'read', rw_entity_id, ['name'])['name']
        self.assertEqual(self.cp_name, self.rw_name)
        # Purchase order creation
        self.template_po = {
            'name': random_name(),
            'partner_id': self._execute(self.cp, 1, 'admin',
                'res.partner', 'search',
                [])[0],
            'partner_address_id': self._execute(self.cp, 1, 'admin',
                'res.partner.address', 'search', [])[0],
            'location_id': self._execute(self.cp, 1, 'admin',
                'stock.location', 'search', [])[0],
            'pricelist_id': self._execute(self.cp, 1, 'admin',
                'product.pricelist', 'search', [])[0],
            'delivery_confirmed_date': now(),
            #'order_type': 'loan',
        }
        self.po_id = self._execute(
            self.cp, 1, 'admin', 'purchase.order', 'create', self.template_po)
        self.po_sdref = self._execute(
            self.cp, 1, 'admin', 'purchase.order', 'get_sd_ref', self.po_id)
        self.assertTrue(self.po_sdref)
        # Line creation
        self.template_line = {
            # TODO
            #   changing name is not allowed in the create() method, so we have
            #   to check if it is possible in write() and handle this second
            #   write() in RW
            'order_id': self.po_id,
            # we need to link to a stockable product in order to trigger the
            # creation of an IN shipment (stock.picking)
            'product_id': self._execute(self.cp, 1, 'admin',
                'product.product', 'search',
                [('product_tmpl_id.type', 'in', ['product', 'consu'])])[0],
            # defaults to avoid exceptions
            'product_qty': 1,
            'product_uom': self._execute(self.cp, 1, 'admin',
                'product.uom', 'search', [])[0],
            'price_unit': 10,
        }
        self.line_id = self._execute(
            self.cp, 1, 'admin', 'purchase.order.line',
            'create', self.template_line)
        self.line = self._execute(self.cp, 1, 'admin', 'purchase.order.line',
            'read', self.line_id, ['name'])
        # Make analytic distribution
        self.distribution_template = {
            'purchase_line_ids': [(4, self.line_id)],
        }
        self.distribution_id = self._execute(self.cp, 1, 'admin',
            'analytic.distribution', 'create', self.distribution_template)
        self.distribution = self._execute(self.cp, 1, 'admin',
            'analytic.distribution', 'read', self.distribution_id, ['name'])
        # Make CC line
        self.cc_line_template = {
            'distribution_id': self.distribution_id,
            'percentage': 42,
            'currency_id': self._execute(self.cp, 1, 'admin', 'res.currency',
                'search', [])[0],
            'destination_id': self._execute(self.cp, 1, 'admin',
                'account.analytic.account', 'search', [])[0],
        }
        self.cc_line_id = self._execute(self.cp, 1, 'admin',
            'cost.center.distribution.line', 'create', self.cc_line_template)
        self.cc_line = self._execute(self.cp, 1, 'admin',
            'cost.center.distribution.line', 'read', self.cc_line_id,
                ['percentage'])
        # Confirm purchase order
        self._exec_workflow(self.cp, 1, 'admin', 'purchase.order',
            'purchase_confirm', self.po_id)
        # Approve the purchase order (the real functional "Confirm")
        self._exec_workflow(self.cp, 1, 'admin', 'purchase.order',
            'purchase_approve', self.po_id)
        # Check the status after the workflow
        self.po = self._execute(self.cp, 1, 'admin', 'purchase.order',
            'read', self.po_id, ['name', 'state', 'order_line'])
        self.assertEqual(self.po['order_line'], [self.line_id])
        self.assertEqual(self.po['state'], 'approved')
        # Find IN shipment (stock.picking)
        in_ids = self._execute(self.cp, 1, 'admin', 'stock.picking',
            'search', [('purchase_id', '=', self.po_id)])
        self.assertEqual(len(in_ids), 1)
        self.in_id = in_ids.pop()
        self.In = self._execute(self.cp, 1, 'admin', 'stock.picking',
            'read', self.in_id, ['name'])
        # Find stock.move linked to pickings
        move_ids = self._execute(self.cp, 1, 'admin', 'stock.move',
            'search', [('picking_id', '=', self.in_id)])
        self.assertEqual(len(move_ids), 1)
        self.move_id = move_ids.pop()
        self.move = self._execute(self.cp, 1, 'admin', 'stock.move',
            'read', self.move_id, ['name'])
        # Rule creation
        self.export_fields = (
            ['id', 'name', 'partner_id/id', 'partner_address_id/id',
             'location_id/id', 'pricelist_id/id', 'order_type',
             'delivery_confirmed_date'] +
            ['order_line/' + f
             for f in ['id', 'name', 'product_id/id', 'product_qty',
                       'product_uom/id', 'price_unit']] +
            ['picking_ids/' + f
             for f in ['id', 'name']] +
            ['picking_ids/move_lines/' + f
             for f in ['id', 'name', 'state', 'product_uom/id',
                       'company_id/id', 'location_dest_id/id',
                       'location_id/id', 'product_id/id',
                       'reason_type_id/id']] +
            ['order_line/analytic_distribution_id/' + f
             for f in ['id', 'name']] +
            ['order_line/analytic_distribution_id/cost_center_lines/' + f
             for f in ['id', 'percentage', 'currency_id/id',
                       'destination_id/id']]
        )
        self.rule = {
            'direction_usb': 'cp_to_rw',
            'model': 'purchase.order',
            'domain': str([('state','=','approved')]),
            'remote_call' :
                'purchase.order.replicate_approved_po_from_cp_on_rw',
            'arguments': str(self.export_fields),
            # Non-sense field required otherwise create_from_rule fail
            'destination_name': 'name',
            # Required to to determine the message identifier
            'server_id': 1,
        }
        # Check domain is valid
        self.assertIn(
            self.po_id,
            self._execute(self.cp, 1, 'admin', 'purchase.order', 'search',
                eval(self.rule['domain'])))
        self.rule_id = self._execute(
            self.cp, 1, 'admin', 'sync.client.message_rule',
            'create', self.rule)
        # Create the messages
        self.assertGreater(self._execute(
            self.cp, 1, 'admin', 'sync_remote_warehouse.message_to_send',
            'create_from_rule', self.rule_id), 0)
        # Check that the message has been created
        self.message_identifier = \
            "%s_%s" % (self.po_sdref, self.rule['server_id'])
        message_ids = self._execute(
            self.cp, 1, 'admin', 'sync_remote_warehouse.message_to_send',
            'search', [('identifier', '=', self.message_identifier)])
        # Mark the message has sent to avoid conflict with regular
        # synchronization
        self._execute(
            self.cp, 1, 'admin', 'sync_remote_warehouse.message_to_send',
            'write', message_ids, {'sent': True})
        self.assertEqual(len(message_ids), 1)
        self.message_id = message_ids.pop()
        # Fetch the message
        self.message = self._execute(
            self.cp, 1, 'admin', 'sync_remote_warehouse.message_to_send',
            'read', self.message_id, ['identifier', 'remote_call',
                                      'arguments'])
        # Transfer message to rw instance
        self.rw_message_id = self._execute(
            self.rw, 1, 'admin', 'sync_remote_warehouse.message_received',
            'create', dict(self.message, source=self.cp_name))
        # Execute message in rw instance
        self.assertEqual(self._execute(
            self.rw, 1, 'admin', 'sync_remote_warehouse.message_received',
            'execute', [self.rw_message_id]), 1)
        self.rw_message = self._execute(
            self.rw, 1, 'admin', 'sync_remote_warehouse.message_received',
            'read', self.rw_message_id, ['identifier', 'remote_call', 'source',
                                         'arguments', 'run', 'log'])
        # Consistency & execution checks
        self.assertDictContainsSubset(
            dict(self.message, id='***'), dict(self.rw_message, id='***'))
        self.assertTrue(self.rw_message['run'],
            "Message not run because of the following reason:\n" +
            self.rw_message['log'])
        # compare export result
        datas = self._execute(self.cp, 1, 'admin', 'purchase.order',
            'export_data_json', [self.po_id], self.export_fields)['datas']
        self.assertTrue(datas, "could not export row")
        self.export = datas.pop()
        rw_po_ids = self._execute(self.rw, 1, 'admin', 'purchase.order',
            'search', [('name', '=', self.po['name'])])
        self.assertEqual(len(rw_po_ids), 1)
        self.rw_po_id = rw_po_ids.pop()
        rw_datas = self._execute(self.rw, 1, 'admin', 'purchase.order',
            'export_data_json', [self.rw_po_id], self.export_fields)['datas']
        self.assertTrue(rw_datas, "could not export row")
        self.rw_export = rw_datas.pop()
        self.assertDictContainsSubset(self.export, self.rw_export)

if __name__ == '__main__':
    unittest2.main(failfast=True, verbosity=2)
