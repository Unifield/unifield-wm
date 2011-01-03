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
import time

def rounding(f, r):
    if not r:
        return f
    return round(f / r) * r

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
            if vals['bareme_id']:
               bareme = bareme_obj.read(cr, uid, vals.get('bareme_id'), ['valeur'], context)
               vals['price_discount'] = bareme.get('valeur')-1
            else:
               vals['price_discount'] = 0.0

        return super(product_pricelist_item, self).write(cr, uid, ids, vals, context=context)

    _columns = {
        'price_discount': fields.float('Price Discount', digits=(16,6)),
        'bareme_id': fields.many2one('product.pricelist.bareme', string='Barème'),
    }

    def bareme_change(self, cr, uid, ids, bareme_id, base_id, context={}):
        price_type = self.pool.get('product.price.type').browse(cr, uid, base_id)
        if bareme_id:
            if price_type.name == u'Prix Special':
               return {'value': {'bareme_id' : False, 'price_discount': -1.0}}
            else:
               discount = self.pool.get('product.pricelist.bareme').read(cr, uid, bareme_id, ['valeur'], context)
               return {'value': {'price_discount': discount.get('valeur')-1}}
        else:
            if base_id != -1 :
               if price_type.name == u'Prix Special':
                  return {'value': {'price_discount': -1.0}}
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
    }

    def price_get (self, cr, uid, ids, prod_id, qty, partner=None, context=None):
        if context and ('date' in context):
           context['datestandard'] = context['date']
	# Calcul habituel du prix 
        res = self._orig_price_get(cr, uid, ids, prod_id, qty, partner, context)

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

	return res

    def _orig_price_get(self, cr, uid, ids, prod_id, qty, partner=None, context=None):
        '''
        fonction d'orgine: ajoute juste le passage du contexte à 2 endroits
        context = {
            'uom': Unit of Measure (int),
            'partner': Partner ID (int),
            'date': Date of the pricelist (%Y-%m-%d),
            'datestandard'
        }
        '''
        context = context or {}
        currency_obj = self.pool.get('res.currency')
        product_obj = self.pool.get('product.product')
        supplierinfo_obj = self.pool.get('product.supplierinfo')
        price_type_obj = self.pool.get('product.price.type')

        if context and ('partner_id' in context):
            partner = context['partner_id']
        context['partner_id'] = partner
        date = time.strftime('%Y-%m-%d')
        if context and ('date' in context):
            date = context['date']
        result = {}
        for id in ids:
            cr.execute('SELECT * ' \
                    'FROM product_pricelist_version ' \
                    'WHERE pricelist_id = %s AND active=True ' \
                        'AND (date_start IS NULL OR date_start <= %s) ' \
                        'AND (date_end IS NULL OR date_end >= %s) ' \
                    'ORDER BY id LIMIT 1', (id, date, date))
            plversion = cr.dictfetchone()

            if not plversion:
                raise osv.except_osv(_('Warning !'),
                        _('No active version for the selected pricelist !\n' \
                                'Please create or activate one.'))

            cr.execute('SELECT id, categ_id ' \
                    'FROM product_template ' \
                    'WHERE id = (SELECT product_tmpl_id ' \
                        'FROM product_product ' \
                        'WHERE id = %s)', (prod_id,))
            tmpl_id, categ = cr.fetchone()
            categ_ids = []
            while categ:
                categ_ids.append(str(categ))
                cr.execute('SELECT parent_id ' \
                        'FROM product_category ' \
                        'WHERE id = %s', (categ,))
                categ = cr.fetchone()[0]
                if str(categ) in categ_ids:
                    raise osv.except_osv(_('Warning !'),
                            _('Could not resolve product category, ' \
                                    'you have defined cyclic categories ' \
                                    'of products!'))
            if categ_ids:
                categ_where = '(categ_id IN (' + ','.join(categ_ids) + '))'
            else:
                categ_where = '(categ_id IS NULL)'

            cr.execute(
                'SELECT i.*, pl.currency_id '
                'FROM product_pricelist_item AS i, '
                    'product_pricelist_version AS v, product_pricelist AS pl '
                'WHERE (product_tmpl_id IS NULL OR product_tmpl_id = %s) '
                    'AND (product_id IS NULL OR product_id = %s) '
                    'AND (' + categ_where + ' OR (categ_id IS NULL)) '
                    'AND price_version_id = %s '
                    'AND (min_quantity IS NULL OR min_quantity <= %s) '
                    'AND i.price_version_id = v.id AND v.pricelist_id = pl.id '
                'ORDER BY sequence LIMIT 1',
                (tmpl_id, prod_id, plversion['id'], qty))
            res = cr.dictfetchone()

            if res:
                if res['base'] == -1:
                    if not res['base_pricelist_id']:
                        price = 0.0
                    else:
                        # passage du contexte
                        price_tmp = self.price_get(cr, uid,
                                [res['base_pricelist_id']], prod_id,
                                qty,context=context)[res['base_pricelist_id']]
                        ptype_src = self.browse(cr, uid,
                                res['base_pricelist_id']).currency_id.id
                        price = currency_obj.compute(cr, uid, ptype_src,
                                res['currency_id'], price_tmp, round=False)
                elif res['base'] == -2:
                    where = []
                    if partner:
                        where = [('name', '=', partner) ]
                    sinfo = supplierinfo_obj.search(cr, uid,
                            [('product_id', '=', tmpl_id)] + where)
                    price = 0.0
                    if sinfo:
                        cr.execute('SELECT * ' \
                                'FROM pricelist_partnerinfo ' \
                                'WHERE suppinfo_id IN (' + \
                                    ','.join(map(str, sinfo)) + ') ' \
                                    'AND min_quantity <= %s ' \
                                'ORDER BY min_quantity DESC LIMIT 1', (qty,))
                        res2 = cr.dictfetchone()
                        if res2:
                            price = res2['price']
                else:
                    price_type = price_type_obj.browse(cr, uid, int(res['base']))
                    # passage du contexte
                    price = currency_obj.compute(cr, uid,
                            price_type.currency_id.id, res['currency_id'],
                            product_obj.price_get(cr, uid, [prod_id],
                                price_type.field,context=context)[prod_id], round=False)

                price_limit = price

                price = price * (1.0+(res['price_discount'] or 0.0))
                price = rounding(price, res['price_round'])
                price += (res['price_surcharge'] or 0.0)
                if res['price_min_margin']:
                    price = max(price, price_limit+res['price_min_margin'])
                if res['price_max_margin']:
                    price = min(price, price_limit+res['price_max_margin'])
            else:
                # False means no valid line found ! But we may not raise an
                # exception here because it breaks the search
                price = False
            result[id] = price
            if context and ('uom' in context):
                product = product_obj.browse(cr, uid, prod_id)
                uom = product.uos_id or product.uom_id
                result[id] = self.pool.get('product.uom')._compute_price(cr,
                        uid, uom.id, result[id], context['uom'])
        return result
		
product_pricelist()



class product_nouveau_prix_achat(osv.osv):
    _name = 'product.nouveau.prix.achat'
    _description = 'Nouveau prix d\'achat'

    _columns = {
            'product_id': fields.many2one('product.product', 'Produit'),
            'nouveau_prix_achat': fields.float(digits=(16, int(config['price_accuracy'])), string='Nouveau Prix d\'Achat', required=True),
            'ancien_prix_achat': fields.float(digits=(16, int(config['price_accuracy'])), string='Prix d\'Achat actuel', required=True),

    }

    def on_change_product_id (self, cr, uid, ids, prod_id=False):
        if not prod_id:
           return {}
        product = self.pool.get('product.product').browse(cr, uid, prod_id)
        return {'value': {'ancien_prix_achat' : product.prix_achat}}


product_nouveau_prix_achat()

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


class product_tarifs_speciaux(osv.osv):
    _name = 'product.tarifs.speciaux'
    _description = 'Tarifs Spéciaux'

    _columns = {
            'name': fields.char(size=64, string='Nom', select=1, required=True),
            'start_date': fields.date(string='Date de début', select=1, required=True),
            'end_date': fields.date(string='Date de fin', required=True),
            'product_id': fields.one2many('product.tarif.special.client',
                                          'tarif_id',
                                           string='Tarif Spécial'),
        }
product_tarifs_speciaux()


class product_tarif_special_client(osv.osv):
    _name = 'product.tarif.special.client'
    _description = 'Tarif spécial pour un client'

    _columns = {
            'product_id': fields.many2one('product.product', 'Produit'),
            'tarif_id': fields.many2one('product.tarifs.speciaux', 'Tarifs Spéciaux'),
            'prix_special': fields.float(digits=(16, int(config['price_accuracy'])), string='Prix spécial', required=True),

    }

product_tarif_special_client()


class product_tarif_special_client_wizard(osv.osv):
    _name = 'product.tarif.special.client.wizard'
    _description = 'Tarif spécial pour un client (utilisé dans wizard)'

    _columns = {
            'product_id': fields.many2one('product.product', 'Produit'),
            'tarif_id': fields.many2one('product.tarifs.speciaux', 'Tarifs Spéciaux'),
            'prix_special': fields.float(digits=(16, int(config['price_accuracy'])), string='Prix spécial', required=True),
            'prix_vente_initial': fields.float(digits=(16, int(config['price_accuracy'])), string='Prix de vente initial', readonly=True, required=True),

    }

    def on_change_product_id (self, cr, uid, ids, prod_id=False):
        if not prod_id:
           return {}
        product = self.pool.get('product.product').browse(cr, uid, prod_id)
        return {'value': {'prix_vente_initial' : product.list_price, 'categ_id': False}}

product_tarif_special_client_wizard()

