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

class wizard_articles_par_tournee(osv.osv):
    _name = 'articles.par.tournee'
    _columns = {
        'tournee_id': fields.many2one('tournee.iller', string="Tournées", required=True),
        'date': fields.date(string="Date de tournée", required=True),
        # Champ type suit les informations trouvés dans le module iller_product, product.py#161
        'type': fields.selection([('0', ''), ('1', 'Congelé'), ('2', 'Salaison'), ('3', 'Volaille')], string="Liste préparation", required=True)
    }
    
    _defaults = {
        'type': lambda *a: '0', # permet de n'avoir aucun tri sur le type d'articles de la liste résultante
    }
    
    def action_confirmer_liste_articles(self, cr, uid, ids, context={}):
        # Préparation des objets
        wiz_obj = self.browse(cr,uid,ids)[0]
        so_obj = self.pool.get('sale.order')
        irmd_obj = self.pool.get('ir.model.data')
        # Récupération des ids de commandes correspondant à la recherche fournie
        res_ids = so_obj.search(cr, uid, [('tournee_id', '=', wiz_obj.tournee_id.id), ('date_order', '=', wiz_obj.date), ('state', '=', 'progress')])
        # Création du domaine contenant les éléments de recherche
        type_article = wiz_obj.type
        domain = [('order_id', 'in', res_ids)]
        if type_article != '0':
            domain = [('order_id', 'in', res_ids), ('product_id.liste_prepa', '=', wiz_obj.type)]
        # Récupération de l'id de la vue à afficher
        view_ids = irmd_obj.search(cr, uid, [('name', '=', 'wizard_sale_order_line_form_view'), ('model', '=', 'ir.ui.view')])
        # Préparation de l'élément permettant de trouver la vue à  afficher
        if view_ids:
            view = irmd_obj.read(cr, uid, view_ids[0])
            view_id = (view.get('res_id'), view.get('name'))
        else:
            raise osv.except_osv(_('Erreur'), _("Impossible d'afficher le résultat : vue non trouvée."))
        # On retourne le résultat dans une vue en 'tree'
        return {'type': 'ir.actions.act_window',
                'res_model': 'sale.order.line',
                'view_type': 'form',
                'view_mode': 'tree,form',
                'view_id': view_id,
                'domain': domain,
                }

    def action_imprimer_rapport(self, cr, uid, ids, context={}):
        return { 'type': 'ir.actions.act_window.close' }

wizard_articles_par_tournee()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
