#!/usr/bin/env python
# -*- coding: UTF8 -*-

import wizard
import pooler
import time
from datetime import date
from datetime import datetime
from datetime import timedelta


_configure_form = """<?xml version="1.0" encoding="utf-8" ?>
<form string="Configurer une promo">
    <separator colspan="4" string="Informations Generales" />
    <field name="title" colspan="4" />
    <field name="start_date" required="1" />
    <field name="end_date" required="1" />
    <separator colspan="4" string="Produits" />
    <field name="product_ids" nolabel="1" colspan="4" width="1000" height="450" />
</form>"""


_configure_fields = {
        'title': {'type': 'char', 'size': 64, 'string': 'Nom de la promo', 'required': True},
        'start_date': {'type': 'date', 'required': True, 'string': 'Date de debut'},
        'end_date': {'type': 'date', 'required': True, 'string': 'Date de fin'},
        'product_ids': {'type': 'many2many', 'relation': 'product.product', 'string': 'Produits'},
    }

_error_date_form = """<?xml version="1.0" encoding="utf-8" ?>
    <form string="Erreur sur les dates">
        <label colspan="4" string="La date de debut doit etre inferieure a la date de fin" />
    </form>
"""

_error_product_form = """<?xml version="1.0" encoding="utf-8" ?>
    <form string="Erreur sur les produits">
    <label colspan="4" string="Vous devez au moins introduire un produit dans la promo !" />
    </form>
"""


class wizard_configure_promo(wizard.interface):


    def _valid_form(self, cr, uid, data, args, context={}):
        '''
            Vérifie que la date de début est inférieur à la date de fin
            et qu'au moins un produit est fourni pour la promo
        '''
        if data['form']['start_date'] > data['form']['end_date']:
            return 'error_date'
        if len(data['form']['product_ids'][0][2]) < 1:
            return 'error_product'

        return 'create'



    def _define_promo(self, cr, uid, data, list):
        '''
            Créé la nouvelle version de liste de prix correspondant à la promo pour
            la liste de prix list
        '''
        version_obj = pooler.get_pool(cr.dbname).get('product.pricelist.version')
        item_obj = pooler.get_pool(cr.dbname).get('product.pricelist.item')

        name = data['form']['title']
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
            if v_data.get('date_start') == start_date:
                version_obj.unlink(cr, uid, [version_ids[0]])
            else:
                version_obj.write(cr, uid, [version_ids[0]], {'date_end': n_start_date})
            next_id = version_obj.copy(cr, uid, base_version, {'date_start': n_end_date, 
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


    def _create_item(self, cr, uid, data, version_id, type='blanche'):
        '''
            Créer les différentes lignes de prix en fonction des produits et
            du type de promo
        '''
        pool_obj = pooler.get_pool(cr.dbname)
        item_obj = pool_obj.get('product.pricelist.item')
        prod_obj = pool_obj.get('product.product')
        product_ids = data['form']['product_ids'][0][2]

        base = 1
        bareme = 15
        coeff = 1.136300
        items = []
        
        if type == 'blanche':
            ## On recherche le type de prix qui correspond au prix
            ## promo blanche
            type_ids = pool_obj.get('product.price.type').search(cr, uid, [('name', '=', 'Prix promo blanche')])
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

        elif type == 'jaune':
            ## On recherche le bareme c15
            bareme_ids = pool_obj.get('product.pricelist.bareme').search(cr, uid, [('name', '=', 'c13')])
            if bareme_ids:
                bareme = bareme_ids[0]
                coeff = pool_obj.get('product.pricelist.bareme').read(cr, uid, bareme, ['valeur']).get('valeur', 1.136300)

            ## On recherche le type de prix qui correspond au prix de vente classique
            type_ids = pool_obj.get('product.price.type').search(cr, uid, [('name', '=', 'Public Price')])
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
        return items


    def _create_promo(self, cr, uid, data, args, context={}):
        '''
            Créer les différentes versions et lignes de prix
        '''
        pool_obj = pooler.get_pool(cr.dbname)
        pricelist_obj = pool_obj.get('product.pricelist')
        version_obj = pool_obj.get('product.pricelist.version')

        ## On récupère toutes les listes de prix où les promos s'appliquent (promo jaune ou blanche cochée)
        blanche_ids = pricelist_obj.search(cr, uid, [('promo_blanche', '=', True), ('type', '=', 'sale')])
        jaune_ids = pricelist_obj.search(cr, uid, [('promo_jaune', '=', True), ('type', '=', 'sale')])

        ## On cherche la version de base pour la liste de prix
        ## On cherche la version en cours pendant la promo
        ## On lui donne une date de fin qui correspond au début-1jour de la promo
        for list in pricelist_obj.browse(cr, uid, blanche_ids):
#        for list in pricelist_obj.browse(cr, uid, data['ids']):
            new_version = self._define_promo(cr, uid, data, list)
            if new_version:
                version_obj.write(cr, uid, [new_version], {'active': True, 'name': data['form']['title']})
                new_items = self._create_item(cr, uid, data, new_version, 'blanche')

        for list in pricelist_obj.browse(cr, uid, jaune_ids):
            new_version = self._define_promo(cr, uid, data, list)
            if new_version:
                version_obj.write(cr, uid, [new_version], {'active': True, 'name': data['form']['title']})
                new_items = self._create_item(cr, uid, data, new_version, 'jaune')

        promo_obj = pooler.get_pool(cr.dbname).get('product.pricelist.promo')

        print "AVANT CREATE PROMO, product_ids = %s" %data['form']['product_ids'][0][2]
        promo_obj.create(cr, uid, {'name': data['form']['title'],
                                   'start_date': data['form']['start_date'],
                                   'end_date': data['form']['end_date'],
                                   'product_ids': [(6,0,data['form']['product_ids'][0][2])]})

        return {}


    states = {
        'init': {
            'actions': [],
            'result': {'type': 'form',
                       'arch': _configure_form,
                       'fields': _configure_fields,
                       'state': [('end', 'Annuler'),('choice', 'Creer les promos')]},
        },
        'choice': {
            'actions': [],
            'result': {'type': 'choice',
                       'next_state': _valid_form,}
        },
        'error_date': {
            'actions': [],
            'result': {'type': 'form',
                       'arch': _error_date_form,
                       'fields': {},
                       'state': [('end', 'Annuler')]},
        },
        'error_product': {
            'actions': [],
            'result': {'type': 'form',
                       'arch': _error_product_form,
                       'fields': {},
                       'state': [('end', 'Annuler')]},
        },
        'create': {
            'actions': [],
            'result': {'type': 'action',
                        'action': _create_promo,
                        'state': 'end'},
        }
    }

wizard_configure_promo('pricelist.configure.promo')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

