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

class ca_client_par_an(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(ca_client_par_an, self).__init__(cr, uid, name, context)
        self.total_partner = {}
        self.total_repr = {}
        self.localcontext.update({
            'getRepr': self.get_repr,
            'getPartners': self.get_partners,
            'getInfos': self.get_info_one,
            'time': time,
            'locale': locale,
        })

    def get_repr(self, repr_id):
        '''
        Remplit le cache et retourne la liste des commerciaux
        '''
        for r in repr_id:
            if not self.total_repr.get(r, False):
                self.total_repr.update({r: {}})

        return self.pool.get('res.users').browse(self.cr, self.uid, repr_id)

    def get_partners(self, partner_ids):
        '''
        Remplit le cache et retourne la liste des partenaires
        '''
        for p in self.pool.get('res.partner').browse(self.cr, self.uid, partner_ids):
            if not self.total_partner.get(p.id, False):
                self.total_partner.update({p.id: {'seller_id': p.user_id.id}})

        return self.pool.get('res.partner').browse(self.cr, self.uid, partner_ids)

    def get_info(self, partner_id, date_debut, date_fin, year, month, repr_id=False):
        '''
        Retourne les totaux pour un mois donné et remplit le cache
        '''
        invoice_obj = self.pool.get('account.invoice')
        invoice_ids = []
        qty = 0.00
        val = 0.00


        if isinstance(partner_id, type([])):
            for p in partner_id:
                qty += self.total_partner[p][year]['qty']
                val += self.total_partner[p][year]['caa']
        else:
            invoice_ids = invoice_obj.search(self.cr, self.uid, [('date_invoice', '>=', date_debut),
                                                                 ('date_invoice', '<=', date_fin),
                                                                 ('partner_id', '=', partner_id)])

            # On fait la somme de toutes les factures
            for invoice in invoice_obj.browse(self.cr, self.uid, invoice_ids):
                for line in invoice.invoice_line:
                    qty += line.quantity
                    val += line.price_subtotal

            # On remplit le cache
            total_qty = self.total_partner[partner_id][year]['qty'] + qty
            total_caa = self.total_partner[partner_id][year]['caa'] + val
            month_qty = self.total_partner[partner_id][year][month]['qty'] + qty
            month_caa = self.total_partner[partner_id][year][month]['caa'] + val

            self.total_partner[partner_id][year].update({'qty': total_qty, 'caa': total_caa})
            self.total_partner[partner_id][year][month].update({'qty': month_qty, 'caa': month_caa})

        return {'qty': qty != 0.00 and qty or '', 'caa': val != 0.00 and val or ''}

    def get_info_one(self, year, partner_id, month, repr_id=False, tot_gen=False):
        '''
        Retourne l'information pour une cellule précise
        '''
        # Si l'année pour ce partenaire n'est pas dans le cache, on l'ajoute
        if not self.total_partner.get(partner_id).get(year, False):
            self.total_partner.get(partner_id).update({year: {'caa': 0.00, 'qty': 0.00}})

        # Si le mois pour ce partenaie n'est pas dans le cache, on l'ajoute
        if month != 0 and not self.total_partner.get(partner_id).get(year).get(month, False):
            self.total_partner[partner_id][year].update({month: {'caa': 0.00, 'qty': 0.00}})

        # On fait le total général de toutes les ventes
        if tot_gen:
            tot_qty = 0.00
            tot_val = 0.00
            for p in self.total_partner.keys():
                if month == 0:
                    tot_qty += self.total_partner[p][year]['qty']
                    tot_val += self.total_partner[p][year]['caa']
                else:
                    tot_qty += self.total_partner[p][year][month]['qty']
                    tot_val += self.total_partner[p][year][month]['caa']
            
            return {'qty': tot_qty != 0.00 and tot_qty or '', 'caa': tot_val != 0.00 and tot_val or ''}

        # On fait le total pour un représentant
        if repr_id:
            tot_qty = 0.00
            tot_val = 0.00
            for p in self.total_partner.keys():
                if self.total_partner[p].get('seller_id') == repr_id:
                    if month == 0:
                        tot_qty += self.total_partner[p][year]['qty']
                        tot_val += self.total_partner[p][year]['caa']
                    else:
                        tot_qty += self.total_partner[p][year][month]['qty']
                        tot_val += self.total_partner[p][year][month]['caa']

            return {'qty': tot_qty != 0.00 and tot_qty or '', 'caa': tot_val != 0.00 and tot_val or ''}

        # Si on recherhce les ventes totale d'une année pour un client
        if month == 0:
            return self.total_partner[partner_id][year]
        else:   # On recherche les ventes pour un mois précis
            depart = date(year, month, 1).strftime('%Y-%m-%d')
            fin = (date(month==12 and year+1 or year,
                       month==12 and 1 or month+1, 1) - timedelta(days=1)).strftime('%Y-%m-%d')

        return self.get_info(partner_id, depart, fin, year, month, repr_id)

report_sxw.report_sxw('report.ca.client.par.an', 'stats.ca.client.par.an', 'addons/iller_stats/report/ca_client_par_an.rml', parser=ca_client_par_an)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
