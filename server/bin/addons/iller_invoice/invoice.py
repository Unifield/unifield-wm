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
from tools import config


class iller_account_invoice_line(osv.osv):
    _name = 'account.invoice.line'
    _inherit = 'account.invoice.line'

    def product_id_change(self, cr, uid, ids, product, uom, qty=0, name='',
                          inv_type='out_invoice', partner_id=False,
                          fposition_id=False, price_unit=False,
                          address_invoice_id=False, context=None):
        """
        Mise à jour, en fonction de la liste de prix du partenaire renseigné :
        - du prix unitaire
        - de la description
        """
        prod_obj = self.pool.get('product.product')
        part_obj = self.pool.get('res.partner')
        price_obj = self.pool.get('product.pricelist')

        if not context:
            context = {}

        # Préparation de certains éléments
        new_price_unit = False

        # Si aucun prix unitaire n'est donné, alors on cherche celui de la
        # liste de prix du partenaire fourni en argument de la fonction
        if not price_unit and product:
            part_brw = part_obj.browse(cr, uid, partner_id, context=context)

            pricelist_id = part_brw.property_product_pricelist.id or None

            # Cas où le partenaire n'a pas de liste de prix (ne devrait, en
            # théorie, jamais arriver)
            if not pricelist_id:
                default_pricelist = price_obj.search(cr, uid, [
                    ('name', '=', 'Tarif Général'),
                ], limit=1, context=context)
                if default_pricelist:
                    pricelist_id = default_pricelist[0]

            # Calcul du prix
            context['uom'] = uom
            new_price_unit = price_obj.price_get(
                cr,
                uid,
                [pricelist_id],
                product,
                qty or 1.0,
                partner_id,
                context=context,
            )[pricelist_id]

        # Utilisation de la méthode par défaut
        res = super(iller_account_invoice_line, self).product_id_change(
            cr,
            uid,
            ids,
            product=product,
            uom=uom,
            qty=qty,
            name=name,
            partner_id=partner_id,
            fposition_id=fposition_id,
            price_unit=price_unit,
        )

        # Si on a un prix, on l'affecte, sinon on laisse celui par défaut
        if new_price_unit:
            res['value']['price_unit'] = new_price_unit

        # Vérification de l'existence de la description dans les valeurs
        desc = res['value'].get('name', False)
        if not desc and product:
            # Affectation de la description dans la ligne
            res['value']['name'] = prod_obj.read(
                cr,
                uid,
                product,
                context=context,
            ).get('name', False)

        # On retourne le résultat
        return res

iller_account_invoice_line()


class account_invoice(osv.osv):
    _name = "account.invoice"
    _inherit = "account.invoice"

    def copy(self, cr, uid, id, default=None, context=None):
        """
        Surcharge de copy pour mettre par défaut exported à False
        Les account move line sont automatiquement mises à false
        puisqu'elles sont recréées
        """
        if not default:
            default = {}

        default['exported'] = False
        return super(account_invoice, self).\
            copy(cr, uid, id, default=default, context=context)

    def _get_code_client(self, cr, uid, ids, field_name, arg, context=None):
        # Récupération du code client à afficher dans le formulaire
        if isinstance(ids, (int, long)):
            ids = [ids]

        res = {}
        for acc_invoice_record in self.browse(cr, uid, ids, context=context):
            res[acc_invoice_record.id] = acc_invoice_record.partner_id.ref

        return res

    def _amount_all(self, cr, uid, ids, field_name, arg, context):
        res = {}
        so_obj = self.pool.get('sale.order')
        sp_obj = self.pool.get('stock.picking')
        for invoice in self.browse(cr, uid, ids, context=context):
            res[invoice.id] = {
                'amount_untaxed': 0.0,
                'amount_tax': 0.0,
                'amount_total': 0.0,
                'frais_de_port': 0.0
            }

            frais_de_port = 0.0
            for line in invoice.invoice_line:
                if not line.name == 'Frais de port':
                    res[invoice.id]['amount_untaxed'] += line.price_subtotal
                else:
                    frais_de_port = line.price_subtotal

            for line in invoice.tax_line:
                res[invoice.id]['amount_tax'] += line.amount

            # On recherche les sale_order sur le nom par rapport à
            # l'origine de la facture
            sale_ids = so_obj.search(cr, uid, [
                ('name', '=', invoice.origin[-5:]),
            ], context=context)

            # Si des commandes existent bien
            if not sale_ids and res[invoice.id]['amount_untaxed'] < 50.00:
                # Si on a pas de sale order, il y a un problème mais on regarde
                # le montant de la facture pour en déduire les frais de port
                res[invoice.id]['frais_de_port'] = 3.00
            elif not sale_ids:
                res[invoice.id]['frais_de_port'] = 0.00
            else:
                so_records = so_obj.browse(cr, uid, sale_ids, context=context)
                pick_ids = sp_obj.search(cr, uid, [
                    ('name', '=', invoice.name),
                ], context=context)

                pick_records = sp_obj.\
                    read(cr, uid, pick_ids, ['include_port'], context=context)

                # On se base sur la commande pour voir le total commandé et
                # si le colisage inclut les frais de port
                for so_record in so_records:
                    for pick_record in pick_records:
                        if (so_record.amount_untaxed < 50) and \
                           pick_record['include_port']:
                            # Si le montant de la commande est < 50 ET que le
                            # colisage inclut les frais, alors 3 euros
                            res[invoice.id]['frais_de_port'] = frais_de_port
                        else:
                            res[invoice.id]['frais_de_port'] = 0.00

            # On fait le calcul du montant final
            res[invoice.id]['amount_total'] = \
                res[invoice.id]['amount_untaxed'] + \
                res[invoice.id]['amount_tax'] + \
                res[invoice.id]['frais_de_port']
        return res

    def _get_invoice_line(self, cr, uid, ids, context=None):
        line_obj = self.pool.get('account.invoice.line')
        result = {}
        for line in line_obj.browse(cr, uid, ids, context=context):
            result[line.invoice_id.id] = True
        return result.keys()

    def _get_invoice_tax(self, cr, uid, ids, context=None):
        tax_obj = self.pool.get('account.invoice.tax')
        result = {}
        for tax in tax_obj.browse(cr, uid, ids, context=context):
            result[tax.invoice_id.id] = True
        return result.keys()

    _columns = {
        'code': fields.function(
            _get_code_client,
            type='char',
            method=True,
            string='Code',
            readonly=True,
        ),
        'exported': fields.boolean(
            string=u'Exportée',
            readonly=True,
        ),
        'frais_de_port': fields.function(
            _amount_all,
            type='float',
            method=True,
            string='Frais de port',
            digits=(3, 2),
            readonly=True,
            store={
                'account.invoice': (
                    lambda self, cr, uid, ids, c={}: ids,
                    ['invoice_line'],
                    20,
                ),
                'account.invoice.tax': (
                    _get_invoice_tax,
                    None,
                    20,
                ),
                'account.invoice.line': (
                    _get_invoice_line,
                    [
                        'price_unit',
                        'invoice_line_tax_id',
                        'quantity',
                        'discount',
                    ],
                    20,
                ),
            },
            help="""Ajout automatique de 3 euros si le montant de la commande
 est inférieur à 50 euros.""",
            multi='all',
        ),
        'amount_untaxed': fields.function(
            _amount_all,
            method=True,
            digits=(16, int(config['price_accuracy'])),
            string='Untaxed',
            store={
                'account.invoice': (
                    lambda self, cr, uid, ids, c={}: ids,
                    ['invoice_line'],
                    20,
                ),
                'account.invoice.tax': (
                    _get_invoice_tax,
                    None,
                    20,
                ),
                'account.invoice.line': (
                    _get_invoice_line,
                    [
                        'price_unit',
                        'invoice_line_tax_id',
                        'quantity',
                        'discount',
                    ],
                    20,
                ),
            },
            multi='all',
        ),
        'amount_tax': fields.function(
            _amount_all,
            method=True,
            digits=(16, int(config['price_accuracy'])),
            string='Tax',
            store={
                'account.invoice': (
                    lambda self, cr, uid, ids, c={}: ids,
                    ['invoice_line'],
                    20,
                ),
                'account.invoice.tax': (
                    _get_invoice_tax,
                    None,
                    20,
                ),
                'account.invoice.line': (
                    _get_invoice_line,
                    [
                        'price_unit',
                        'invoice_line_tax_id',
                        'quantity',
                        'discount',
                    ],
                    20,
                ),
            },
            multi='all',
        ),
        'amount_total': fields.function(
            _amount_all,
            method=True,
            digits=(16, int(config['price_accuracy'])),
            string='Total',
            store={
                'account.invoice': (
                    lambda self, cr, uid, ids, c={}: ids,
                    ['invoice_line'],
                    20,
                ),
                'account.invoice.tax': (
                    _get_invoice_tax,
                    None,
                    20,
                ),
                'account.invoice.line': (
                    _get_invoice_line,
                    [
                        'price_unit',
                        'invoice_line_tax_id',
                        'quantity',
                        'discount',
                    ],
                    20,
                ),
            },
            multi='all',
        ),
    }

    _default = {
        'exported': lambda *a: False,
    }

    def onchange_partner_id(self, cr, uid, ids, type_partner=None,
                            partner_id=None, date_invoice=None,
                            payment_term=None, context={}):
        partner_obj = self.pool.get('res.partner')

        res = super(account_invoice, self).onchange_partner_id(
            cr,
            uid,
            ids,
            type_partner,
            partner_id,
            date_invoice,
            payment_term,
        )

        if partner_id:
            partner = partner_obj.browse(cr, uid, partner_id, context=context)
            if partner.ref:
                res['value'].update({'code': partner.ref})

        return res

account_invoice()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
