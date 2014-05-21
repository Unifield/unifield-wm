#!/usr/bin/env python
# -*- encoding: utf-8 -*-

from osv import osv
from osv import fields
import time
import re
from tools import config
from tools.translate import _

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
        Check the validity of prices on sale order lines
        '''
        comment_obj = self.pool.get('iller.sale.comment')
        
        for line in self.browse(cr, uid, ids):
            line_data = {'unit_price': data.get('price_unit', line.price_unit),
                         'qty': data.get('product_uom_qty', line.product_uom_qty),
                         'partner_id': line.order_id.partner_id.id,
                         'pricelist_id': line.order_id.pricelist_id.id,
                         'name': line.product_id.name,
                         'prix_vente': line.product_id.list_price}
            #control = self.pool.get('sale.order.line').control_unit_price(cr, uid, [line_data], context=context)
            #if not control[0] and not line.product_id.depassement_autorise and line.order_id.partner_id.ref != '160053':
            #    raise osv.except_osv('Erreur', 'Impossible d\'enregistrer la commande car le prix unitaire sur la ligne %s n\'est pas correct !' % line_data['name'])
        
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
    
    # Fonction générique permettant de récupérer le champ name d'un field.selection
    # en lui passant le nom de l'objet contenant le field.selection, le nom du champ en question
    # et la valeur étant la clé du field.selection pour laquelle on veut récupérer le nom
    # Ex : getSelectionValue(cr, uid, 'product.product', 'type_cond', product_browse.type_cond)
    def getSelectionValue(self, cr, uid, model,fieldName,field_val):
        return dict(self.pool.get(model).fields_get(cr, uid)[fieldName]['selection'])[field_val]

    def product_id_change(self, cr, uid, ids, pricelist, product, qty=0,
          uom=False, qty_uos=0, uos=False, name='', partner_id=False,
          lang=False, update_tax=True, date_order=False, packaging=False, fiscal_position=False, tournee_id=False, flag=False):
        '''
            Lors du changement de produit, on regarde si un commentaire existe déjà 
            pour ce produit et ce partenaire
        '''
        if not  partner_id:
            raise osv.except_osv(_('Aucun partenaire défini !'), _('Veuillez sélectionner un partenaire dans le formulaire de vente avant de choisir un produit !'))

        comment_obj = self.pool.get('iller.sale.comment')
        comment = ''
        res = super(iller_sale_line, self).product_id_change(cr, uid, ids, pricelist, product, qty, uom, qty_uos, uos, name, partner_id, \
                                                             lang, update_tax, date_order, packaging, fiscal_position, tournee_id, flag)

        if product and partner_id:
            comment_ids = comment_obj.search(cr, uid, [('partner_id', '=', partner_id), ('product_id', '=', product)])
            if comment_ids and len(comment_ids) > 0:
                comment = comment_obj.browse(cr, uid, comment_ids[0]).comment
        type_cond = code_affect = ''
        if uom:
            uom_record = self.pool.get('product.uom').browse(cr, uid, [uom])
            if uom_record[0].code_uom:
                type_cond = self.getSelectionValue(cr, uid, 'product.product', 'type_cond', '00%s' % (uom_record[0].code_uom,))
        if product:
            product_id = self.pool.get('product.product').browse(cr, uid, product)
            if type_cond == '':
                type_cond = self.getSelectionValue(cr, uid, 'product.product', 'type_cond', product_id.type_cond)
            code_affect = product_id.code_affectation

        res['value'].update({
            'notes': comment, 
            'type_prep': code_affect,
            'type_cond': type_cond,
            'product_uom': uom or 2,
        })
        return res

    def _get_info_order_line(self, cr, uid, ids, name, args, context=None):

        if isinstance(ids, (int, long)):
            ids = [ids]

        res = {}

        # Parcours des lignes de vente
        for line in self.browse(cr, uid, ids, context=context):

            res[line.id] = {
                    'type_prep': line.product_id.code_affectation,
                    'type_cond': self.getSelectionValue(cr, uid, 'product.product', 'type_cond', line.product_id.type_cond),
                }

        return res

    _columns = {
        'type_cond': fields.function(_get_info_order_line, type='char', method=True, string=u'Type conditionnement', readonly=True, multi='infos_order_line'),
        'type_prep': fields.function(_get_info_order_line, type='char', method=True, string=u'Type prép.', readonly=True, multi='infos_order_line'),
        'num_lot': fields.char(u'N° Lot', size=64),
        'type_tarif': fields.selection(
            selection=[
                ('normal', 'PN'),
                ('jaune', 'PJ'),
                ('blanche', 'PB'),
                ('special', 'SP'),
                ('mea', 'MEA'),
                ('decembre', 'Noel'),
            ],
            string='Type tarif',
        ),
    }

iller_sale_line()

class iller_sale(osv.osv):
    _name = 'sale.order'
    _inherit = 'sale.order'

    def onchange_partner_id(self, cr, uid, ids, part, context=None):
        
        res = super(iller_sale, self).onchange_partner_id(cr, uid, ids, part, context=context)
        
        # Vérification que ce qui est entré dans partenaire est correct
        if not isinstance(part, bool):
            partner = self.pool.get('res.partner').browse(cr, uid, part, context=context)

            val = {
                'code': partner.ref
            }
            res['value'].update(val)
        
        return res

    def _get_code_client(self, cr, uid, ids, field_name, arg, context=None):

        res = {}
        for sale_order_record in self.browse(cr, uid, ids, context=context):
            partner = sale_order_record.partner_id
            res[sale_order_record.id] = partner.ref
            
        return res



    def _amount_all(self, cr, uid, ids, field_name, arg, context):
        if isinstance(ids, (int, long)):
            ids = [ids]
        res = {}
        cur_obj = self.pool.get('res.currency')
        for order in self.browse(cr, uid, ids):
            res[order.id] = {
                'amount_untaxed': 0.0,
                'amount_tax': 0.0,
                'amount_total': 0.0,
                'frais_de_port': 0.0,
            }
            val = val1 = 0.0
            cur = order.pricelist_id.currency_id
            for line in order.order_line:
                val1 += line.price_subtotal
                val += self._amount_line_tax(cr, uid, line, context)

            res[order.id]['amount_tax'] = cur_obj.round(cr, uid, cur, val)
            res[order.id]['amount_untaxed'] = cur_obj.round(cr, uid, cur, val1)
            
            if res[order.id]['amount_untaxed'] < 50.00:
                res[order.id]['frais_de_port'] = 3.00
                res[order.id]['amount_tax'] += res[order.id]['frais_de_port'] * 0.1960
                res[order.id]['amount_total'] = res[order.id]['amount_untaxed'] + res[order.id]['amount_tax'] + res[order.id]['frais_de_port']
            else:
                res[order.id]['frais_de_port'] = 0.00
                res[order.id]['amount_total'] = res[order.id]['amount_untaxed'] + res[order.id]['amount_tax']
        return res

    def _get_order(self, cr, uid, ids, context={}):
        result = {}
        for line in self.pool.get('sale.order.line').browse(cr, uid, ids, context=context):
            result[line.order_id.id] = True
        return result.keys()

    _columns = {
        'user_id': fields.many2one('res.users', 'Salesman', states={'draft': [('readonly', False)]}, select=True, required=True),
        'code': fields.function(_get_code_client, type='char', method=True, string='Code', readonly=True),
        'frais_de_port': fields.function(_amount_all, type='float', method=True,
            string='Frais de port', digits=(3, int(config['price_accuracy'])), readonly=True,
            help='Ajout automatique de 3 euros si le montant de la commande est inférieur à 50 euros.', multi='sums'),
        ##Ajout des champs des montants de la commande pour pouvoir ajouter les frais de port
        'amount_untaxed': fields.function(_amount_all, method=True, digits=(16, int(config['price_accuracy'])), string='Untaxed Amount',
            store = {
                'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line'], 10),
                'sale.order.line': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10),
            },
            multi='sums'),
        'amount_tax': fields.function(_amount_all, method=True, digits=(16, int(config['price_accuracy'])), string='Taxes',
            store = {
                'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line'], 10),
                'sale.order.line': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10),
            },
            multi='sums'),
        'amount_total': fields.function(_amount_all, method=True, digits=(16, int(config['price_accuracy'])), string='Total',
            store = {
                'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line'], 10),
                'sale.order.line': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10),
            },
            multi='sums'),
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
            args += [('customer', '=', True), ('Active', '=', True)]
            if name:
                ## Recherche sur nom du partenaire
                name_ids = self.search(cr, uid, [('name', operator, name)] + args, limit=limit, context=context)
                for name_id in name_ids:
                    if name_id not in res:
                        res.append(name_id)
                
                ## Recherche sur nom de la rue
                street_ids = address_obj.search(cr, uid, [('street', operator, name)], limit=limit, context=context)
                for street in address_obj.browse(cr, uid, street_ids):
                    # Rajout d'une vérification sur le type de l'id, car parfois stockait "False' ==> erreur dans la requête
                    if street.partner_id.id not in res and not isinstance(street.partner_id.id, bool) and street.partner_id.active:
                        res.append(street.partner_id.id)

                ## Recherche sur nom secondaire de la rue
                street2_ids = address_obj.search(cr, uid, [('street2', operator, name)], limit=limit, context=context)
                for street2 in address_obj.browse(cr, uid, street2_ids):
                    if street2.partner_id.id not in res and not isinstance(street2.partner_id.id, bool) and street2.partner_id.active:
                        res.append(street2.partner_id.id)

                ## Recherche sur nom de la ville
                city_name = '%'+str(name)+'%'
                city_ids = address_obj.search(cr, uid, [('city', operator, city_name)], limit=limit, context=context)
                for city in address_obj.browse(cr, uid, city_ids):
                    if city.partner_id.id not in res and not isinstance(city.partner_id.id, bool) and city.partner_id.active:
                        res.append(city.partner_id.id)

                ## Recherche sur le code exact
                if not res or len(res) <1 :
                    res = self.search(cr, uid, [('ref', '=', name)] + args, limit=limit, context=context)

                ## Recherche sur le numéro de téléphone
                if not res or len(res) < 1:

                    tel = re.sub('\D', '', str(name))
                    if tel:
                        addr_ids = address_obj.search(cr, uid, [('phone', operator, tel)], limit=limit, context=context)
                        for addr in address_obj.browse(cr, uid, addr_ids):
                            if addr.partner_id and addr.partner_id.id and addr.partner_id.active and addr.partner_id.id not in res:
                                res.append(addr.partner_id.id)
            
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
            values['phone'] = re.sub('\D', '', str(values.get('phone', '')))

        return super(iller_partner_address, self).create(cr, uid, values, context=context)

    def write(self, cr, uid, ids, data, context={}):
        '''
            Modifie le numéro de téléphone pour qu'il soit
            dans le bon format pour les recherches
        '''
        if 'phone' in data:
            data['phone'] = re.sub('\D', '', str(data.get('phone', '')))

        return super(iller_partner_address, self).write(cr, uid, ids, data, context=context)

iller_partner_address()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

