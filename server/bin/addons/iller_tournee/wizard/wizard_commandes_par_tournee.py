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
from tools.translate import _

class commandes_par_tournee(osv.osv):
    """
    Affiche un wizard pour obtenir la liste des commandes validées 
    par tournée et par date (selon ce que l'utilisateur complète)
    """
    _name = 'commandes.par.tournee'
    _columns = {
        'tournee_id': fields.many2one('tournee.iller', string="Tournée"),
        'date': fields.date(string="Date", required=True)
    }

    def action_confirmer_liste_commandes(self, cr, uid, ids, context={}):
        # Préparation des objets
        wiz_obj = self.browse(cr,uid,ids)[0]
        # Test sur les données complétées
        if wiz_obj.tournee_id: 
            # Cas où une tournée est donnée
            domain = [('tournee_id', '=', wiz_obj.tournee_id.id), ('date_order', '=', wiz_obj.date), ('state', '=', 'progress')]
        else:
            # Cas où aucune tournée n'est donnée
            domain = [('date_order', '=', wiz_obj.date), ('state', '=', 'progress')]
        # On renvoie sur une liste de commandes
        return {'type': 'ir.actions.act_window',
                'res_model': 'sale.order',
                'view_type': 'form',
                'view_mode': 'tree,form',
                'domain': domain,
                }

commandes_par_tournee()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
