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
from tools.translate import _

class product_product(osv.osv):

    def _compute_last_date_or_quantity(self, cr, uid, ids, field_name, arg, context={}):
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
        partner_id = context.get('partner_id', False)
        mes_produits = self.browse(cr, uid, ids, context=context)

        # Traitement pour chaque produit trouvé
        for product in mes_produits:
            # Recherche des commandes faites par le fournisseur
            commande_ids = sale_order_obj.search(cr, uid, [('partner_id', '=', partner_id)], context=context)

            # Recherche des lignes de commandes correspondantes
            lignes = sale_order_line_obj.search(cr, uid, [('order_id', 'in', commande_ids), ('state', 'in', ['confirmed', 'done']), ('product_id', '=', product.product_tmpl_id.id)], context=context)

            # Préparation de la recherche de la date et de la commande attachée
            derniere_date = None
            commande_id = None
            # Traitement pour récupérer la date et la commande attaché (pour la 
            #+ quantité)
            for ligne in lignes:
                commande = sale_order_line_obj.browse(cr, uid, ligne, context=context)
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
                ligne_commande = sale_order_line_obj.read(cr, uid, commande_id, ['id', 'product_uos_qty'], context=context)
                if ligne_commande:
                    res[product.id] = ligne_commande.get('product_uos_qty')
        return res

    _name = "product.product"
    _inherit = "product.product"
    _columns = {
        'derniere_date': fields.function(_compute_last_date_or_quantity, type='date', method=True, string='Dernière date', 
            store=False),
        'derniere_quantite': fields.function(_compute_last_date_or_quantity, type='float', method=True, string='Dernière quantité', 
            store=False),
    }

    def read(self, cr, uid, ids, fields=None, context={}, load='_classic_read'):
        res = super(product_product, self).read(cr, uid, ids, fields, context=context, load=load)

        # Création de la liste par défaut
        complete_list = res

        if context.get('partner_id') and context.get('from', False) == 'sale.order.line':
            # Division de la liste en deux listes : 
            # - ceux ayant une dernière date
            # - ceux n'en ayant pas (False)
            false_list = []
            last_date_list = []
            for el in res:
                if not el.get('derniere_date'):
                    false_list.append(el)
                else:
                    last_date_list.append(el)

            if last_date_list:
                # Tri de la liste ayant des dates
                # Récupération des dates
                tmp_dates = []
                for el in last_date_list:
                    tmp_dates.append(el.get('derniere_date'))
                # Suppression des doublons
                dates = list(set(tmp_dates))
                # Tri des dates par ordre décroissant
                dates = sorted(dates, reverse=True)
                
                # Création du nouveau tableau contenant les éléments triés par 
                #+ date décroissante (selon dates[])
                tmp_last_date_list = list(last_date_list) # copie de la liste originale
                new_date_list = [] # nouvelle liste
                # Parcours des dates
                for ladate in dates:
                    # création d'un tableau temporaire des éléments d'une même date
                    tmp_prod = []
                    for prod in tmp_last_date_list:
                        if prod.get('derniere_date') == ladate:
                            tmp_prod.append(prod)
                    # Suppression des produits déjà récupérés de la liste 
                    #+ de parcours
                    for prod in tmp_prod:
                        tmp_last_date_list.remove(prod)
                    
                    # Récupération des noms
                    noms = []
                    for el in tmp_prod:
                        noms.append(el.get('name'))
                    # Tri des noms par ordre croissant
                    noms = sorted(noms)
                    
                    # Parcours des noms pour en faire une liste
                    tmp_el = []
                    for nom in noms:
                        tmp_nom = []
                        for prod in tmp_prod:
                            if prod.get('name') == nom:
                                tmp_nom.append(prod)
                        # Suppression des produits déjà récupérés de la liste 
                        #+ de parcours
                        for prod in tmp_nom:
                            tmp_prod.remove(prod)
                        tmp_el += tmp_nom
                    
                    # ajout du résultat à la liste commune
                    new_date_list += tmp_el
                
                # On redonne à last_date_list les éléments triés
                last_date_list = new_date_list
                
                # On concatène la liste ayant des dates avec celle sans dates
                complete_list = last_date_list + false_list
        # on retourne complete_list
        return complete_list

product_product()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
