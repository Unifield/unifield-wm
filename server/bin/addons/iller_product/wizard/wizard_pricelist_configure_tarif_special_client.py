#!/usr/bin/env python
# -*- coding: UTF8 -*-

import wizard
import pooler
import time
from datetime import date
from datetime import datetime
from datetime import timedelta


_configure_form = """<?xml version="1.0" encoding="utf-8" ?>
<form string="Configurer un tarif spécial pour un client">
    <separator colspan="4" string="Informations Generales" />
    <field name="title" colspan="4" />
    <field name="client" required="1" />
    <field name="tarif_promo"/>
    <newline/>
    <field name="start_date" required="1" />
    <field name="end_date" required="1" />
    <separator colspan="4" />
    <field name="products" nolabel="1" colspan="4" width="1000" height="450" />
</form>"""


_configure_fields = {
        'title': {'type': 'char', 'size': 64, 'string': 'Nom du tarif', 'required': True},
        'client': {'type': 'many2one', 'relation': 'res.partner', 'string': 'Client'},
        'tarif_promo': {'type': 'many2one', 'relation': 'product.pricelist', 'help': 'Si le prix promo est inférieur au prix spécial du client, on prend le prix promo', 'string': 'Tarif Promo'},
        'start_date': {'type': 'date', 'required': True, 'string': 'Date de debut'},
        'end_date': {'type': 'date', 'required': True, 'string': 'Date de fin'},
        'products': {'type': 'one2many', 'relation': 'product.tarif.special.client', 'string': 'Produits'},
    }

_error_date_form = """<?xml version="1.0" encoding="utf-8" ?>
    <form string="Erreur sur les dates">
        <label colspan="4" string="La date de debut doit etre inferieure a la date de fin" />
    </form>
"""

_error_product_form = """<?xml version="1.0" encoding="utf-8" ?>
    <form string="Erreur sur les produits">
    <label colspan="4" string="Vous devez au moins introduire un produit dans le tarif !" />
    </form>
"""


class wizard_configure_tarif_special_client(wizard.interface):


    def _valid_form(self, cr, uid, data, args, context={}):
        '''
            Vérifie que la date de début est inférieur à la date de fin
            et qu'au moins un produit est fourni pour le tarif
        '''
        if data['form']['start_date'] > data['form']['end_date']:
            return 'error_date'
        if len(data['form']['products']) == 0:
            return 'error_product'
        return 'create'



    def _define_tarif_special_client(self, cr, uid, data, pricelist_id, context):
        '''
            Créé la nouvelle version de liste de prix correspondant au tarif spécial pour
            la liste de prix
        '''
        version_obj = pooler.get_pool(cr.dbname).get('product.pricelist.version')
        item_obj = pooler.get_pool(cr.dbname).get('product.pricelist.item')

        name = data['form']['title']
        end_date = data['form']['end_date']
        start_date = data['form']['start_date']

        ## La version précédente s'arrête à j-1 du début du tarif spécial
        n_end_date = (datetime.strptime(end_date, '%Y-%m-%d')+timedelta(days=1)).strftime('%Y-%m-%d')
        ## La version précédente démarre à j+1 de la fin du tarif spécial
        n_start_date = (datetime.strptime(start_date, '%Y-%m-%d')-timedelta(days=1)).strftime('%Y-%m-%d')


        ## On cherche la version de base
        base_version = False
        base_ids = version_obj.search(cr, uid, [('pricelist_id', '=', pricelist_id), ('base_ok', '=', True)])
        if not base_ids:
            base_ids = version_obj.search(cr, uid, [('pricelist_id', '=', pricelist_id)])
            if not base_ids:
                return False
        base_version = base_ids[0]

        # On cherche si le tarif englobe une ou plusieurs promos existantes
        included_ids = version_obj.search(cr, uid, [('pricelist_id', '=', pricelist_id), \
                                                    ('date_end', '<=', end_date), \
                                                    ('date_start', '>=', start_date)])
        if included_ids:
            for included_id in included_ids:
                version_obj.unlink(cr, uid, [included_id])

        ## On cherche si le tarif se situe à l'intérieur d'une version existante
        version_ids = version_obj.search(cr, uid, [('pricelist_id', '=', pricelist_id), \
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

        ## On cherche si le tarif est à cheval sur deux versions existantes
        else:
            before_ids = version_obj.search(cr, uid, [('pricelist_id', '=', pricelist_id), \
                                                      ('date_start', '<', start_date), \
                                                      ('date_end', '>', start_date), \
                                                      ('date_end', '<', end_date)])
            after_ids = version_obj.search(cr, uid, [('pricelist_id', '=', pricelist_id), \
                                                     ('date_end', '>', end_date), \
                                                     ('date_start', '<', end_date), \
                                                     ('date_start', '>', start_date)])
            if before_ids:
                version_obj.write(cr, uid, before_ids, {'date_end': n_start_date})
            if after_ids:
                version_obj.write(cr, uid, after_ids, {'date_start': n_end_date})

        return version_obj.copy(cr, uid, base_version, {'date_start': start_date, 
                                                        'date_end': end_date, 
                                                        'base_ok': False,
                                                        'name': name} )


    def _create_item(self, cr, uid, data, version_id):
        '''
            Créer les différentes lignes de prix en fonction des produits
        '''
        pool_obj = pooler.get_pool(cr.dbname)
        item_obj = pool_obj.get('product.pricelist.item')
        prod_obj = pool_obj.get('product.product')

        products = data['form']['products']

        base = 1
        items = []
        type_ids = pool_obj.get('product.price.type').search(cr, uid, [('name', '=', 'Prix Special')])
        if type_ids:
            base = type_ids[0]

        for product in products:
            product_id = product[2].get('product_id')
            p_data = prod_obj.read(cr, uid, product_id, ['name'])
# La règle standard est: Prix de vente = Prix de base * (1 + coeff) + surcharge
# Pour un tarif spécial, le coeff vaut -1 est la surcharge est égale au prix spécial
# Donc Prix de vente = Prix de base * (1-1) + prix spécial = prix spécial
# Le prix de base importe peu car il n'intervient pas dans le calcul
            item_id = item_obj.create(cr, uid, {'sequence': 1,
                                                'name': p_data.get('name'), 
                                                'product_id': product_id,
                                                'base': base,
                                                'base_pricelist_id': data['form']['tarif_promo'],
                                                'price_discount' :-1.0,
                                                'price_surcharge': product[2].get('prix_special'),
                                                'price_version_id': version_id})
            items.append(item_id)

        return items


    def _create_tarif_special_client(self, cr, uid, data, args, context={}):
        '''
            Créer les différentes versions et lignes de prix
        '''
        pool_obj = pooler.get_pool(cr.dbname)
        pricelist_obj = pool_obj.get('product.pricelist')
        version_obj = pool_obj.get('product.pricelist.version')
        client_obj = pool_obj.get('res.partner')

        ## On récupère la liste de prix associée au client et on la duplique 
        client = client_obj.browse(cr, uid, data['form']['client']) 
        pricelist_id = client.property_product_pricelist.id
        new_pricelist_id = pricelist_obj.copy(cr, uid, pricelist_id, {'name': data['form']['title'],
                                                                      'tarif_special': True,
                                                                      'tarif_promo_comparatif_id': data['form']['tarif_promo'] })

        ## On cherche la version de base pour la liste de prix
        ## On cherche la version en cours pendant la promo
        ## On lui donne une date de fin qui correspond au début-1jour de la promo

        new_version = self._define_tarif_special_client(cr, uid, data, new_pricelist_id,context)
        if new_version:
            version_obj.write(cr, uid, [new_version], {'active': True, 'name': data['form']['title']})
            new_items = self._create_item(cr, uid, data, new_version)

        # On associe la nouvelle liste de prix au client
        client_obj.write(cr, uid, client.id, {'property_product_pricelist': new_pricelist_id})

        return {}


    states = {
        'init': {
            'actions': [],
            'result': {'type': 'form',
                       'arch': _configure_form,
                       'fields': _configure_fields,
                       'state': [('end', 'Annuler'),('choice', 'Creer le tarif')]},
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
                        'action': _create_tarif_special_client,
                        'state': 'end'},
        }
    }

wizard_configure_tarif_special_client('pricelist.configure.tarif.special.client')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

