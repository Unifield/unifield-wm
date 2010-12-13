# -*- encoding: utf-8 -*-
# EN CAS D'UPGRADE, VOIR LES REMARQUES DE TYPE "!!! ATTENTION MISE A JOUR !!!
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY ir FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from osv import fields
from osv import osv
from tools import config
from product import _common
from datetime import date
import pooler
import time

class product_pricelist_bareme(osv.osv):
    _name = 'product.pricelist.bareme'
    _description = 'Product Pricelist Bareme'

    def write(self, cr, uid, ids, vals, context={}):
        '''
            Losrque la valeur du barème change, on modifie le taux de
            multiplication de tous les éléments des listes de prix qui
            contiennent se barème.
        '''
        item_obj = self.pool.get('product.pricelist.item')
        if 'valeur' in vals:
            for id in ids:
                item_ids = item_obj.search(cr, uid, [('bareme_id', '=', id)], context=context)
                item_obj.write(cr, uid, item_ids, {'price_discount': float(vals.get('valeur'))-1})

        return super(product_pricelist_bareme, self).write(cr, uid, ids, vals, context={})

    _columns = {
        'name': fields.char(size=64, string='Nom'),
        'valeur': fields.float(digits=(16,6), string='Valeur'),
    }

product_pricelist_bareme()


class product_pricelist_version(osv.osv):
    _name = 'product.pricelist.version'
    _inherit = 'product.pricelist.version'

    _columns = {
        'base_ok': fields.boolean(string='Base ?'),
    }

product_pricelist_version()


class product_pricelist_item(osv.osv):
    _name = 'product.pricelist.item'
    _inherit = 'product.pricelist.item'


    def write(self, cr, uid, ids, vals, context={}):
        '''
            Calcul du taux de multiplication du prix en fontion du barème.
        '''
        bareme_obj = self.pool.get('product.pricelist.bareme')
        if 'bareme_id' in vals and vals['bareme_id']:
            bareme = bareme_obj.read(cr, uid, vals.get('bareme_id'), ['valeur'], context)
            vals['price_discount'] = bareme.get('valeur')-1

        return super(product_pricelist_item, self).write(cr, uid, ids, vals, context=context)

    _columns = {
        'bareme_id': fields.many2one('product.pricelist.bareme', string='Barème'),
    }

    def bareme_change(self, cr, uid, ids, bareme_id, context={}):
        if bareme_id:
            discount = self.pool.get('product.pricelist.bareme').read(cr, uid, bareme_id, ['valeur'], context)
            return {'value': {'price_discount': discount.get('valeur')-1}}

        return {'value': {}}

product_pricelist_item()


class product_pricelist(osv.osv):
    _name = 'product.pricelist'
    _inherit = 'product.pricelist'

    _columns = {
            'promo_jaune': fields.boolean(string='Promo jaune'),
            'promo_blanche': fields.boolean(string='Promo blanche'),
            'price_discount': fields.float('Price Discount', digits=(16,6)),
    }

    def price_get (self, cr, uid, ids, prod_id, qty, partner=None, context=None):
	# Calcul habituel du prix
	res = super(product_pricelist,self).price_get(cr, uid, ids, prod_id, qty, partner, context)

	# L'éventuel prix de Noel du produit est appliqué si la date de la commande est en décembre
	# Remarque importante: ce prix de Noel est bien le même pour TOUS
	mois = context['date'].split('-')[1]
	if mois == '12':
	   prix_decembre = self.pool.get('product.product').browse(cr,uid,prod_id).prix_decembre
           if prix_decembre:
	      res[ids[0]] = prix_decembre

	return res
		
product_pricelist()


class product_tarif_special_client(osv.osv):
    _name = 'product.tarif.special.client'
    _description = 'Tarif spécial pour un client'

    _columns = {
            'product_id': fields.many2one('product.product', 'Produit'),
            'prix_vente_initial': fields.float(digits=(16, int(config['price_accuracy'])), string='Prix de vente initial', readonly=True),
            'prix_special': fields.float(digits=(16, int(config['price_accuracy'])), string='Prix spécial', required=True),
    }

    def on_change_product_id (self, cr, uid, ids, prod_id=False):
        if not prod_id:
           return {}
        product = self.pool.get('product.product').browse(cr, uid, prod_id)
        return {'value': {'prix_vente_initial' : product.list_price}}


product_tarif_special_client()

class product_pricelist_promo(osv.osv):
    _name = 'product.pricelist.promo'
    _description = 'Promo'

    _columns = {
            'name': fields.char(size=64, string='Nom', required=True),
            'start_date': fields.date(string='Date de début', required=True),
            'end_date': fields.date(string='Date de fin', required=True),
            'product_ids': fields.many2many('product.product',
                                            'product_pricelist_promo_rel',
                                            'promo_id', 'product_id',
                                            string='Promo'),
        }

product_pricelist_promo()
