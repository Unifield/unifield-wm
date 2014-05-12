#!/usr/bin/env python

import os
import sys
import functools
import string
import random
import pprint
import unittest2
import xmlrpclib
import datetime


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

    def setUp(self):
        self.proxy = xmlrpclib.ServerProxy(self.url + '/object')

    def tearDown(self):
        if self.debug:
            print
            pprint.pprint(self.__dict__)

    @catch_xmlrpc_errors
    def test_10_import_business_object(self):
        # what we're going to export/import
        self.po_cols = ['id', 'order_line', 'name', 'partner_address_id',
                        'location_id', 'partner_id', 'pricelist_id']
        self.line_cols = ['id', 'analytic_distribution_id', 'name',
                          'product_id/id', 'product_qty', 'product_uom/id',
                          'price_unit']
        self.distribution_cols = ['id', 'cost_center_lines', 'name']
        self.cc_cols = ['id', 'percentage']
        # generate export_fields
        self.export_fields = ['id', 'name', 'partner_address_id/id',
                              'location_id/id', 'partner_id/id',
                              'pricelist_id/id']
        for col in ('id', 'name', 'product_id/id', 'product_qty',
                    'product_uom/id', 'price_unit'):
            self.export_fields.append('order_line/' + col)
        for col in ('id', 'name'):
            self.export_fields.append(
                'order_line/analytic_distribution_id/' + col)
        for col in ('id', 'percentage'):
            self.export_fields.append(
                'order_line/analytic_distribution_id/cost_center_lines/' + col)
        # find a suitable PO in CP
        po_ids = self._execute(self.cp, 1, 'admin', 'purchase.order', 'search',
            [('order_line.analytic_distribution_id.id','!=',False)])
        self.assertTrue(po_ids, "can not find a suitable purchase.order")
        self.po_id = po_ids.pop()
        self.po_sdref = self._execute(self.cp, 1, 'admin', 'purchase.order',
            'get_sd_ref', self.po_id)
        # purge rw from this PO
        self.rw_po_id = self._execute(self.rw, 1, 'admin', 'purchase.order',
            'find_sd_ref', self.po_sdref)
        # make sure the record actually exists
        if self.rw_po_id:
            if not self._execute(self.rw, 1, 'admin', 'purchase.order',
                    'search', [('id', '=', self.rw_po_id)]):
                self.rw_po_id = False
        if self.rw_po_id:
            self._execute(self.rw, 1, 'admin',
                'purchase.order', 'write', self.rw_po_id, {'state': 'draft'})
            rw_in_ids = self._execute(self.rw, 1, 'admin', 'stock.picking',
                'search', [('purchase_id', '=', self.rw_po_id)])
            if rw_in_ids:
                self._execute(self.rw, 1, 'admin',
                    'stock.picking', 'write', rw_in_ids, {'state': 'draft'})
                self._execute(self.rw, 1, 'admin', 'stock.picking',
                    'unlink', rw_in_ids)
            self._execute(self.rw, 1, 'admin',
                'purchase.order', 'unlink', self.rw_po_id)
        # gather data from cp
        self.po = self._execute(self.cp, 1, 'admin', 'purchase.order', 'read',
            self.po_id, self.po_cols)
        self.line_id = self.po.pop('order_line')[0]
        self.line = self._execute(self.cp, 1, 'admin', 'purchase.order.line',
            'read', self.line_id, self.line_cols)
        self.distribution_id = self.line['analytic_distribution_id'][0]
        self.distribution = self._execute(self.cp, 1, 'admin',
            'analytic.distribution', 'read', self.distribution_id,
            self.distribution_cols)
        self.cc_line_id = self.distribution['cost_center_lines'][0]
        self.cc_line = self._execute(self.cp, 1, 'admin',
            'cost.center.distribution.line', 'read', self.cc_line_id,
            self.cc_cols)
        # export datas
        datas = self._execute(self.cp, 1, 'admin', 'purchase.order',
            'export_data_json', [self.po_id], self.export_fields)['datas']
        self.assertTrue(datas, "could not export row")
        self.export = datas.pop()
        # import from rw
        self._execute(self.rw, 1, 'admin', 'purchase.order',
            'import_data_json', [self.export])
        # find imported PO in rw
        self.rw_po_id = self._execute(self.rw, 1, 'admin', 'purchase.order',
            'find_sd_ref', self.po_sdref)
        # gather data from rw
        self.rw_po = self._execute(self.rw, 1, 'admin',
            'purchase.order', 'read', self.rw_po_id, self.po_cols)
        self.assertTrue(self.rw_po)
        self.rw_line_id = self.rw_po.pop('order_line')[0]
        self.rw_line = self._execute(self.rw, 1, 'admin',
            'purchase.order.line', 'read', self.rw_line_id, self.line_cols)
        self.rw_distribution_id = self.rw_line['analytic_distribution_id'][0]
        self.rw_distribution = self._execute(self.rw, 1, 'admin',
            'analytic.distribution', 'read', self.rw_distribution_id,
            self.distribution_cols)
        self.rw_cc_line_id = self.rw_distribution['cost_center_lines'][0]
        self.rw_cc_line = self._execute(self.rw, 1, 'admin',
            'cost.center.distribution.line', 'read', self.rw_cc_line_id,
            self.cc_cols)
        # check consistency in rw
        self.assertDictContainsSubset(
            dict(self.po, id='*'), dict(self.rw_po, id='*'))
        self.assertDictContainsSubset(
            dict(self.line, id='*'), dict(self.rw_line, id='*'))
        self.assertDictContainsSubset(dict(self.distribution, id='*'),
            dict(self.rw_distribution, id='*'))
        self.assertDictContainsSubset(
            dict(self.cc_line, id='*'), dict(self.rw_cc_line, id='*'))
        # compare export result
        rw_datas = self._execute(self.rw, 1, 'admin', 'purchase.order',
            'export_data_json', [self.rw_po_id], self.export_fields)['datas']
        self.assertTrue(rw_datas, "could not export row")
        self.rw_export = rw_datas.pop()
        self.assertDictContainsSubset(self.export, self.rw_export)

if __name__ == '__main__':
    unittest2.main(failfast=True, verbosity=2)
