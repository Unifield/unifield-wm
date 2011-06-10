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

from datetime import date, datetime, timedelta

class ca_client_periode(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(ca_client_periode, self).__init__(cr, uid, name, context)
        self.localcontext.update({
            'getPartners': self.get_partners,
            'getInfos': self.get_info_one,
            'getInfos2': self.get_info_two,
            'getInfos3': self.get_info_three,
            'time': time,
            'locale': locale,
        })

    def get_partners(self, partner_ids):
        return self.pool.get('res.partner').browse(self.cr, self.uid, partner_ids[:10])

    def get_info(self, partner_id, date_debut, date_fin, month):
        partner_obj = self.pool.get('res.partner')
        invoice_obj = self.pool.get('account.invoice')

        invoice_ids = []
        start_date = date_debut.strftime('%Y-%m-%d')
        end_date = date_fin.strftime('%y-%m-%d')

        qty = 0.00
        val = 0.00

        if month == 0:
            invoice_domain = [('date_invoice', '>=', date_debut.strftime('%Y-%m-%d')),
                              ('date_invoice', '<=', date_fin.strftime('%Y-%m-%d'))]
        else:
            if month < date_debut.month and month < date_fin.month:
                start_date = date(date_fin.year, month, 1)
                end_date = (date(month==12 and date_fin.year+1 or date_fin.year, month==12 and 1 or month+1, 1)-timedelta(days=1))
            elif month > date_debut.month and month > date_fin.month:
                start_date = date(date_debut.year, month, 1)
                end_date = (date(month==12 and date_debut.year+1 or date_debut.year, month==12 and 1 or month+1, 1)-timedelta(days=1))
            elif month == date_debut.month:
                start_date = date_debut
                end_date = (date(month==12 and date_debut.year+1 or date_debut.year, month==12 and 1 or month+1, 1)-timedelta(days=1))
            elif month == date_fin.month:
                start_date = date(date_fin.year, month, 1)
                end_date = date_fin
            elif month < date_debut.month and month > date_fin.month:
                return {'qte': '', 'caa': ''}

            invoice_domain = [('date_invoice', '>=', start_date.strftime('%Y-%m-%d')),
                              ('date_invoice', '<=', end_date.strftime('%Y-%m-%d'))]


        if isinstance(partner_id, type([])):
            invoice_domain.extend([('partner_id', 'in', partner_id)])
        else:
            invoice_domain.extend([('partner_id', '=', partner_id)])

        invoice_ids = invoice_obj.search(self.cr, self.uid, invoice_domain)

        for invoice in invoice_obj.browse(self.cr, self.uid, invoice_ids):
            for line in invoice.invoice_line:
                qty += line.quantity
                val += line.price_subtotal

        return {'qte': qty != 0.00 and qty or '', 'caa': val != 0.00 and val or ''}

    def get_info_one(self, partner_id, dates, month):
        depart = datetime.strptime(dates.date_depart_per1, '%Y-%m-%d')
        fin = datetime.strptime(dates.date_fin_per1, '%Y-%m-%d')

        return self.get_info(partner_id, depart, fin, month)

    def get_info_two(self, partner_id, dates, month):
        depart = datetime.strptime(dates.date_depart_per2, '%Y-%m-%d')
        fin = datetime.strptime(dates.date_fin_per2, '%Y-%m-%d')

        return self.get_info(partner_id, depart, fin, month)

    def get_info_three(self, partner_id, dates, month):
        depart = datetime.strptime(dates.date_depart_per3, '%Y-%m-%d')
        fin = datetime.strptime(dates.date_fin_per3, '%Y-%m-%d')

        return self.get_info(partner_id, depart, fin, month)

          

report_sxw.report_sxw('report.ca.client.periode', 'stats.ca.client.trois.periodes', 'addons/iller_stats/report/ca_client_periode.rml', parser=ca_client_periode)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
