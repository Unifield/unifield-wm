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

class wizard_produits_a_expedier_par_tournee(osv.osv):
    _name = 'produits.a.expedier.par.tournee'
    _columns = {
        'tournee_id': fields.many2one('tournee.iller', string="Tournée", required=True),
        'date': fields.date(string="Date de tournée", required=True),
    }
    
    def action_confirmer_tournee(self, cr, uid, ids, context={}):
        # Préparation des objets
        wiz_obj = self.browse(cr,uid,ids)[0]
        sp_obj = self.pool.get('stock.picking')
        sm_obj = self.pool.get('stock.move')
        # Récupération des ids de commandes correspondant à la recherche fournie
        res_ids = sp_obj.search(cr, uid, [('tournee_id', '=', wiz_obj.tournee_id.id), ('max_date', '=', wiz_obj.date), ('state', '=', 'confirmed')])
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
        datas = {'ids': context.get('active_ids', [])}
        res = self.read(cr, uid, ids, ['tournee_id', 'date'], context=context)
        res = res and res[0] or {}
        datas['form'] = res
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'produits.a.expedier.par.tournee',
            'datas': datas,
                }

wizard_produits_a_expedier_par_tournee()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
