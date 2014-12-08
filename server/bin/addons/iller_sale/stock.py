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
import time

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
            partner_pricelist_id = None
            if sm.picking_id and sm.picking_id.address_id and sm.picking_id.address_id.partner_id:
                partner_pricelist_id = sm.picking_id.address_id.partner_id.property_product_pricelist.id or None
            default_pricelist = None
            if sm.sale_line_id:
                # Liste de prix du bon de commande
                pricelist_id = sm.sale_line_id.order_id.pricelist_id.id or None
                # Liste de prix du client
                partner_pricelist_id = sm.sale_line_id.order_id.partner_id.property_product_pricelist.id or None
            else:
                default_pricelist = self.pool.get('product.pricelist').search(cr, uid, [('name', 'ilike', 'NU01')], limit=1)[0]
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

    def _is_reliquat(self, cr, uid, ids, name, args, context=None):
        res = {}
        # On regarde si le stock picking en cours est un reliquat
        for this in self.browse(cr, uid, ids, context=context):
            if not this.backorder_id:
                res[this.id] = True
            else:
                res[this.id] = False
        return res

    _columns = {
        'address_id': fields.many2one('res.partner.address', string='Partner', required=True),
        'include_port': fields.function(_is_reliquat, method=True, type='boolean', store=False, string='Inclure frais de port ?'),
        #~ 'include_port': fields.boolean('Inclure frais de port ?'),
    }
    _defaults = {
        'include_port': lambda *a: True,
    }


    def _get_price_unit_invoice(self, cr, uid, stock_move, inv_type):
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
            if inv_type in ('in_invoice', 'in_refund'):
                return stock_move.product_id.standard_price
            else:
                return stock_move.product_id.list_price


    def  check_created_invoice(self, cr, uid, inv_ids, context=None):
        inv_obj = self.pool.get('account.invoice')
        sp_obj = self.pool.get('stock.picking')
        inv = inv_obj.read(cr, uid, inv_ids, ['amount_total', 'partner_id'], context=context)
        date_courante = time.strftime('%Y-%m-%d')
        inv_ids_partner = inv_obj.search(cr, uid, [
            ('partner_id', '=', inv['partner_id'][0]),
            ('date_invoice', '=', date_courante)
        ], context=context)
        inv_records = inv_obj.browse(cr, uid, inv_ids_partner, context=context)
        montant_total = inv['amount_total']
        for inv_record in inv_records:
            montant_total += inv_record.amount_total
            if montant_total > 50:
                return True
        return False


    def action_invoice_create(self, cr, uid, ids, journal_id=False, group=False, inv_type='out_invoice', context=None):
        """
        Donne l'ensemble des factures pour les "pickings"
        """
        if isinstance(ids, (int, long)):
            ids = [ids]
        res = {}
        
        for sp in self.browse(cr, uid, ids, context=context):
            if sp.sale_id:
                context.update({'from_sale_order': sp.sale_id.id})

            res2 = super(iller_stock_picking, self).action_invoice_create(cr, uid, [sp.id], journal_id, group, inv_type, context)
            inv_ids = res2.values()

            import pdb
            pdb.set_trace()
            if inv_ids and (sp.sale_id.amount_untaxed < 50) and sp.include_port and not self.check_created_invoice(cr, uid, inv_ids[0], context=context):
                ait_obj = self.pool.get('account.invoice.tax')
                tax = self.pool.get('account.tax').search(cr, uid, [('amount', '=', 0.20), ('type_tax_use', '=', 'sale')], context=context)
                # Si le montant de la commande est < 50 et que le colis comprend les frais de port
                # alors on crée une nouvelle ligne de facture pour le frais de port
                inv_line_id = self.pool.get('account.invoice.line').create(cr, uid, {
                    'name': "Frais de port",
                    'origin': sp.name + ':' + sp.sale_id.name,
                    'account_id': self.pool.get('account.account').search(cr, uid, [('code', '=', '70811000')], context=context)[0], #854
                    'price_unit': 3.0,
                    'quantity': 1.0,
                    'invoice_id': inv_ids[0],
                    'invoice_line_tax_id': [(6, 0, [tax[0]])],
                    'product_id': self.pool.get('product.product').search(cr, uid, [('default_code', '=', '999999')], context=context)[0], #2675
                }, context=context)
                # On recalcule les taxes
                compute_taxes = ait_obj.compute(cr, uid, inv_ids[0], context=context)
                compute_values = compute_taxes.values()
                tab_keys = []

                # On parcourt les lignes de taxe pour les créer si elles ne sont pas présentes dans l'invoice
                for inv in self.pool.get('account.invoice').browse(cr, uid, [inv_ids[0]], context=context):
                    for tax in inv.tax_line:
                        if tax.manual:
                            continue
                        key = (tax.tax_code_id.id, tax.base_code_id.id, tax.account_id.id)
                        tab_keys.append(key)
                for comp_tax in compute_taxes.keys():
                    if comp_tax not in tab_keys:
                        ait_obj.create(cr, uid, compute_taxes[comp_tax], context=context)

            res.update(res2)
        return res


iller_stock_picking()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
