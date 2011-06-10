#!/usr/bin/env python
# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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

from osv import osv, fields

from datetime import date, datetime, timedelta


class stats_ca_client_trois_periodes(osv.osv_memory):
    _name = 'stats.ca.client.trois.periodes'

    _columns = {
        'depart_partner_id': fields.many2one('res.partner', 'Client Début'),
        'fin_partner_id': fields.many2one('res.partner', 'Client Fin'),
        'date_depart_per1': fields.date(string='Date de départ', required=True),
        'date_fin_per1': fields.date(string='Date de fin', required=True),
        'date_depart_per2': fields.date(string='Date de départ'),
        'date_fin_per2': fields.date(string='Date de fin'),
        'date_depart_per3': fields.date(string='Date de départ'),
        'date_fin_per3': fields.date(string='Date de fin'),
    }

    def default_get(self, cr, uid, fields, context={}):
        '''
        Mettre date de début au début du mois courant et date fin au dernier jour
        '''
        res = super(stats_ca_client_trois_periodes, self).default_get(cr, uid, fields, context=context)
 
        today = date.today()
        res['date_depart_per1'] = date(today.year, today.month, 1).strftime('%Y-%m-%d')
        res['date_fin_per1'] = (date(today.year, today.month+1, 1)-timedelta(days=1)).strftime('%Y-%m-%d')
 
        return res

    def print_report(self, cr, uid, ids, context={}):
        stat = self.browse(cr, uid, ids)[0]

        # Rechercher des référence des partenaires de début et de fin
        partner_obj = self.pool.get('res.partner')
        ref_partner_debut = partner_obj.browse(cr, uid, [stat.depart_partner_id.id])[0].ref
        ref_partner_fin = partner_obj.browse(cr, uid, [stat.fin_partner_id.id])[0].ref

        # Recherche des partenaires corrspondants
        partner_ids = partner_obj.search(cr, uid, [('ref', '>=', ref_partner_debut), ('ref', '<=', ref_partner_fin)])

        date_depart_per1 = datetime.strptime(stat.date_depart_per1, '%Y-%m-%d')
        date_fin_per1 = datetime.strptime(stat.date_fin_per1, '%Y-%m-%d')
        if stat.date_depart_per2 and stat.date_fin_per2:
            date_depart_per2 = datetime.strptime(stat.date_depart_per2, '%Y-%m-%d')
            date_fin_per2 = datetime.strptime(stat.date_fin_per2, '%Y-%m-%d')
        if stat.date_depart_per3 and stat.date_fin_per3:
            date_depart_per3 = datetime.strptime(stat.date_depart_per3, '%Y-%m-%d')
            date_fin_per3 = datetime.strptime(stat.date_fin_per3, '%Y-%m-%d')


        if date_depart_per1 > date_fin_per1 or \
            (stat.date_depart_per2 and stat.date_fin_per2 and date_depart_per2 < date_fin_per2) or \
            (stat.date_depart_per3 and stat.date_fin_per3 and date_depart_per3 < date_fin_per3):
            raise osv.except_osv('Erreur', 'La date de fin doit être supérieure à la date de début')
        if (date_fin_per1.year-date_depart_per1.year > 1 or (date_fin_per1.year-date_depart_per1.year == 1 and date_depart_per1.month < date_fin_per1.month)) \
            or (stat.date_depart_per2 and stat.date_fin_per2 and (date_fin_per2.year-date_depart_per2.year > 1 or (date_fin_per2.year-date_depart_per2 == 1 and date_depart_per2.month < date_fin_per2.month))) \
            or (stat.date_depart_per3 and stat.date_fin_per3 and (date_fin_per3.year-date_depart_per3.year > 1 or (date_fin_per3.year-date_depart_per3 == 1 and date_depart_per3.month < date_fin_per3.month))):
            raise osv.except_osv('Erreur', 'La période ne peut pas excéder une année')

        partners = []
        invoice_ids = []

        invoice_ids.extend(self.pool.get('account.invoice').search(cr, uid, [('date_invoice', '>=', stat.date_depart_per1),
                                                                             ('date_invoice', '<=', stat.date_fin_per1),
                                                                             ('partner_id', 'in', partner_ids),
                                                                             ('type', '=', 'out_invoice')]))
        invoice_ids.extend(self.pool.get('account.invoice').search(cr, uid, [('date_invoice', '>=', stat.date_depart_per2),
                                                                             ('date_invoice', '<=', stat.date_fin_per2),
                                                                             ('partner_id', 'in', partner_ids),
                                                                             ('type', '=', 'out_invoice')]))
        invoice_ids.extend(self.pool.get('account.invoice').search(cr, uid, [('date_invoice', '>=', stat.date_depart_per3),
                                                                             ('date_invoice', '<=', stat.date_fin_per3),
                                                                             ('partner_id', 'in', partner_ids),
                                                                             ('type', '=', 'iout_invoice')]))

        for res in self.pool.get('account.invoice').read(cr, uid, invoice_ids, ['partner_id']):
           if res['partner_id'][0] not in partners:
                partners.append(res['partner_id'][0])

        datas = {'ids': ids,
                 'model': 'stats.ca.client.trois.periodes',
                 'form': {'partners': partners,}}

        return {'type': 'ir.actions.report.xml',
                'report_name': 'ca.client.periode',
                'datas': datas}

stats_ca_client_trois_periodes()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

