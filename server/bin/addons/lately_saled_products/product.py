# -*- encoding: utf-8 -*-
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

class product_product(osv.osv):

    def _get_last_date_or_quantity(self, cr, uid, ids, field_name, arg, context={}):
        """
        Donne pour chaque produit soit la date de la dernière commande de chaque
         produit du fournisseur renseigné dans la variable 'context', 
        soit la quantité de cette même commande.
        """
        # TODO : affiner la recherche de la commande sur une date plus précise
        #+ Actuellement la finesse est au 'jour', pas à l'heure ni à la minute.
        
        # Préparation des objets
        res = {}
        sale_order_obj = self.pool.get('sale.order')
        sale_order_line_obj = self.pool.get('sale.order.line')
        partner_id = context.get('partner_id')
        mes_produits = self.browse(cr, uid, ids)

        # Traitement pour chaque produit trouvé
        for product in mes_produits:
            # Recherche des commandes faites par le fournisseur
            commande_ids = sale_order_obj.search(cr, uid, [('partner_id', '=', partner_id)])

            # Recherche des lignes de commandes correspondantes
            lignes = sale_order_line_obj.search(cr, uid, [('order_id', 'in', commande_ids), ('state', 'in', ['confirmed', 'done']), ('product_id', '=', product.product_tmpl_id.id)])

            # Préparation de la recherche de la date et de la commande attachée
            derniere_date = None
            commande_id = None
            # Traitement pour récupérer la date et la commande attaché (pour la 
            #+ quantité)
            for ligne in lignes:
                commande = sale_order_line_obj.browse(cr, uid, ligne)
                if not derniere_date:
                    derniere_date = commande.order_id.date_order
                    commande_id = commande.id
                elif commande.order_id.date_order > derniere_date:
                    derniere_date = commande.order_id.date_order
                    commande_id = commande.id

            # Préparation du résultat
            res[product.id] = None
            # On donne un résultat en fonction du champ demandé :
            #+ soit la date de la dernière commande
            #+ soit la quantité de la dernière commande
            if field_name == "derniere_date":
                res[product.id] = derniere_date
            elif field_name == "derniere_quantite":
                ligne_commande = sale_order_line_obj.read(cr, uid, commande_id)
                if ligne_commande:
                    res[product.id] = ligne_commande.get('product_uos_qty')
        return res

    _name = "product.product"
    _inherit = "product.product"
    _columns = {
        'derniere_date': fields.function(_get_last_date_or_quantity, method=True, type='date', string='Dernière date', store=False),
        'derniere_quantite': fields.function(_get_last_date_or_quantity, method=True, type='char', string='Dernière quantité', store=False),
    }

product_product()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
