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
    <field name="tarif_initial"/>
    <newline/>
    <separator colspan="4" />
    <field name="products" nolabel="1" colspan="4" width="1000" height="450" />
</form>"""


_configure_fields = {
        'title': {'type': 'char', 'size': 64, 'string': 'Nom du tarif', 'required': True},
        'client': {'type': 'many2one', 'relation': 'res.partner', 'string': 'Client'},
        'tarif_initial': {'type': 'many2one', 'relation': 'product.pricelist', 'help': 'Tarif de départ auquel se rajouteront les prix spéciaux', 'string': 'Tarif initial'},
        'products': {'type': 'one2many', 'relation': 'product.tarif.special.client', 'string': 'Produits'},
    }

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
        end_date = datetime(2100, 1, 1, 0, 0)
        start_date = datetime(1900, 1, 1, 0, 0)

        ## On cherche la version de base pour ne garder que celle-la
        base_version = False
        base_ids = version_obj.search(cr, uid, [('pricelist_id', '=', pricelist_id), ('base_ok', '=', True)])
        if not base_ids:
            base_ids = version_obj.search(cr, uid, [('pricelist_id', '=', pricelist_id)])
            if not base_ids:
                return False
        base_version = base_ids[0]

        all_version_ids = version_obj.search(cr, uid, [('pricelist_id', '=', pricelist_id)])
        ## On efface toutes les versions qui ne correspondent pas a la version de base
        for version_id in all_version_ids:
            if version_id != base_version:
                version_obj.unlink(cr, uid, [version_id])

        version_obj.write(cr, uid, [base_version], {
                                                   'date_start' : start_date,
                                                   'date_end': end_date,
                                                   })
        return base_version 


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
                                                'base_pricelist_id': data['form']['tarif_initial'],
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

        ## On récupère la liste de prix initiale servant de base et on la duplique 
        client = client_obj.browse(cr, uid, data['form']['client']) 
        pricelist_id = data['form']['tarif_initial'] 
        new_pricelist_id = pricelist_obj.copy(cr, uid, pricelist_id, {'name': data['form']['title'],
                                                                      'tarif_special': True })

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

