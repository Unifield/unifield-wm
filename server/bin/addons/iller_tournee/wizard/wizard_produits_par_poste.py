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

from osv import osv, fields
import time
from datetime import datetime

class wizard_produits_par_poste(osv.osv):
    _name = "produits.par.poste"

    _columns = {
        'tournee_id': fields.many2one('tournee.iller', string="Tournée", required=False),
        'date': fields.date(string="Date de tournée", required=True),
        'poste_id': fields.many2one('iller.poste', string="Poste de préparation", required=True),
    }

    _defaults = {
        'date': lambda *a:time.strftime('%Y-%m-%d'),
    }

    def action_confirmer_poste(self, cr, uid, ids, context={}):
        """
        Retourne la liste des mouvements par poste et par tournée [facultative].
        """
        # Préparation des objets
        wiz_obj = self.browse(cr, uid, ids, context=context)[0]
        sp_obj = self.pool.get('stock.picking')
        tournee = wiz_obj.tournee_id.id or None
        poste = wiz_obj.poste_id.id
        date = datetime.strptime(wiz_obj.date, '%Y-%m-%d')
        max_date = datetime(date.year, date.month, date.day, 23, 59, 59).__str__()
        min_date = datetime(date.year, date.month, date.day, 0, 0, 0).__str__()
        # Récupération des ids de commandes correspondant à la recherche fournie
        if not tournee:
            res_ids = sp_obj.search(cr, uid, [('max_date', '>=', min_date), ('max_date', '<=', max_date)])
        else:
            res_ids = sp_obj.search(cr, uid, [('max_date', '>=', min_date), ('max_date', '<=', max_date), ('tournee_id', '=', tournee)])
        # Création du domaine contenant les éléments de recherche
        domain = [('picking_id', 'in', res_ids), ('poste_id', '=', poste)]
        # On retourne le résultat dans une vue en 'tree'
        return {'type': 'ir.actions.act_window',
                'res_model': 'stock.move',
                'view_type': 'form',
                'view_mode': 'tree,form',
                'domain': domain,
        }

wizard_produits_par_poste()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
