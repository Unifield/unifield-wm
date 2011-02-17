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
from time import strptime, strftime
from tools.translate import _

class iller_stock_move(osv.osv):
    _name = 'stock.move'
    _inherit = 'stock.move'

    def _get_pricelist_id(self, cr, uid, ids, *a):
        """
        Retourne la liste de prix pour cette ligne de préparation.
        On priorise la liste définie pour la ligne de commande si elle existe.
        Sinon on prend la liste de prix du client.
        Si on ne trouve aucune liste de prix, on prend les tarifs généraux.
        """
        # Préparation de la variable de retour
        res = {}
        for sm in self.browse(cr, uid, ids):
            # Préparation des valeurs possibles
            pricelist_id = None
            partner_pricelist_id = sm.picking_id.address_id.partner_id.property_product_pricelist.id or None
            default_pricelist = None
            if sm.sale_line_id:
                # Liste de prix du bon de commande
                pricelist_id = sm.sale_line_id.order_id.pricelist_id.id or None
                # Liste de prix du client
                partner_pricelist_id = sm.sale_line_id.order_id.partner_id.property_product_pricelist.id or None
            else:
                default_pricelist = self.pool.get('product.pricelist').search(cr, uid, [('name', '=', 'Tarif Général')], limit=1)[0]
            # Affectation de la liste de prix adéquate
            #+ - celle de la commande par défaut
            #+ - sinon celle du client par défaut
            #+ - sinon la liste de prix par défaut
            if pricelist_id:
                res[sm.id] = pricelist_id
            elif partner_pricelist_id:
                res[sm.id] = partner_pricelist_id
            else:
                res[sm.id] = default_pricelist
        return res

    _columns = {
        'pricelist_id': fields.function(_get_pricelist_id, method=True, type='many2one', relation='product.pricelist', store=True, string="Liste de prix"),
    }

iller_stock_move()

class iller_stock_picking(osv.osv):

    _name = 'stock.picking'
    _inherit = 'stock.picking'

    _columns = {
        'address_id': fields.many2one('res.partner.address', string='Partner', required=True),
    }

    def _get_price_unit_invoice(self, cr, uid, stock_move, type):
        """
        Retourne le prix unitaire d'une ligne d'expédition (stock_move) pour 
        une ligne d'écriture comptable (account_move)
        Note : 
          * Utilise la fonction price_get surchargée dans iller_product dans le 
            fichier pricelist.py#152
          * La date est celle de livraison
        """
        # Test de l'existence d'une ligne de commande (sale_order_line)
        if stock_move.sale_line_id and stock_move.sale_line_id.product_id.id == stock_move.product_id.id:
            return stock_move.sale_line_id.price_unit
        # Si pas de ligne de commande, on utilise l'identifiant de la liste de 
        #+ prix renseigné dans la ligne d'expédition (stock_move)
        elif stock_move.pricelist_id:
            # Récupération de l'id de la liste de prix
            pricelist_id = stock_move.pricelist_id.id
            # Utilisation de la date de livraison pour création de la facture
            date = strftime('%Y-%m-%d', strptime(stock_move.date, ('%Y-%m-%d %H:%M:%S'))) or False
            if not date:
                raise osv.except_osv(_('Erreur'), _("Aucune date de livraison n'a été renseignée !"))
            # On retourne le prix unitaire à l'aide de la fonction price_get 
            #+ (déjà surchargée par iller_product)
            return self.pool.get('product.pricelist').price_get(cr, uid, [pricelist_id], stock_move.product_id.id, stock_move.product_qty or 1.0, stock_move.picking_id.address_id.partner_id.id, context={ 'uom': stock_move.product_uom.id, 'date': date })[pricelist_id]
        # Si aucune ligne de commande, ni de liste de prix, alors on utilise le 
        #+ prix du produit
        else:
            if type in ('in_invoice', 'in_refund'):
                return stock_move.product_id.standard_price
            else:
                return stock_move.product_id.list_price

iller_stock_picking()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
