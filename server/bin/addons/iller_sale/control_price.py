#!/usr/bin/env python
# -*- encoding: utf-8 -*-

from osv import osv
from osv import fields


class iller_control_unit_price(osv.osv):
    _name = 'sale.order.line'
    _inherit = 'sale.order.line'

  
    def control_unit_price(self, cr, uid, lines=[], context={}):
        '''
            Contrôle que le prix unitaire saisi est dans la fourchette
            des barèmes
        '''
        bareme_obj = self.pool.get('product.pricelist.bareme')
        user_obj = self.pool.get('res.users')
        role_obj = self.pool.get('res.roles')
        model_data_obj = self.pool.get('ir.model.data')
        order_obj = self.pool.get('sale.order')
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
                ## coeficient d'un barème
                if round(bareme.valeur*l.get('prix_vente'),2) == l.get('unit_price'):
                    return l.get('unit_price'), message

                if l.get('unit_price') > round(bareme.valeur*l.get('prix_vente'),2) and (not bareme_below or bareme.valeur > bareme_below.valeur):
                    bareme_below = bareme

                if l.get('unit_price') < round(bareme.valeur*l.get('prix_vente'),2) and (not bareme_above or bareme.valeur < bareme_above.valeur):
                    bareme_above = bareme

            ## Si le prix inscrit est compris dans la fourchette des barèmes
            if (bareme_below and bareme_above) or not bareme_above:
                return l.get('unit_price'), message

            ## Si le prix est inférieur au prix de vente multiplié par le plus petit coeff.
            if not bareme_below:
                if 'order_id' in l:
                    order = order_obj.browse(cr, uid, l.get('order_id'))
                    ## On vérifie si le client ne fait pas partie de la liste des clients autorisés
                    if order.partner_id.depassement:
                        return l.get('unit_price'), message
                elif 'partner_id' in l:
                    partner = partner_obj.browse(cr, uid, l.get('partner_id'))
                    ## On vérifie si le client ne fait pas partie de la liste des clients autorisés
                    if partner.depassement:
                        return l.get('qty'), message



                ## On vérifie si le client n'est pas une collectivité
                model_data_ids = model_data_obj.search(cr, uid, [('name', '=', 'pricelist_tarif_collectivite'), ('module', '=', 'iller_product'), ('model', '=', 'product.pricelist')])
                model_datas = model_data_obj.read(cr, uid, model_data_ids, ['res_id'])
                if model_datas and len(model_datas) > 0:
                    if 'order_id' in l:
                        if order.pricelist_id.id == model_datas[0].get('res_id', False):
                            return l.get('unit_price'), message
                    elif 'pricelist_id' in l:
                        if l.get('pricelist_id') == model_datas[0].get('res_id', False):
                            return l.get('unit_price'), message


                ## On vérifie les droits de l'utilisateur
                model_data_ids = model_data_obj.search(cr, uid, [('name', '=', 'res_roles_super_salesman'), ('model', '=', 'res.roles')])
                model_datas = model_data_obj.read(cr, uid, model_data_ids, ['res_id'])
                if model_datas and len(model_datas) > 0:
                    user = user_obj.browse(cr, uid, uid)
                    ## Si l'utilisateur a le rôle DISTRI5
                    for role in user.roles_id:
                        if role.id == model_datas[0].get('res_id', False):
                            return l.get('unit_price'), 'Le prix indiqué est inférieur à ce qui est autorisé - Cependant, vos droits vous donne la possibilité de valider cette commande avec ce prix.'

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

        ## On enregistre la ligne
        lines.append({'unit_price': price_unit,
                      'qty': qty,
                      'partner_id': partner_id,
                      'pricelist_id': pricelist_id,
                      'name': product.name,
                      'prix_vente': product.list_price})

        ## On lance la vérification du prix
        res2 = self.control_unit_price(cr, uid, lines, context=context)

        ## Si le prix est inférieur et que l'on a pas les droits de surpasser, on affiche une erreur
        if not res2[0] and not product.depassement_autorise:
            return {'value': {},
                    'warning': {'title': 'Erreur !',
                                'message': 'Vous ne pourrez pas enregistrer la commande car le prix indiqué est inférieur à ce qui est autorisé.'}}
        elif res2[1] != '':
            return {'value': {},
                    'warning': {'title': 'Attention !',
                                'message': res2[1]}}
        return {'value': {}}


iller_control_unit_price()


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

