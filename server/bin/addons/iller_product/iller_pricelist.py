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
import pooler
from datetime import date
from datetime import datetime
from datetime import timedelta

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

    def bareme_change(self, cr, uid, ids, bareme_id, base_id, context={}):
        if bareme_id:
            discount = self.pool.get('product.pricelist.bareme').read(cr, uid, bareme_id, ['valeur'], context)
            return {'value': {'price_discount': discount.get('valeur')-1}}
        else:
            price_type = self.pool.get('product.price.type').browse(cr, uid, base_id)
            if price_type.name == u'Prix Special':
               return {'value': {'price_discount': -1.0}}
            else:
               return {'value': {'price_discount': 0.0}}

product_pricelist_item()

class product_pricelist(osv.osv):
    _name = 'product.pricelist'
    _inherit = 'product.pricelist'

    _columns = {
            'promo_jaune': fields.boolean(string='Promo jaune'),
            'promo_blanche': fields.boolean(string='Promo blanche'),
            'tarif_special' : fields.boolean(string='Tarif spécial'),
            'price_discount': fields.float('Price Discount', digits=(16,6)),
	    'tarif_promo_comparatif_id':  fields.many2one('product.pricelist', 'Tarif promo à comparer',
            ondelete='cascade',
            help="Si le tarif promotionnel est moins cher que le tarif spécial, c'est lui qui sera retenu"),
    }

    def price_get (self, cr, uid, ids, prod_id, qty, partner=None, context=None):
	print "DEBUT iller_price_get, ids = %s" %ids
	# Calcul habituel du prix
	res = super(product_pricelist,self).price_get(cr, uid, ids, prod_id, qty, partner, context)

	# L'éventuel prix de Noel du produit est appliqué si la date de la commande est incluse dans la promo de Noel 
	# Remarque importante: ce prix de Noel est bien le même pour TOUS
	# Le début de la promo est le 1er décembre si ce jour tombe un lundi, sinon c'est le dernier lundi de novembre
	# La fin de la promo est le 31 décembre si ce jour est un vendredi, sinon cest le premier vendredi de l'année suivante
        if context and ('date' in context):
           date_commande = datetime.strptime(context['date'],'%Y-%m-%d')
           an = context['date'].split('-')[0]
           premier_decembre = datetime(int(an), 12, 1, 0, 0)
           jour_premier_decembre = premier_decembre.strftime("%A")
           if jour_premier_decembre == 'lundi':
                date_start = premier_decembre
           elif jour_premier_decembre == 'mardi':
                date_start = premier_decembre - timedelta(days=1)
           elif jour_premier_decembre == 'mercredi':
                date_start = premier_decembre - timedelta(days=2)
           elif jour_premier_decembre == 'jeudi':
                date_start = premier_decembre - timedelta(days=3)
           elif jour_premier_decembre == 'vendredi':
                date_start = premier_decembre - timedelta(days=4)
           elif jour_premier_decembre == 'samedi':
                date_start = premier_decembre - timedelta(days=5)
           else: 
                date_start = premier_decembre - timedelta(days=6)

           dernier_decembre = datetime(int(an), 12,31, 0, 0)
           jour_dernier_decembre = dernier_decembre.strftime("%A")
           if jour_dernier_decembre == 'vendredi':
                date_end = dernier_decembre
           elif jour_dernier_decembre == 'samedi':
                date_end = dernier_decembre + timedelta(days=6)
           elif jour_dernier_decembre == 'dimanche':
                date_end = dernier_decembre + timedelta(days=5)
           elif jour_dernier_decembre == 'lundi':
                date_end = dernier_decembre + timedelta(days=4)
           elif jour_dernier_decembre == 'mardi':
                date_end = dernier_decembre + timedelta(days=3)
           elif jour_dernier_decembre == 'mercredi':
                date_end = dernier_decembre + timedelta(days=2)
           else:    
                date_end = premier_decembre - timedelta(days=1)

           # Si on est en période de promo de Noel et que le produit a un tarif de Noel
           # alors celui-ci est retourné en priorité, sinon, on continue.
           if (date_start <= date_commande) and (date_commande <= date_end):
	      prix_decembre = self.pool.get('product.product').browse(cr,uid,prod_id).prix_decembre
              if prix_decembre:
	         res[ids[0]] = prix_decembre
                 return res

	# Ici commence le traitement très particulier des clients ayant un tarif spécial à comparer avec un promo.
	# Le tarif spécial vient d'être récupéré dans la variable res
        # On commence par récupérer la liste de prix du client et on en extrait la liste de prix des promos
        print "res initial = %s" %res
        if partner:
           client_obj = self.pool.get('res.partner')
           client = client_obj.browse(cr, uid, partner) 
   	   pricelist_initiale = client.property_product_pricelist
           if pricelist_initiale.tarif_special:
              print "CE CLIENT A UN TARIF SPECIAL"
              pricelist_promo = client.property_product_pricelist.tarif_promo_comparatif_id
              print "pricelist_promo = %s" %pricelist_promo
              if pricelist_promo:
                 print "CE TARIF SPECIAL A UNE LISTE DE PROMO"
                 # On applique la liste de prix promo au client pour pouvoir calculer le tarif promo
                 client_obj.write(cr, uid, client.id, {'property_product_pricelist': pricelist_promo.id})
                 res_promo = super(product_pricelist,self).price_get(cr, uid, [pricelist_promo.id], prod_id, qty, partner, context)
                 print "res_promo = %s" %res_promo
                 # On remet en place le tarif initial
                 client_obj.write(cr, uid, client.id, {'property_product_pricelist': pricelist_initiale.id})
	
        print "RES returned = %s" %res
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
