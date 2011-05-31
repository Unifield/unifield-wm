#!/usr/bin/env python
# -*- encoding: utf-8 -*-

from osv import osv
from osv import fields
import re


class iller_sale_comment(osv.osv):
    _name = 'iller.sale.comment'
    _description = 'Commentaire par produit/client'
    _rec_name = 'product_id'

    _columns = {
        'product_id': fields.many2one('product.product', string='Produit', required=True),
        'partner_id': fields.many2one('res.partner', string='Client', required=True),
        'comment': fields.text(string='Commentaire'),
    }

iller_sale_comment()


class iller_sale_line(osv.osv):
    _name = 'sale.order.line'
    _inherit = 'sale.order.line'


    def write(self, cr, uid, ids, data, context={}):
        '''
            Enregistre ou remplace le commentaire enregistré dans 
            la BDD
        '''
        comment_obj = self.pool.get('iller.sale.comment')

        if 'notes' in data and data.get('notes') != '':
            for line in self.browse(cr, uid, ids):
                comment_ids = comment_obj.search(cr, uid, [('product_id', '=', line.product_id.id), ('partner_id', '=', line.order_id.partner_id.id)])
                if comment_ids and len(comment_ids) > 0:
                    comment_obj.write(cr, uid, comment_ids, {'comment': data.get('notes')})
                else:
                    comment_obj.create(cr, uid, {'comment': data.get('notes'), 'partner_id': line.order_id.partner_id.id, 'product_id': line.product_id.id})

        return super(iller_sale_line, self).write(cr, uid, ids, data, context=context)


    def create(self, cr, uid, data, context={}):
        '''
            Enregistre ou remplace le commentaire enregistré dans
            la BDD
        '''
        comment_obj = self.pool.get('iller.sale.comment')
        order_obj = self.pool.get('sale.order')


        if 'notes' in data and data.get('notes') != '' and 'product_id' in data and 'order_id' in data:
            partner_id = order_obj.browse(cr, uid, data.get('order_id')).partner_id.id
            comment_ids = comment_obj.search(cr, uid, [('product_id', '=', data.get('product_id')), ('partner_id', '=', partner_id)])
            if comment_ids and len(comment_ids) > 0:
                comment_obj.write(cr, uid, comment_ids, {'comment': data.get('notes')})
            else:
                comment_obj.create(cr, uid, {'comment': data.get('notes'), 'partner_id': partner_id, 'product_id': data.get('product_id')})

        return super(iller_sale_line, self).create(cr, uid, data, context={})


    def product_id_change(self, cr, uid, ids, pricelist, product, qty=0,
          uom=False, qty_uos=0, uos=False, name='', partner_id=False,
          lang=False, update_tax=True, date_order=False, packaging=False, fiscal_position=False, tournee_id=False, flag=False):
        '''
            Lors du changement de produit, on regarde si un commentaire existe déjà 
            pour ce produit et ce partenaire
        '''
        comment_obj = self.pool.get('iller.sale.comment')
        product_obj = self.pool.get('product.product')
        tournee_obj = self.pool.get('tournee.iller')

        comment = ''
        res = super(iller_sale_line, self).product_id_change(cr, uid, ids, pricelist, product, qty, uom, qty_uos, uos, name, partner_id, \
                                                             lang, update_tax, date_order, packaging, fiscal_position, tournee_id, flag)

        if product and partner_id:
            comment_ids = comment_obj.search(cr, uid, [('partner_id', '=', partner_id), ('product_id', '=', product)])
            if comment_ids and len(comment_ids) > 0:
                comment = comment_obj.browse(cr, uid, comment_ids[0]).comment

        res['value'].update({'notes': comment})

        return res


iller_sale_line()

class iller_sale(osv.osv):
    _name = 'sale.order'
    _inherit = 'sale.order'

    _columns = {
        'user_id': fields.many2one('res.users', 'Salesman', states={'draft': [('readonly', False)]}, select=True, required=True),
    }

    _defaults = {
        'user_id': lambda obj, cr, uid, context: uid,
    }

    def _make_invoice(self, cr, uid, order, lines, context={}):
        """
        Rajoute un contexte à la création d'une facture pour ajouter le vendeur
        """
        #@@@override@sale.sale.py:_make_invoice
        a = order.partner_id.property_account_receivable.id
        if order.payment_term:
            pay_term = order.payment_term.id
        else:
            pay_term = False
        for preinv in order.invoice_ids:
            if preinv.state not in ('cancel',):
                for preline in preinv.invoice_line:
                    inv_line_id = self.pool.get('account.invoice.line').copy(cr, uid, preline.id, {'invoice_id': False, 'price_unit': -preline.price_unit})
                    lines.append(inv_line_id)
        inv = {
            'name': order.client_order_ref or order.name,
            'origin': order.name,
            'type': 'out_invoice',
            'reference': "P%dSO%d" % (order.partner_id.id, order.id),
            'account_id': a,
            'partner_id': order.partner_id.id,
            'address_invoice_id': order.partner_invoice_id.id,
            'address_contact_id': order.partner_order_id.id,
            'invoice_line': [(6, 0, lines)],
            'currency_id': order.pricelist_id.currency_id.id,
            'comment': order.note,
            'payment_term': pay_term,
            'fiscal_position': order.fiscal_position.id or order.partner_id.property_account_position.id
        }
        inv_obj = self.pool.get('account.invoice')
        inv.update(self._inv_get(cr, uid, order))
        # DEBUT modification
        context.update({'from_sale_order': order.id})
        inv_id = inv_obj.create(cr, uid, inv, context=context)
        # FIN modification
        data = inv_obj.onchange_payment_term_date_invoice(cr, uid, [inv_id], pay_term, time.strftime('%Y-%m-%d'))
        if data.get('value', False):
            inv_obj.write(cr, uid, [inv_id], data['value'], context=context)
        inv_obj.button_compute(cr, uid, [inv_id])
        return inv_id
        #@@@end

iller_sale()

class iller_partner(osv.osv):
    _name = 'res.partner'
    _inherit = 'res.partner'


    def name_search(self, cr, uid, name='', args=[], operator='ilike', context={}, limit=80):
        '''
            Recherche du partenaire grâce à son code, son nom, son numéro de 
            téléphone ou son adresse (ville, rue)
        '''
        if 'from' in context and context.get('from') == 'sale.order':
            address_obj = self.pool.get('res.partner.address')
            res = []

            ## Recherche sur le code exact
            if name:
                res = self.search(cr, uid, [('ref', '=', name)] + args, limit=limit, context=context)

                ## Recerche sur le numéro de téléphone exact
                if not res or len(res) < 1:
                    tel = re.sub('\D', '', name)
                    addr_ids = address_obj.search(cr, uid, [('phone', operator, tel)], limit=limit, context=context)
                    for addr in address_obj.browse(cr, uid, addr_ids):
                        if addr.partner_id and addr.partner_id.id and not addr.partner_id.bloque and addr.partner_id.id not in res:
                            res.append(addr.partner_id.id)

                ## Recherche sur le nom, la ville ou le nom de la rue
                if not res or len(res) < 1:
                    ## Nom de la rue
                    street_ids = address_obj.search(cr, uid, [('street', operator, name)], limit=limit, context=context)
                    for street in address_obj.browse(cr, uid, street_ids):
                        if street.partner_id.id not in res:
                            res.append(street.partner_id.id)
                    ## Nom secondaire de la rue
                    street2_ids = address_obj.search(cr, uid, [('street2', operator, name)], limit=limit, context=context)
                    for street2 in address_obj.browse(cr, uid, street2_ids):
                        if street2.partner_id.id not in res:
                            res.append(street2.partner_id.id)
                    ## Nom de la ville
                    city_ids = address_obj.search(cr, uid, [('city', operator, name)], limit=limit, context=context)
                    for city in address_obj.browse(cr, uid, city_ids):
                        if city.partner_id.id not in res:
                            res.append(city.partner_id.id)

                    ## Nom du partenaire
                    name_ids = self.search(cr, uid, [('name', operator, name)] + args, limit=limit, context=context)
                    for name in name_ids:
                        if name not in res:
                            res.append(name)
            else:
                res = self.search(cr, uid, [] + args, limit=limit, context=context)


            return self.name_get(cr, uid, res, context)
        else:
            return super(iller_partner, self).name_search(cr, uid, name, args, operator, context=context, limit=limit)


iller_partner()


class iller_partner_address(osv.osv):
    _name = 'res.partner.address'
    _inherit = 'res.partner.address'

    def create(self, cr, uid, values, context={}):
        '''
            Modifie le numéro de téléphone pour qu'il soit
            dans le bon format pour les recherches
        '''
        if 'phone' in values:
            values['phone'] = re.sub('\D', '', values.get('phone', ''))

        return super(iller_partner_address, self).create(cr, uid, values, context=context)


    def write(self, cr, uid, ids, data, context={}):
        '''
            Modifie le numéro de téléphone pour qu'il soit
            dans le bon format pour les recherches
        '''
        if 'phone' in data:
            data['phone'] = re.sub('\D', '', data.get('phone', ''))

        return super(iller_partner_address, self).create(cr, uid, data, context=context)

iller_partner_address()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

