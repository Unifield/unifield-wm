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

class pricelist_promo_configuration(osv.osv):
    _name = 'pricelist.promo.configuration'
    _description = 'Ecran de configuration des promos'

    def create(self, cr, uid, values, context={}):
        if len(self.search(cr, uid, [])) > 0:
            raise osv.except_osv('Erreur', 'Impossible de créer une nouvelle configuration - Veuillez modifier les valeurs dans la configuration actuelle')
        return super(pricelist_promo_configuration, self).create(cr, uid, values, context=context)

    def unlink(self, cr, uid, ids, context={}):
        raise osv.except_osv('Erreur', 'Impossible de supprimer cette configuration - Veuillez modifier les valeurs dans la configuration actuelle')

        return False

    _columns = {
        'name': fields.char(size=64, string='Nom', required=True, readonly=True),
        'bareme_jaune': fields.many2one('product.pricelist.bareme', string='Barème jaune', required=True),
        'bareme_page2': fields.many2one('product.pricelist.bareme', string='Barème Page 2', required=True),
    }

pricelist_promo_configuration()


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

    def on_change_product_id (self, cr, uid, ids, prod_id=False, context={}):
        if not prod_id:
            return {}
        warning = {}
        title = False
        message = False
        promo_obj = self.pool.get('product.pricelist.promo')
        promo_ids = promo_obj.search(cr, uid, [('start_date', '>', datetime.now())])
        for promo in promo_obj.browse(cr, uid, promo_ids):
            for prod in promo.product_ids:
                if prod.product_id.id == prod_id:
                    title = ("Produit [%s]%s dans une promo") %(prod.product_id.default_code, prod.product_id.name.replace('  ',''))
                    message = "Attention ! Le produit [%s]%s fait partie de la promo %s qui commence le %s" %(prod.product_id.default_code, prod.product_id.name.replace('  ',''), promo.name, promo.start_date)
                    warning = {'title': title,
                               'message': message,}

        product = self.pool.get('product.product').browse(cr, uid, prod_id)
        return {'value': {'ancien_prix_achat' : product.prix_achat}, 'warning': warning}


product_nouveau_prix_achat()

class product_pricelist_promo(osv.osv):
    _name = 'product.pricelist.promo'
    _description = 'Promo'

    def create(self, cr, uid, vals, context=None):
        if not context:
            context={}
        seq_max = len(vals.get('product_ids', []))
        i = 0
        if 'product_ids' in vals:
            for promo_in in vals.get('product_ids', []):
                vals['product_ids'][i][2].update({'name': seq_max})
                seq_max -= 1
                i += 1
        if 'product_ids' in vals:
            for promo_in in vals.get('product_ids', []):
                vals['product2_ids'][i][2].update({'name': seq_max})
                seq_max -= 1
                i += 1
        

        return super(product_pricelist_promo, self).create(cr, uid, vals, context=context)

    _columns = {
            'name': fields.char(size=64, string='Nom', required=True),
            'start_date': fields.date(string='Date de début', required=True),
            'end_date': fields.date(string='Date de fin', required=True),
            'product_ids': fields.one2many('product.pricelist.promo.in', 
                                           'promo_id',
                                           string='Produits'),
            'product2_ids': fields.one2many('product2.pricelist.promo.in',
                                            'promo_id',
                                            string='Produits 2ème page'),
            'state': fields.selection([('draft', 'Brouillon'), ('done', 'Validée')], string='État'),
        }

    _defaults = {
        'state': lambda *a: 'draft',
    }

    def _define_promo(self, cr, uid, data, list, context={}):
        '''
            Créé la nouvelle version de liste de prix correspondant à la promo pour
            la liste de prix list
        '''
        version_obj = self.pool.get('product.pricelist.version')
        item_obj = self.pool.get('product.pricelist.item')

        name = data['form']['name']
        end_date = data['form']['end_date']
        start_date = data['form']['start_date']

        ## La version précédente s'arrête à j-1 du début de la promo
        n_end_date = (datetime.strptime(end_date, '%Y-%m-%d')+timedelta(days=1)).strftime('%Y-%m-%d')
        ## La version précédente démare à j+1 de la fin de la promo
        n_start_date = (datetime.strptime(start_date, '%Y-%m-%d')-timedelta(days=1)).strftime('%Y-%m-%d')

        ## On cherche la version de base
        base_version = False
        base_ids = version_obj.search(cr, uid, [('pricelist_id', '=', list.id), ('base_ok', '=', True)])
        if not base_ids:
            base_ids = version_obj.search(cr, uid, [('pricelist_id', '=', list.id)])
            if not base_ids:
                return False
        base_version = base_ids[0]

        # On cherche si la promo englobe une ou plusieurs promos existantes
        included_ids = version_obj.search(cr, uid, [('pricelist_id', '=', list.id), \
                                                    ('date_end', '<=', end_date), \
                                                    ('date_start', '>=', start_date)])
        if included_ids:
            for included_id in included_ids:
                version_obj.unlink(cr, uid, [included_id])

        ## On cherche si la promo se situe à l'intérieur d'une version existante
        version_ids = version_obj.search(cr, uid, [('pricelist_id', '=', list.id), \
                                                   ('date_start', '<=', start_date),\
                                                   ('date_end', '>=', end_date)])

        if version_ids:
            v_data = version_obj.read(cr, uid, version_ids[0], ['date_start', 'date_end', 'name'])
            # Si les 2 dates de début coincident, il suffit de modifier la date de début de la version qui englobe
            if v_data.get('date_start') == start_date:
               version_obj.write(cr, uid, [version_ids[0]], {'date_start': n_end_date})
            else:
                # Si les 2 dates de fin coincident, il suffit de modifier la date de fin de la version qui englobe
                if v_data.get('date_end') == end_date:
                    version_obj.write(cr, uid, [version_ids[0]], {'date_end': n_start_date})
                else:
                    # Et sinon, la version qui englobe doit être scindée en deux
                    # 1) on garde la version actuelle en en modifiant la date de fin
                    version_obj.write(cr, uid, [version_ids[0]], {'date_end': n_start_date})
                    # 2) et on crée l'autre moitié
                    next_id = version_obj.copy(cr, uid, version_ids[0], {'date_start': n_end_date,
                                                                         'date_end': v_data.get('date_end'),
                                                                         'base_ok': False,
                                                                         'name': v_data.get('name')})
                    version_obj.write(cr, uid, [next_id], {'active': True})



        ## On cherche si la promo est à cheval sur deux versions existantes
        else:
            before_ids = version_obj.search(cr, uid, [('pricelist_id', '=', list.id), \
                                                      ('date_start', '<=', start_date), \
                                                      ('date_end', '>=', start_date), \
                                                      ('date_end', '<=', end_date)])
            after_ids = version_obj.search(cr, uid, [('pricelist_id', '=', list.id), \
                                                     ('date_end', '>=', end_date), \
                                                     ('date_start', '<=', end_date), \
                                                     ('date_start', '>=', start_date)])
            if before_ids:
                version_obj.write(cr, uid, before_ids, {'date_end': n_start_date})
            if after_ids:
                version_obj.write(cr, uid, after_ids, {'date_start': n_end_date})


        return version_obj.copy(cr, uid, base_version, {'date_start': start_date, 
                                                        'date_end': end_date, 
                                                        'base_ok': False,
                                                        'name': name})


    def _create_item(self, cr, uid, data, version_id, type='blanche',context={}):
        '''
            Créer les différentes lignes de prix en fonction des produits et
            du type de promo
        '''
        item_obj = self.pool.get('product.pricelist.item')
        prod_obj = self.pool.get('product.product')
        b_conf_id = self.pool.get('pricelist.promo.configuration').search(cr, uid, [])

        product_ids = []
        product2_ids = []
        for promo_in in self.pool.get('product.pricelist.promo.in').browse(cr, uid, data['form']['product_ids']):
            product_ids.append(promo_in.product_id.id)

        for promo2_in in self.pool.get('product2.pricelist.promo.in').browse(cr, uid, data['form']['product2_ids']):
            if promo2_in.product_id.id not in product_ids:
                product2_ids.append(promo2_in.product_id.id)


        base = 1
        bareme = 15
        coeff = 1.136300
        bareme_2 = 16
        coeff2 = 1.111110

        if b_conf_id and len(b_conf_id) > 0:
            bareme2 = self.pool.get('pricelist.promo.configuration').browse(cr, uid, b_conf_id[0]).bareme_page2.id
            coeff2 = self.pool.get('pricelist.promo.configuration').browse(cr, uid, b_conf_id[0]).bareme_page2.valeur

        items = []
        
        if type == 'blanche':
            ## On recherche le type de prix qui correspond au prix
            ## promo blanche
            type_ids = self.pool.get('product.price.type').search(cr, uid, [('name', '=', 'Prix promo blanche')])
            if type_ids:
                base = type_ids[0]

            ## Si la promo est de type blanche, on applique
            ## le prix promo blanche pour chaque produit
            for product in product_ids:
                p_data = prod_obj.read(cr, uid, product, ['name'])
                item_id = item_obj.create(cr, uid, {'sequence': 3,
                                                    'name': p_data.get('name'), 
                                                    'product_id': product,
                                                    'base': base,
                                                    'price_version_id': version_id})
                items.append(item_id)

            ## On recherche le type de prix qui correspond au prix de vente classique
            type_ids = self.pool.get('product.price.type').search(cr, uid, [('name', '=', 'Public Price')])
            if type_ids:
                base = type_ids[0]

            for product2 in product2_ids:
                p_data = prod_obj.read(cr, uid, product2, ['name'])
                item_id = item_obj.create(cr, uid, {'sequence': 3,
                                                    'name': p_data.get('name'),
                                                    'product_id': product2,
                                                    'base': base,
                                                    'bareme_id': bareme2,
                                                    'price_discount': coeff2-1,
                                                    'price_version_id': version_id})
                items.append(item_id)

        elif type == 'jaune':
            ## On recherche le bareme mis dans la configuration
            b_conf_id = self.pool.get('pricelist.promo.configuration').search(cr, uid, [])
            b_conf = self.pool.get('pricelist.promo.configuration').browse(cr, uid, b_conf_id)
            coeff = b_conf[0].bareme_jaune.valeur

            ## On recherche le type de prix qui correspond au prix de vente classique
            type_ids = self.pool.get('product.price.type').search(cr, uid, [('name', '=', 'Public Price')])
            if type_ids:
                base = type_ids[0]

            ## Si la promo est de type jaune, on applique
            ## le barème c15 pour chaque produit
            for product in product_ids:
                p_data = prod_obj.read(cr, uid, product, ['name'])
                item_id = item_obj.create(cr, uid, {'sequence': 3,
                                                    'name': p_data.get('name'), 
                                                    'product_id': product,
                                                    'base': base,
                                                    'bareme_id': bareme,
                                                    'price_discount': coeff-1,
                                                    'price_version_id': version_id})
                items.append(item_id)

            for product2 in product2_ids:
                p_data = prod_obj.read(cr, uid, product2, ['name'])
                item_id = item_obj.create(cr, uid, {'sequence': 3,
                                                    'name': p_data.get('name'),
                                                    'product_id': product2,
                                                    'base': base,
                                                    'bareme_id': bareme2,
                                                    'price_discount': coeff2-1,
                                                    'price_version_id': version_id})
                items.append(item_id)

        # Il reste maintenant à rajouter les produits relatifs à un éventuel tarif spécial se déroulant en même temps que la promo
        if data['form'].get('ts_products'):
            base_special = 1
            items = []
            type_ids = self.pool.get('product.price.type').search(cr, uid, [('name', '=', 'Prix Special')])
            if type_ids:
               base_special = type_ids[0]

            for product in data['form']['ts_products']:
                prod = prod_obj.browse(cr, uid, product[2].get('product_id'))
                item_id = item_obj.create(cr, uid, {'sequence': 1,
                                                    'name': prod.name,
                                                    'product_id': prod.id,
                                                    'base': base_special,
                                                    'price_discount' :-1.0,
                                                    'price_surcharge': product[2].get('prix_special'),
                                                    'price_version_id': version_id})

        return items


    def _create_history(self, cr, uid, promo_in, data):
        p_history_obj = self.pool.get('product.price.history')
        p_history_obj.create(cr, uid, {'product_id': promo_in.product_id.id,
                                      'name': data['form']['end_date'],
                                      'nouveau_prix_achat': promo_in.product_id.prix_achat,
                                      'nouveau_prix_vente': promo_in.product_id.prix_achat*promo_in.product_id.coeff_depart,
                                     })
        p_history_obj.create(cr, uid, {'product_id': promo_in.product_id.id,
                                      'name': data['form']['start_date'],
                                      'nouveau_prix_achat': promo_in.new_prix_achat,
                                      'nouveau_prix_vente': promo_in.new_prix_achat*promo_in.product_id.coeff_depart,
                                      'comment': 'Promo \'%s\'' %data['form']['name'],
                                     })

        return True


    def _create_promo(self, cr, uid, ids, context={}):
        '''
            Créer les différentes versions et lignes de prix
        '''
        pricelist_obj = self.pool.get('product.pricelist')
        version_obj = self.pool.get('product.pricelist.version')
        tarifs_speciaux_obj = self.pool.get('product.tarifs.speciaux')
        product_ids = []
        product2_ids = []
        data = {}
        data['form'] = self.read(cr, uid, ids[0])
        for promo_in in self.pool.get('product.pricelist.promo.in').browse(cr, uid, data['form']['product_ids']):
            product_ids.append(promo_in.product_id.id)
            if promo_in.new_prix_achat and promo_in.new_prix_achat != 0.00:
                self._create_history(cr, uid, promo_in, data)
        
        ## On traite la deuxième page
        for promo2_in in self.pool.get('product2.pricelist.promo.in').browse(cr, uid, data['form']['product2_ids']):
            if promo2_in.product_id.id not in product_ids:
                product2_ids.append(promo2_in.product_id.id)
                if promo2_in.new_prix_achat and promo2_in.new_prix_achat != 0.00:
                    self._create_history(cr, uid, promo2_in, data)

        data = {}
        data['form'] = self.read(cr, uid, ids[0])

        # Sauvegarde des données saisies (il faudra les restaurer lors de la création des version contenant les cumul promo + tarifs spéciaux) 
        data_ori = data['form'].copy()

        ## On cherche les tarifs spéciaux qui pourraient se cumuler à cette promo  
        data['ts_av_ids'] = tarifs_speciaux_obj.search(cr, uid, [('start_date', '<=', data['form']['start_date']), \
                                                                 ('end_date', '>=', data['form']['start_date']), \
                                                                 ('end_date', '<=', data['form']['end_date']) ])

        data['ts_ap_ids'] = tarifs_speciaux_obj.search(cr, uid, [('end_date', '>=', data['form']['end_date']), \
                                                                 ('start_date', '<=', data['form']['end_date']), \
                                                                 ('start_date', '>=',data['form']['start_date'])])

        data['ts_pdt_ids'] = tarifs_speciaux_obj.search(cr, uid, [('end_date', '<=', data['form']['end_date']), \
                                                                  ('start_date', '>=', data['form']['start_date'])])


        data['ts_av_pdt_ap_ids'] = tarifs_speciaux_obj.search(cr, uid, [('end_date', '>=', data['form']['end_date']), \
                                                                        ('start_date', '<=', data['form']['start_date'])])
        ## On récupère toutes les listes de prix où les promos s'appliquent (promo jaune ou blanche cochée)
        blanche_ids = pricelist_obj.search(cr, uid, [('promo_blanche', '=', True), ('type', '=', 'sale')])
        jaune_ids = pricelist_obj.search(cr, uid, [('promo_jaune', '=', True), ('type', '=', 'sale')])

        ## On cherche la version de base pour la liste de prix
        ## On cherche la version en cours pendant la promo
        ## On lui donne une date de fin qui correspond au début-1jour de la promo
        for list in pricelist_obj.browse(cr, uid, blanche_ids):
#        for list in pricelist_obj.browse(cr, uid, data['ids']):
            new_version = self._define_promo(cr, uid, data, list, context=context)
            if new_version:
                version_obj.write(cr, uid, [new_version], {'active': True, 'name': data['form']['name']})
                new_items = self._create_item(cr, uid, data, new_version, 'blanche', context=context)

        for list in pricelist_obj.browse(cr, uid, jaune_ids):
            new_version = self._define_promo(cr, uid, data, list, context=context)
            if new_version:
                version_obj.write(cr, uid, [new_version], {'active': True, 'name': data['form']['name']})
                new_items = self._create_item(cr, uid, data, new_version, 'jaune',context=context)

    #        promo_obj = self.pool.get('product.pricelist.promo')
            self.write(cr, uid, ids, {'state': 'done'})

    #        promo_obj.create(cr, uid, {'name': data['form']['name'],
    #                                   'start_date': data['form']['start_date'],
    #                                   'end_date': data['form']['end_date'],
    #                                   'product_ids': [(6,0,product_ids)]})

        # OK, arrivé à ce stade, la version des promos a été mise en place et a "poussé" les autres versions
        # Il faut voir si ces promos ne sont pas à cumuler avec des tarifs spéciaux
        # Recherche de toutes les listes de prix correspondant à un tarif spécial
        ts_pl_ids = pricelist_obj.search (cr, uid, [('tarif_special', '=', True)])
         
        if data['ts_av_ids']:
             # Au départ, le tarif spécial se trouvait avant la promo tout en empiétant sur le début de celle-ci.
             # Sa date de fin a déjà été reculée de sorte que ce tarif n'empiète maintenant plus sur la promo
             # Il reste maintenant à créer une nouvelle version allant de la date de début de la promo à la date de la fin du tarif spécial
             # et contenant le cumul des produits de la promo et tous les produits du tarif spécial
             ts_av = tarifs_speciaux_obj.browse(cr, uid, data['ts_av_ids'])
             for ts in ts_av:
                 data['form'] = data_ori.copy()
                 data['form']['name'] += " + " + ts.name
                 data['form']['end_date'] = ts.end_date
                 products = []
                 # On rajoute les produits du tarif spécial
                 for product in ts.product_id:
                     products.append((0,0,{'sequence' : 1 , 'prix_vente_initial': 0.00, 'product_id': product.product_id.id, 'prix_special': product.prix_special}))
                 data['form']['ts_products'] = products
                 # Pour chaque liste de prix concernée, on crée cette nouvelle version
                 for list in ts_pl_ids:
                     # Est-ce que le client pour lequel ce tarif spécial a été défini est le même 
                     # que le client correspondant au tarif spécial que l'on se propose de traiter?
                     # Si oui, il faut cumuler tarif spécial + promo, si non, on passe au tarif spécial suivant
                     pl =  pricelist_obj.browse(cr, uid, list)
                     if ts.client.property_product_pricelist != pl:
                        continue
                     pl_version = self._define_promo(cr, uid, data, pl, context=context)
                     type_promo = False
                     if pl.promo_blanche is True:
                         type_promo = 'blanche'
                     if pl.promo_jaune is True:
                         type_promo = 'jaune'
                     if pl_version and type_promo:
                        version_obj.write(cr, uid, [pl_version], {'active': True})
                        pl_new_items = self._create_item(cr, uid, data, pl_version, type_promo, context=context)

        if data['ts_ap_ids']:
            # Au départ, le tarif spécial se trouvait après la promo tout en empiétant sur la fin de celle-ci.
            # Sa date de début a déjà été repoussée de sorte que ce tarif n'empiète maintenant plus sur la promo
            # Il reste maintenant à créer une nouvelle version allant de la date de début du tarif spécial à la date de la fin de la promo
            # et contenant le cumul des produits de la promo et tous les produits du tarif spécial
            ts_ap = tarifs_speciaux_obj.browse(cr, uid, data['ts_ap_ids'])
            for ts in ts_ap:
                data['form'] = data_ori.copy()
                data['form']['name'] += " + " + ts.name
                data['form']['start_date'] = ts.start_date
                products = []
                # On rajoute les produits du tarif spécial
                for product in ts.product_id:
                    products.append((0,0,{'sequence' : 1 , 'prix_vente_initial': 0.00, 'product_id': product.product_id.id, 'prix_special': product.prix_special}))
                data['form']['ts_products'] = products
                # Pour chaque liste de prix concernée, on crée cette nouvelle version
                for list in ts_pl_ids:
                    # Est-ce que le client pour lequel ce tarif spécial a été défini est le même 
                    # que le client correspondant au tarif spécial que l'on se propose de traiter?
                    # Si oui, il faut cumuler tarif spécial + promo, si non, on passe au tarif spécial suivant
                    pl =  pricelist_obj.browse(cr, uid, list)
                    if ts.client.property_product_pricelist != pl:
                       continue
                    pl_version = self._define_promo(cr, uid, data, pl, context=context)
                    type_promo = False
                    if pl.promo_blanche is True:
                        type_promo = 'blanche'
                    if pl.promo_jaune is True:
                        type_promo = 'jaune'
                    if pl_version and type_promo:
                       version_obj.write(cr, uid, [pl_version], {'active': True})
                       pl_new_items = self._create_item(cr, uid, data, pl_version, type_promo, context=context)

        if data['ts_pdt_ids']:
             # On a un tarif spécial  dont les dates sont comprises à l'intérieur d'une promo. Il a été supprimé.
             # Il faut le recréer en y rajoutant les produits de la promo
             ts_pdt = tarifs_speciaux_obj.browse(cr, uid, data['ts_pdt_ids'])
             for ts in ts_pdt:
                 data['form'] = data_ori.copy()
                 data['form']['name'] += " + " + ts.name
                 data['form']['start_date'] = ts.start_date
                 data['form']['end_date'] = ts.end_date
                 products = []
                 # On rajoute les produits du tarif spécial
                 for product in ts.product_id:
                     products.append((0,0,{'sequence' : 1 , 'prix_vente_initial': 0.00, 'product_id': product.product_id.id, 'prix_special': product.prix_special}))
                 data['form']['ts_products'] = products
                 # Pour chaque liste de prix concernée, on crée cette nouvelle version
                 for list in ts_pl_ids:
                     # Est-ce que le client pour lequel ce tarif spécial a été défini est le même 
                     # que le client correspondant au tarif spécial que l'on se propose de traiter?
                     # Si oui, il faut cumuler tarif spécial + promo, si non, on passe au tarif spécial suivant
                     pl =  pricelist_obj.browse(cr, uid, list)
                     if ts.client.property_product_pricelist != pl:
                        continue
                     pl_version = self._define_promo(cr, uid, data, pl, context=context)
                     type_promo = False
                     if pl.promo_blanche is True:
                        type_promo = 'blanche'
                     if pl.promo_jaune is True:
                        type_promo = 'jaune'
                     if pl_version and type_promo:
                        version_obj.write(cr, uid, [pl_version], {'active': True})
                        pl_new_items = self._create_item(cr, uid, data, pl_version, type_promo, context=context)


        if data['ts_av_pdt_ap_ids']:
           # La promo a été crée alors qu'un tarif spécial existait déjà sur la période (avant, pendant et apres). 
           # Le tarif spécial a été "coupé en deux" pour laisser la place à la promo. Il reste à inclure dans la promo les produits du tarif spécial
           ts_av_pdt_ap = tarifs_speciaux_obj.browse(cr, uid, data['ts_av_pdt_ap_ids'])
           for ts in ts_av_pdt_ap:
               data['form'] = data_ori.copy()
               data['form']['name'] += " + " + ts.name
               products = []
               # On rajoute les produits du tarif spécial
               for product in ts.product_id:
                   products.append((0,0,{'sequence' : 1 , 'prix_vente_initial': 0.00, 'product_id': product.product_id.id, 'prix_special': product.prix_special}))
               data['form']['ts_products'] = products
               for list in ts_pl_ids:
                   # Est-ce que le client pour lequel ce tarif spécial a été défini est le même 
                   # que le client correspondant au tarif spécial que l'on se propose de traiter?
                   # Si oui, il faut cumuler tarif spécial + promo, si non, on passe au tarif spécial suivant
                   pl =  pricelist_obj.browse(cr, uid, list)
                   if ts.client.property_product_pricelist != pl:
                       continue
                   pl_version = self._define_promo(cr, uid, data, pl, context=context)
                   type_promo = False
                   if pl.promo_blanche is True:
                       type_promo = 'blanche'
                   if pl.promo_jaune is True:
                       type_promo = 'jaune'
                   if pl_version and type_promo:
                      version_obj.write(cr, uid, [pl_version], {'active': True})
                      pl_new_items = self._create_item(cr, uid, data, pl_version, type_promo, context=context)

        return True


product_pricelist_promo()


class product_in_promo(osv.osv):
    _name = 'product.pricelist.promo.in'
    _description = 'Produit dans la promo'
    _order = 'name'

    def _get_prix_jaune(self, cr, uid, ids, field_name, arg, context={}):
        b_conf_id = self.pool.get('pricelist.promo.configuration').search(cr, uid, [])
        b_conf = self.pool.get('pricelist.promo.configuration').browse(cr, uid, b_conf_id)
        b_coeff = b_conf[0].bareme_jaune.valeur
        res = {}
        for promo_in in self.browse(cr, uid, ids):
            if promo_in.product_id:
                res[promo_in.id] = promo_in.product_id.list_price*b_coeff
            else:
                res[promo_in.id] = False

        return res

    def onchange_product(self, cr, uid, ids, product_id, context={}):
        v = {}
        product_obj = self.pool.get('product.product')
        if product_id:
            for p in product_obj.browse(cr, uid, [product_id]):
                v['prix_blanche'] = p.prix_blanche
                b_conf_id = self.pool.get('pricelist.promo.configuration').search(cr, uid, [])
                b_conf = self.pool.get('pricelist.promo.configuration').browse(cr, uid, b_conf_id)
                b_coeff = b_conf[0].bareme_jaune.valeur
                v['prix_jaune'] = p.list_price*b_coeff
                v['prix_achat'] = p.prix_achat
        return {'value': v}
            

    _columns = {
        'name': fields.integer(string='Séquence', readonly=True),
        'product_id': fields.many2one('product.product', string='Produit', required='1'),
        'promo_id': fields.many2one('product.pricelist.promo'),
        'prix_blanche': fields.related('product_id', 'prix_blanche', string='Prix blanche', readonly=True),
        'prix_jaune': fields.function(_get_prix_jaune, method=True, string='Prix jaune', readonly=True, store=False),
        'prix_achat': fields.related('product_id', 'prix_achat', string='Prix achat', readonly=True),
        'new_prix_achat': fields.float(digits=(16,2), string='Nouveau prix d\'achat'),
    }

product_in_promo()


class product2_in_promo(osv.osv):
    _name = 'product2.pricelist.promo.in'
    _inherit = 'product.pricelist.promo.in'

product2_in_promo()


class product_tarifs_speciaux(osv.osv):
    _name = 'product.tarifs.speciaux'
    _description = 'Tarifs Spéciaux'

    _columns = {
            'name': fields.char(size=64, string='Nom', select=1, required=True),
            'client': fields.many2one('res.partner', 'Client', select=1, required=True),
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

