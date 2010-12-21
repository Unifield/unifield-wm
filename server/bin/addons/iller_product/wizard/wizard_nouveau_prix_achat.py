#!/usr/bin/env python
# -*- coding: UTF8 -*-

import wizard
import pooler
import time
from datetime import date
from datetime import datetime
from datetime import timedelta


_configure_form = """<?xml version="1.0" encoding="utf-8" ?>
<form string="Saisie des nouveaux prix d'achat">
    <separator colspan="4" string="Informations Generales" />
    <field name="start_date" colspan="2" required="1" />
    <separator colspan="4" />
    <field name="products" nolabel="1" colspan="4" width="1000" height="450" />
</form>"""


_configure_fields = {
        'start_date': {'type': 'date', 'required': True, 'string': 'Date de debut de validite'},
        'products': {'type': 'one2many', 'relation': 'product.nouveau.prix.achat', 'string': 'Produits'},
    }


_error_product_form = """<?xml version="1.0" encoding="utf-8" ?>
    <form string="Erreur sur les produits">
    <label colspan="4" string="Vous devez au moins saisir un produit et un prix !" />
    </form>
"""


class wizard_nouveau_prix_achat(wizard.interface):

    def _valid_form(self, cr, uid, data, args, context={}):
        '''
            Vérifie qu'au moins un produit est fourni pour le tarif
        '''
        if len(data['form']['products']) == 0:
            return 'error_product'
        return 'create'

    def _create_nouveau_prix_achat(self, cr, uid, data, args, context={}):
        '''
            Créer les différentes versions et lignes de prix
        '''
        product_obj =  pooler.get_pool(cr.dbname).get('product.product')
        product_price_history_obj =  pooler.get_pool(cr.dbname).get('product.price.history')
        products = data['form']['products']
        for product in products:
            nouveau_prix_achat = product[2].get('nouveau_prix_achat'),
            # remarque: nouveau_prix_achat est un TUPLE
            product_id = product[2].get('product_id')
            prod = product_obj.browse(cr, uid, product_id)
            # Mise à jour du tableau de l'historique des prix
            product_price_history_id = product_price_history_obj.create(cr, uid, 
                                         {
                                         'name'         : data['form']['start_date'],
                                         'nouveau_prix_achat' : nouveau_prix_achat[0],
                                         'nouveau_prix_vente': nouveau_prix_achat[0] * prod.coeff_depart,
                                         'product_id'         : product_id,
                                          }, 
                                          context=context)
            product_obj.write(cr, uid, [product_id], {
                                                     'prix_achat'    : nouveau_prix_achat[0],
                                                     'price_history' : [(4, product_price_history_id)],
                                                     })
        return {}

    states = {
        'init': {
            'actions': [],
            'result': {'type': 'form',
                       'arch': _configure_form,
                       'fields': _configure_fields,
                       'state': [('end', 'Annuler'),('choice', 'Valider')]},
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
                        'action': _create_nouveau_prix_achat,
                        'state': 'end'},
        }
    }

wizard_nouveau_prix_achat('nouveau.prix.achat')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

