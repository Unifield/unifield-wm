#!/usr/bin/env python
# -*- encoding: utf-8 -*-

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
    _name = 'sale.order.line'
    _inherit = 'sale.order.line'

  
    def create(self, cr, uid, data, context={}):
        '''
            On calcule le montant de la commission lors de la création
        '''
        if 'price_unit' in data:
            data['commission'] = self._compute_commission(cr, uid, [], data, context)

        return super(iller_commission_line, self).create(cr, uid, data, context=context)

  
    def write(self, cr, uid, ids, data, context={}):
        '''
            Si le prix unitaire a changé, on recalcule le montant de la commission
        '''
        if 'price_unit' in data:
            data['commission'] = self._compute_commission(cr, uid, ids, data, context)

        return super(iller_commission_line, self).write(cr, uid, ids, data, context=context)


    def _compute_commission(self, cr, uid, ids, data, context={}):
        '''
            Réordonne les données pour faciliter le calcul de la valeur de
            la commission et envoie ces données à la foncion de calcul
        '''
        product_obj = self.pool.get('product.product')
        
        lines = []

        if ids:
            for line in self.browse(cr, uid, ids, context=context):
                lines.append({'unit_price': line.price_unit,
                              'qty': line.product_uom_qty,
                              'order_id': line.order_id.id,
                              'name': line.product_id.name,
                              'prix_vente': line.product_id.list_price})
        
        ## On rentre les nouvelles valeurs
        for l in lines:
            if 'price_unit' in data:
                l['unit_price'] = data.get('price_unit')

            if 'product_uom_qty' in data:
                l['qty'] = data.get('product_uom_qty')

            if 'order_id' in data:
                l['order_id'] = data.get('order_id')


        if len(lines) < 1:
            product = product_obj.browse(cr, uid, data.get('product_id'))
            lines.append({'unit_price': data.get('price_unit'),
                          'qty': data.get('product_uom_qty'),
                          'name': product.name,
                          'order_id': data.get('order_id', False),
                          'prix_vente': product.list_price})

        return self.set_value_commission(cr, uid, lines, context=context)

    
    def set_value_commission(self, cr, uid, lines=[], context={}):
        '''
            Effectue le calcul des commissions dans les différents cas
            possibles.
        '''
        bareme_obj = self.pool.get('product.pricelist.bareme')
        user_obj = self.pool.get('res.users')
        role_obj = self.pool.get('res.roles')
        model_data_obj = self.pool.get('ir.model.data')
        order_obj = self.pool.get('sale.order')

        if not lines:
            return 0.00

        ## On récupère tous les barèmes
        bareme_ids = bareme_obj.search(cr, uid, [('special', '=', False)])

        bareme_below = False
        bareme_above = False

        for l in lines:
            for bareme in bareme_obj.browse(cr, uid, bareme_ids):
                ## Si le prix unitaire est égal au prix de vente du produit * le 
                ## coeficient d'un barème, on retourne la commission associée au taux du barème
                if round(bareme.valeur*l.get('prix_vente'),2) == l.get('unit_price'):
                    return bareme.taux_com*l.get('unit_price')*l.get('qty')

                if l.get('unit_price') > round(bareme.valeur*l.get('prix_vente'),2) and (not bareme_below or bareme.valeur > bareme_below.valeur):
                    bareme_below = bareme

                if l.get('unit_price') < round(bareme.valeur*l.get('prix_vente'),2) and (not bareme_above or bareme.valeur < bareme_above.valeur):
                    bareme_above = bareme

            ## Si le prix inscrit est compris dans la fourchette des barèmes
            if bareme_below and bareme_above:
                taux_comm = (bareme_below.taux_com+bareme_above.taux_com)/2
                return taux_comm*l.get('unit_price')*l.get('qty')

            ## Si le prix est supérieur au prix de vente multiplié par le plus grand coeff., le taux de commission est de 1%
            if not bareme_above:
                return l.get('unit_price')*l.get('qty')*0.01

            ## Si le prix est inférieur au prix de vente multiplié par le plus petit coeff.
            if not bareme_below:
                order = order_obj.browse(cr, uid, l.get('order_id'))
                ## On vérifie si le client ne fait pas partie de la liste des clients autorisés
                if order.partner_id.depassement:
                    return l.get('unit_price')*l.get('qty')*0.01

                ## On vérifie si le client n'est pas une collectivité
                model_data_ids = model_data_obj.search(cr, uid, [('name', '=', 'pricelist_tarif_collectivite'), ('module', '=', 'iller_product'), ('model', '=', 'product.pricelist')])
                model_datas = model_data_obj.read(cr, uid, model_data_ids, ['res_id'])
                if model_datas and len(model_datas) > 0:
                    if order.pricelist_id.id == model_datas[0].get('res_id', False):
                        return l.get('unit_price')*l.get('qty')*0.01

                ## On vérifie les droits de l'utilisateur
                model_data_ids = model_data_obj.search(cr, uid, [('name', '=', 'res_roles_super_salesman'), ('model', '=', 'res.roles')])
                model_datas = model_data_obj.read(cr, uid, model_data_ids, ['res_id'])
                if model_datas and len(model_datas) > 0:
                    user = user_obj.browse(cr, uid, uid)
                    ## Si l'utilisateur a le rôle DISTRI5
                    for role in user.roles_id:
                        if role.id == model_datas[0].get('res_id', False):
                            return l.get('unit_price')*l.get('qty')*0.01

                ## Dans tous les autres cas, on retourne une erreur
                raise osv.except_osv('Erreur', u'Vous ne pouvez pas avoir un prix unitaire inférieur au prix de vente du produit multiplié par le barème c19 -- Produit : %s' %l.get('name'))
                return False

        return res


    _columns = {
        'commission': fields.float(digits=(16,2), string='Commission', readonly=True),
    }

iller_commission_line()


class iller_sale_commission(osv.osv):
    _name = 'sale.order'
    _inherit = 'sale.order'

    def _get_commission(self, cr, uid, ids, field_name, arg, context={}):
        res = {}
        for order in self.browse(cr, uid, ids):
            res[order.id] = 0.00
            for line in order.order_line:
                res[order.id] += line.commission

        return res


    _columns = {
        'commission': fields.function(_get_commission, method=True, string='Commission', store=False, readonly=True),
    }

iller_sale_commission()


class iller_partner(osv.osv):
    _name = 'res.partner'
    _inherit = 'res.partner'

    _columns = {
        'depassement': fields.boolean(string='Dépassement autorisé ?', help='Si la case est cochée, n\'importe quel utilisateur pourra vendre un produit à ce partenaire avec un prix inférieur au plus petit barème'),
    }

    _defaults = {
        'depassement': lambda *a: False,
    }

iller_partner()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

