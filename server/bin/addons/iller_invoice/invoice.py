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

class iller_account_invoice_line(osv.osv):
    _name = 'account.invoice.line'
    _inherit = 'account.invoice.line'

    def product_id_change(self, cr, uid, ids, product, uom, qty=0, name='', type='out_invoice', partner_id=False, fposition_id=False, price_unit=False, address_invoice_id=False, context=None):
        """
        Mise à jour, en fonction de la liste de prix du partenaire renseigné : 
        - du prix unitaire
        - de la description
        """
        # Préparation de certains éléments
        new_price_unit = False
        prod_obj = self.pool.get('product.product')
        # Si aucun prix unitaire n'est donné, alors on cherche celui de la 
        #+ liste de prix du partenaire fourni en argument de la fonction
        if not price_unit:
            if product:
                prod = prod_obj.browse(cr, uid, product, context=context)
                pricelist_id = self.pool.get('res.partner').browse(cr, uid, partner_id, context=context).property_product_pricelist.id or None
                # Cas où le partenaire n'a pas de liste de prix (ne devrait, en 
                #+ théorie, jamais arriver)
                if not pricelist_id:
                    default_pricelist = self.pool.get('product.pricelist').search(cr, uid, [('name', '=', 'Tarif Général')], limit=1)[0]
                    pricelist_id = default_pricelist
                # Calcul du prix
                new_price_unit = self.pool.get('product.pricelist').price_get(cr, uid, [pricelist_id], prod.id, qty or 1.0, partner_id, context={ 'uom': uom })[pricelist_id]
        # Utilisation de la méthode par défaut
        res = super(iller_account_invoice_line, self).product_id_change(cr, uid, ids, product=product, uom=uom, qty=qty, name=name, partner_id=partner_id, fposition_id=fposition_id, price_unit=price_unit)
        # Si on a un prix, on l'affecte, sinon on laisse celui par défaut
        if new_price_unit:
            res['value']['price_unit'] = new_price_unit
        # Vérification de l'existence de la description dans les valeurs
        desc = res['value'].get('name', False)
        if not desc and product:
            # Affectation de la description dans la ligne
            res['value']['name'] = prod_obj.read(cr, uid, product, context=context).get('name', False)
        # On retourne le résultat
        return res

iller_account_invoice_line()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
