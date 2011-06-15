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

from osv import osv
from osv import fields
from datetime import datetime
import time

class wizard_produits_a_expedier_par_tournee(osv.osv_memory):
    _name = 'produits.a.expedier.par.tournee'
    _columns = {
        'tournee_id': fields.many2one('tournee.iller', string="Tournée", required=True),
        'date': fields.date(string="Date de tournée", required=True),
    }

    _defaults = {
        'date': lambda *a:time.strftime('%Y-%m-%d'),
    }

    def action_confirmer_tournee(self, cr, uid, ids, context={}):
        # Préparation des objets
        wiz_obj = self.browse(cr,uid,ids)[0]
        sp_obj = self.pool.get('stock.picking')
        sm_obj = self.pool.get('stock.move')
        date = datetime.strptime(wiz_obj.date, '%Y-%m-%d')
        max_date = datetime(date.year, date.month, date.day, 23, 59, 59).__str__()
        min_date = datetime(date.year, date.month, date.day, 0, 0, 0).__str__()
        # Récupération des ids de commandes correspondant à la recherche fournie
        res_ids = sp_obj.search(cr, uid, [('tournee_id', '=', wiz_obj.tournee_id.id), ('max_date', '>=', min_date), ('max_date', '<=', max_date), ('state', '=', 'confirmed')])
        if context and context.get('sp_state'):
            res_ids = sp_obj.search(cr, uid, [('tournee_id', '=', wiz_obj.tournee_id.id), ('max_date', '>=', min_date), ('max_date', '<=', max_date)])
        # Création du domaine contenant les éléments de recherche
        domain = [('picking_id', 'in', res_ids)]
        # On retourne le résultat dans une vue en 'tree'
        return {'type': 'ir.actions.act_window',
                'res_model': 'stock.move',
                'view_type': 'form',
                'view_mode': 'tree,form',
                'domain': domain,
                }

    def action_imprimer_rapport(self, cr, uid, ids, context={}):
        if context and context.get('sp_state', False):
            raise osv.except_osv('Erreur', "Cette fonction n'est pas disponible pour ce formulaire.")
        datas = {'ids': context.get('active_ids', [])}
        res = self.read(cr, uid, ids, ['tournee_id', 'date'], context=context)
        res = res and res[0] or {}
        datas['form'] = res
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'produits.a.expedier.par.tournee',
            'datas': datas,
                }

    def fields_view_get(self, cr, uid, view_id=None, view_type='form', context={}, toolbar=False):
        res = super(wizard_produits_a_expedier_par_tournee, self).fields_view_get(cr, uid, view_id, view_type, context, toolbar)
        if context and context.get('sp_state', False):
            arch = res.get('arch', False).replace('<button string="Imprimer un rapport" name="action_imprimer_rapport" type="object" icon="gtk-print"/>', '')
            arch = arch.replace('<separator string="Produits à expédier par tournée"/>', '<separator string="État des produits à expédier par tournée"/>')
            res['arch'] = arch
        return res

wizard_produits_a_expedier_par_tournee()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
