#!/usr/bin/env python
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


class iller_commission(osv.osv):
    _name = 'product.pricelist.bareme'
    _inherit = 'product.pricelist.bareme'

    _columns = {
        'taux_com': fields.float(digits=(16,3), string='Taux commission'),
    }

iller_commission()


class iller_commission_line(osv.osv):
    _name = 'account.invoice.line'
    _inherit = 'account.invoice.line'

  
    def create(self, cr, uid, data, context={}):
        '''
            On calcule le montant de la commission lors de la création
        '''
        invoice_obj = self.pool.get('account.invoice')
        if 'price_unit' in data and 'invoice_id' in data:
            inv_type = invoice_obj.\
                browse(cr, uid, data['invoice_id'], context=context).type

            if inv_type == 'out_invoice':
                data['commission'] = self.\
                    _compute_commission(cr, uid, [], data, context)

        return super(iller_commission_line, self).\
            create(cr, uid, data, context=context)
  
    def write(self, cr, uid, ids, data, context={}):
        '''
            Si le prix unitaire a changé, 
            on recalcule le montant de la commission
        '''
        inv_obj = self.pool.get('account.invoice')
        for line in self.browse(cr, uid, ids, context=context):
            if 'price_unit' in data:
                inv_id = data.get('invoice_id', line.invoice_id.id)
                inv_type = inv_obj.\
                    browse(cr, uid, inv_id, context=context).type

                if inv_type == 'out_invoice':
                    data['commission'] = self.\
                        _compute_commission(cr, uid, ids, data, context)

        return super(iller_commission_line, self).\
            write(cr, uid, ids, data, context=context)

    def _compute_commission(self, cr, uid, ids, data, context={}):
        '''
            Réordonne les données pour faciliter le calcul de la valeur de
            la commission et envoie ces données à la foncion de calcul
        '''
        product_obj = self.pool.get('product.product')
        inv_obj = self.pool.get('account.invoice')
        
        lines = []

        if ids:
            for line in self.browse(cr, uid, ids, context=context):
                port = line.name == 'Frais de port'
                if not port and line.invoice_id.type == 'out_invoice':
                    lines.append({'unit_price': line.price_unit,
                                  'qty': line.quantity,
                                  'invoice_id': line.invoice_id.id,
                                  'name': line.product_id.name,
                                  'prix_vente': line.product_id.list_price})
        
        ## On rentre les nouvelles valeurs
        for l in lines:
            if 'price_unit' in data:
                l['unit_price'] = data.get('price_unit')

            if 'quantity' in data:
                l['qty'] = data.get('quantity')

            if 'invoice_id' in data:
                l['invoice_id'] = data.get('invoice_id')

        if 'invoice_id' in data:
            invoice = inv_obj.browse(cr, uid, data.get('invoice_id'))
            if len(lines) < 1:
                if invoice.type == 'out_invoice':
                    product = product_obj.browse(cr, uid, data.get('product_id'))
                    if product.name.strip() != 'PORT FACTURE FRAIS':
                        lines.append({'unit_price': data.get('price_unit'),
                                      'qty': data.get('quantity'),
                                      'name': product.name,
                                      'invoice_id': data.get('invoice_id', False),
                                      'prix_vente': product.list_price})

        res = self.set_value_commission(cr, uid, lines, context=context)

        if lines and not res[0]:
            return False
#            raise osv.except_osv('Erreur', 'Vous ne pouvez pas avoir un prix unitaire inférieur au prix de vente du produit multiplié par le barème c1 - L\'une des lignes de cette commande déroge à cette règle.')

        return res[0]

    
    def set_value_commission(self, cr, uid, lines=[], context={}):
        '''
            Effectue le calcul des commissions dans les différents cas
            possibles.
        '''
        bareme_obj = self.pool.get('product.pricelist.bareme')
        user_obj = self.pool.get('res.users')
        model_data_obj = self.pool.get('ir.model.data')
        invoice_obj = self.pool.get('account.invoice')
        partner_obj = self.pool.get('res.partner')
        message = ''
        res = False

        if not lines:
            return 0.00, ''

        ## On récupère tous les barèmes
        bareme_ids = bareme_obj.search(cr, uid, [('special', '=', False)])

        bareme_below = False
        bareme_above = False

        for l in lines:

            for bareme in bareme_obj.browse(cr, uid, bareme_ids):
                ## Si le prix unitaire est égal au prix de vente du produit * le 
                ## coeficient d'un barème, on retourne la commission associée au taux du barème
                if round(bareme.valeur*l.get('prix_vente'),2) == l.get('unit_price'):
                    return bareme.taux_com*l.get('unit_price')*l.get('qty'), message

                if l.get('unit_price') > round(bareme.valeur*l.get('prix_vente'),2) and (not bareme_below or bareme.valeur > bareme_below.valeur):
                    bareme_below = bareme

                if l.get('unit_price') < round(bareme.valeur*l.get('prix_vente'),2) and (not bareme_above or bareme.valeur < bareme_above.valeur):
                    bareme_above = bareme

            ## Si le prix inscrit est compris dans la fourchette des barèmes
            if bareme_below and bareme_above:
                taux_comm = (bareme_below.taux_com+bareme_above.taux_com)/2
                return taux_comm*l.get('unit_price')*l.get('qty'), message

            ## Si le prix est supérieur au prix de vente multiplié par le plus grand coeff., le taux de commission est de 1%
            if not bareme_above:
                return l.get('unit_price')*l.get('qty')*0.10, message

            ## Si le prix est inférieur au prix de vente multiplié par le plus petit coeff.
            if not bareme_below:
                if 'invoice_id' in l:
                    order = invoice_obj.browse(cr, uid, l.get('invoice_id'))
                    ## On vérifie si le client ne fait pas partie de la liste des clients autorisés
                    if order.partner_id.depassement:
                        return l.get('unit_price')*l.get('qty')*0.01, message
                elif 'partner_id' in l:
                    partner = partner_obj.browse(cr, uid, l.get('partner_id'))
                    ## On vérifie si le client ne fait pas partie de la liste des clients autorisés
                    if partner.depassement:
                        return l.get('unit_price')*l.get('qty')*0.01, message



                ## On vérifie si le client n'est pas une collectivité
                model_data_ids = model_data_obj.search(cr, uid, [('name', '=', 'pricelist_tarif_collectivite'), ('module', '=', 'iller_product'), ('model', '=', 'product.pricelist')])
                model_datas = model_data_obj.read(cr, uid, model_data_ids, ['res_id'])
                if model_datas and len(model_datas) > 0:
                    if 'invoice_id' in l:
                        so_obj = self.pool.get('sale.order')
                        so_ids = so_obj.search(cr, uid, [('invoice_ids', 'in', l.get('invoice_id'))])
                        if len(so_ids):
                            so = so_obj.browse(cr, uid, so_ids, context=context)[0]
                            if so.pricelist_id and so.pricelist_id.id == model_datas[0].get('res_id', False):
                                return l.get('unit_price')*l.get('qty')*0.01, message
                    elif 'pricelist_id' in l:
                        if l.get('pricelist_id') == model_datas[0].get('res_id', False):
                            return l.get('unit_price')*l.get('qty')*0.01, message


                ## On vérifie les droits de l'utilisateur
                model_data_ids = model_data_obj.search(cr, uid, [('name', '=', 'res_roles_super_salesman'), ('model', '=', 'res.roles')])
                model_datas = model_data_obj.read(cr, uid, model_data_ids, ['res_id'])
                if model_datas and len(model_datas) > 0:
                    user = user_obj.browse(cr, uid, uid)
                    ## Si l'utilisateur a le rôle DISTRI5
                    for role in user.roles_id:
                        if role.id == model_datas[0].get('res_id', False):
                            return l.get('unit_price')*l.get('qty')*0.01, 'Le prix indiqué est inférieur à ce qui est autorisé - Cependant, vos droits vous donne la possibilité de valider cette commande avec ce prix.'

                ## Dans tous les autres cas, on retourne une erreur
                return False, message

        return res, message


    def price_unit_change(self, cr, uid, ids, price_unit, product_id, qty, partner_id, pricelist_id, context={}):
        '''
            Affiche un message à l'utilisateur si il tente d'outrepasser la plage de prix
        '''
        product_obj = self.pool.get('product.product')

        lines = []

        if not price_unit or not product_id or not qty:
            return {'value': {}}

        ## On récupère les inforamtions du produit
        product = product_obj.browse(cr, uid, product_id)

        if product.name.strip() != 'PORT FACTURE FRAIS':
            ## On enregistre la ligne
            lines.append({'unit_price': price_unit,
                          'qty': qty,
                          'partner_id': partner_id,
                          'pricelist_id': pricelist_id,
                          'name': product.name,
                          'prix_vente': product.list_price})

        ## On lance le calcul de la commission
        res2 = self.set_value_commission(cr, uid, lines, context=context)

        ## Si le prix est inférieur et que l'on a pas les droits de surpasser, on affiche une erreur
        if not res2[0]:
            return {'value': {},
                    'warning': {'title': 'Erreur !',
                                'message': 'Vous ne pourrez pas enregistrer la commande car le prix indiqué est inférieur à ce qui est autorisé.'}}
        elif res2[1] != '':
            return {'value': {'commission': res2[0]},
                    'warning': {'title': 'Attention !',
                                'message': res2[1]}}
        return {'value': {'commission': res2[0]}}


    def product_id_change(self, cr, uid, ids, product, uom, qty=0, name='', inv_type='out_invoice', partner_id=False, fposition_id=False, price_unit=False, address_invoice_id=False, context=None):
        '''
            Modifie la valeur de la commission lors du changement de produit
        '''
        res = super(iller_commission_line, self).product_id_change(cr, uid, ids, product, uom, qty, name, inv_type, partner_id, fposition_id, price_unit, address_invoice_id, context=context)

        if not product:
            res.get('value').update({'commission': 0.00})
        else:
            res2 = self.price_unit_change(cr, uid, ids, res.get('value', {'price_unit':0.00}).get('price_unit', 0.00), product, qty, partner_id, False, context=context)
            res.get('value').update(res2.get('value'))

        return res


    _columns = {
        'commission': fields.float(digits=(16,2), string='Commission'),
    }

iller_commission_line()


class iller_invoice_commission(osv.osv):
    _name = 'account.invoice'
    _inherit = 'account.invoice'

    def _get_commission(self, cr, uid, ids, field_name, arg, context={}):
        res = {}
        for invoice in self.browse(cr, uid, ids):
            res[invoice.id] = 0.00
            for line in invoice.invoice_line:
                res[invoice.id] += line.commission

        return res


    _columns = {
        'commission': fields.function(_get_commission, method=True, string='Commission', store=False, readonly=True),
    }

iller_invoice_commission()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

