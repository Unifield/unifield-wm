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
from tools.translate import _

from datetime import date, timedelta, datetime

class stats_entree_article(osv.osv_memory):
    _name = 'stats.entree.article'

    _columns = {
        'date_depart': fields.date(string='Date Début', required=True),
        'date_fin': fields.date(string='Date Fin', required=True),
    }

    def default_get(self, cr, uid, fields, context={}):
        '''
        Mettre date de début au début du mois courant et date fin au dernier jour
        '''
        res = super(stats_entree_article, self).default_get(cr, uid, fields, context=context)

        today = date.today()
        res['date_depart'] = date(today.year, today.month, 1).strftime('%Y-%m-%d')
        res['date_fin'] = (date(today.year, today.month+1, 1)-timedelta(days=1)).strftime('%Y-%m-%d')

        
        return res

    def print_report(self, cr, uid, ids, context={}):
        '''
        Recherche de toutes les factures fournisseurs de la période
        puis impression du rapport
        '''
        obj = self.browse(cr, uid, ids)[0]

        date_debut = datetime.strptime(obj.date_depart, '%Y-%m-%d')
        date_fin = datetime.strptime(obj.date_fin, '%Y-%m-%d')

        if date_fin < date_debut:
            raise osv.except_osv(_('Erreur'), _('Vous ne pouvez pas avoir une date de fin inférieure à la date de début'))

        invoice_obj = self.pool.get('account.invoice')
        invoice_ids = invoice_obj.search(cr, uid, [('date_invoice', '>=', obj.date_depart), ('date_invoice', '<=', obj.date_fin)])

        datas = {'ids': ids[0],
                 'model': 'stats.entree.article',
                 'form': {'invoices': invoice_ids}}

        return {'type': 'ir.actions.report.xml',
                'report_name': 'report.entree.article',
                'datas': datas}


        
stats_entree_article()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

