#!/usr/bin/env python
#-*- encoding:utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution    
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    Tempo Consulting (<http://www.tempo-consulting.fr/>).
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

from report import report_sxw
from osv import osv
import time
import locale

class entree_article(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(entree_article, self).__init__(cr, uid, name, context)
        self.localcontext.update({
            'getInvoices': self.get_invoices,
            'getType': self.get_type,
            'getTotalQty': self.get_total_qty,
            'getTotalGen': self.get_total_general,
            'time': time,
            'locale': locale,
        })

    def get_invoices(self, invoice_ids):
        invoice_obj = self.pool.get('account.invoice')
        invoices = invoice_obj.browse(self.cr, self.uid, invoice_ids)

        return invoices

    def get_type(self, invoice_type):
        if invoice_type in ('out_invoice', 'in_invoice'):
            return 'FA'
        else:
            return 'AV'

    def get_total_qty(self, invoice_id):
        tot_qty = 0.00
        for line in invoice_id.invoice_line:
            tot_qty += line.quantity

        return tot_qty

    def get_total_general(self, invoice_ids):
        invoice_obj = self.pool.get('account.invoice')

        qty_gen = 0.00
        val_gen = 0.00

        for inv in invoice_obj.browse(self.cr, self.uid, invoice_ids):
            val_gen += inv.amount_untaxed
            for line in inv.invoice_line:
                qty_gen += line.quantity

        return qty_gen, val_gen

report_sxw.report_sxw('report.report.entree.article', 'stats.entree.article', 'addons/iller_stats/report/entree_article.rml', parser=entree_article)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
