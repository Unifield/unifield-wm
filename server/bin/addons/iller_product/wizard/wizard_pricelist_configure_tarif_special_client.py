#!/usr/bin/env python
# -*- coding: UTF8 -*-

import wizard
import pooler
import time
from osv import osv
from datetime import date
from datetime import datetime
from datetime import timedelta
from osv import fields,osv


_configure_form = """<?xml version="1.0" encoding="utf-8" ?>
<form string="Configurer un tarif spécial pour un client">
    <separator colspan="4" string="Informations Generales" />
    <field name="title" colspan="4" />
    <field name="client" required="1" />
    <field name="tarif_initial" help="Si un tarif est saisi, il sera pris comme base à la place du tarif existant"/>
    <newline/>
    <field name="start_date" on_change="start_date_change(start_date,end_date)" required="1" />
    <field name="end_date" on_change="end_date_change(start_date,end_date)" required="1" />
    <newline/>
    <separator colspan="4" />
    <field name="products" nolabel="1" colspan="4" width="1000" height="450" />
</form>"""


_configure_fields = {
        'title': {'type': 'char', 'size': 64, 'string': 'Nom du tarif', 'required': True},
        'client': {'type': 'many2one', 'relation': 'res.partner', 'string': 'Client'},
        'tarif_initial': {'type': 'many2one', 'relation': 'product.pricelist', 'help': 'Tarif de départ auquel se rajouteront les prix spéciaux', 'string': 'Tarif initial'},
        'start_date': {'type': 'date', 'string': 'Date de debut'},
        'end_date': {'type': 'date', 'string': 'Date de fin'},
        'products': {'type': 'one2many', 'relation': 'product.tarif.special.client.wizard', 'string': 'Produits'},
    }

_error_product_form = """<?xml version="1.0" encoding="utf-8" ?>
    <form string="Erreur sur les produits">
    <label colspan="4" string="Vous devez au moins introduire un produit dans le tarif !" />
    </form>
"""

_error_pricelist_form = """<?xml version="1.0" encoding="utf-8" ?>
    <form string="Erreur sur les tarifs">
        <label colspan="4" string="Le tarif auquel il faut rajouter ces prix n\'est pas un tarif spécial !" />
            </form>
            """

class wizard_configure_tarif_special_client(osv.osv):
      _name="wizard.pricelist.configure.tarif.special.client"

      def start_date_change (self, cr, uid, ids, start_date, end_date):
          if end_date is False:
             return {}
          if start_date > end_date:
             raise osv.except_osv( ('Attention'), ('La date de fin est inférieure à la date de départ'))
          return {}

      def end_date_change (self, cr, uid, ids, start_date, end_date):
          if start_date is False:
             return {}
          if start_date > end_date:
             raise osv.except_osv( ('Attention'), ('La date de fin est inférieure à la date de départ'))
          return {}

wizard_configure_tarif_special_client()

class wizard_configure_tarif_special_client(wizard.interface):

    def _valid_form(self, cr, uid, data, args, context={}):
        if len(data['form']['products']) == 0:
            return 'error_product'

        pool_obj = pooler.get_pool(cr.dbname)
        pricelist_obj = pool_obj.get('product.pricelist')
        client_obj = pool_obj.get('res.partner')
        # Si on ne donne pas de liste de prix, on part de celle déjà associée au client, mais
        # celle-ci doit déjà être cochée en "tarif spécial"
        if data['form']['tarif_initial'] is False:
           client = client_obj.browse(cr, uid, data['form']['client'])
           pricelist_id = client.property_product_pricelist.id
           if pricelist_obj.browse(cr, uid, pricelist_id).tarif_special is False:
               return 'error_pricelist'

        return 'create'


    def _redefine_existing_tarif_special_client(self, cr, uid, data, pricelist_id, context):
        '''
        Créé la nouvelle version de liste de prix avec les tarifs spéciaux 
        et "décale" les versions existantes
        '''
        version_obj = pooler.get_pool(cr.dbname).get('product.pricelist.version')
        item_obj = pooler.get_pool(cr.dbname).get('product.pricelist.item')

        name = data['form']['title']
        end_date = data['form']['end_date']
        start_date = data['form']['start_date']

        ## La version précédente s'arrête à j-1 du début de la nouvelle version avec les prix spéciaux 
        n_end_date = (datetime.strptime(end_date, '%Y-%m-%d')+timedelta(days=1)).strftime('%Y-%m-%d')
        ## La version précédente démare à j+1 de la fin de la nouvelle version avec les prix spéciaux 
        n_start_date = (datetime.strptime(start_date, '%Y-%m-%d')-timedelta(days=1)).strftime('%Y-%m-%d')

        ## On cherche la version de base
        base_version = False
        base_ids = version_obj.search(cr, uid, [('pricelist_id', '=', pricelist_id), ('base_ok', '=', True)])
        if not base_ids:
            base_ids = version_obj.search(cr, uid, [('pricelist_id', '=', pricelist_id)])
            if not base_ids:
                return False
        base_version = base_ids[0]

        # On cherche si la nouvelle version englobe une ou plusieurs versions existantes
        included_ids = version_obj.search(cr, uid, [('pricelist_id', '=', pricelist_id), \
                                                    ('date_end', '<=', end_date), \
                                                    ('date_start', '>=', start_date)])
        print "included_ids = %s" %included_ids
        if included_ids:
            for included_id in included_ids:
                version_obj.unlink(cr, uid, [included_id])

        ## On cherche si la nouvelle version se situe à l'intérieur d'une version existante
        version_ids = version_obj.search(cr, uid, [('pricelist_id', '=', pricelist_id), \
                                                   ('date_start', '<=', start_date),\
                                                   ('date_end', '>=', end_date)])
        print "version_ids = %s" %version_ids

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

        ## On cherche si la nouvelle version est à cheval sur deux versions existantes
        else:
            before_ids = version_obj.search(cr, uid, [('pricelist_id', '=', pricelist_id), \
                                                      ('date_start', '<=', start_date), \
                                                      ('date_end', '>=', start_date), \
                                                      ('date_end', '<=', end_date)])
            after_ids = version_obj.search(cr, uid, [('pricelist_id', '=', pricelist_id), \
                                                     ('date_end', '>=', end_date), \
                                                     ('date_start', '<=', end_date), \
                                                     ('date_start', '>=', start_date)])
            print "before_ids = %s" %before_ids
            print "after_ids = %s" %after_ids
            if before_ids:
                version_obj.write(cr, uid, before_ids, {'date_end': n_start_date})
            if after_ids:
                version_obj.write(cr, uid, after_ids, {'date_start': n_end_date})


        return version_obj.copy(cr, uid, base_version, {'date_start': start_date,
                                                        'date_end': end_date,
                                                        'base_ok': False,
                                                        'name': name})


    def _define_new_tarif_special_client(self, cr, uid, data, pricelist_id, context):
        '''
            CAS D'UN NOUVEAU TARIF: 
            Il faut créer 3 versions:
            - 1 version de base de 1900 à la date de début des tarifs spéciaux (marquée version de base)
            - 1 version pour les tarifs spéciaux en fonction des dates de début et de fin saisies
            - 1 version de base allant de la date de fin des tarifs spéciaux jusqu'à 2100
            Toutes les promos sont perdues
        '''
        version_obj = pooler.get_pool(cr.dbname).get('product.pricelist.version')
        item_obj = pooler.get_pool(cr.dbname).get('product.pricelist.item')

        name = data['form']['title']
        end_date = data['form']['end_date']
        start_date = data['form']['start_date']
        ## La version précédente s'arrête à j-1 du début de la nouvelle version avec les prix spéciaux 
        n_end_date = (datetime.strptime(end_date, '%Y-%m-%d')+timedelta(days=1)).strftime('%Y-%m-%d')
        ## La version précédente démarre à j+1 de la fin de la nouvelle version avec les prix spéciaux 
        n_start_date = (datetime.strptime(start_date, '%Y-%m-%d')-timedelta(days=1)).strftime('%Y-%m-%d')

        date_2100 = datetime(2100, 1, 1, 0, 0)
        date_1900 = datetime(1900, 1, 1, 0, 0)

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

        # Moification des dates de la version de base allant de 1900 jusqu'à la date de début des tarifs spéciaux
        v1900 = version_obj.write(cr, uid, [base_version], {
                                                   'date_start' : date_1900,
                                                   'date_end': n_start_date,
                                                   })

        # Création de la version où viendront se rajoutant les prix spéciaux
        # (cette version sera rendu active apres le retour à la routine appelante)
        version_tarif_special = version_obj.copy(cr, uid, base_version, {
                                                 'date_start': start_date,
                                                 'date_end': end_date,
                                                 'base_ok': False,
                                                 'name': name})

        # Création de la version allant de la fin des prix spéciaux à 2100
        v2100 = version_obj.copy(cr, uid, base_version, {
                                                'date_start': n_end_date,
                                                'date_end': date_2100,
                                                'base_ok': False,
                                                })
        version_obj.write(cr, uid, [v2100], {'active': True})

        return version_tarif_special


    def _create_item(self, cr, uid, data, version_id, context):
        '''
            Créer les différentes lignes de prix en fonction des produits
        '''
        pool_obj = pooler.get_pool(cr.dbname)
        item_obj = pool_obj.get('product.pricelist.item')
        prod_obj = pool_obj.get('product.product')

        products = data['form']['products']

        base = 1
        base_specal = 1
        items = []
        type_ids = pool_obj.get('product.price.type').search(cr, uid, [('name', '=', 'Prix Special')])
        if type_ids:
            base_special = type_ids[0]
        if type_ids and (not 'promo' in context or context['promo'] == False):
            base = type_ids[0]
        else:
            type_ids = pool_obj.get('product.price.type').search(cr, uid, [('name', '=', 'Prix promo blanche')])
            if type_ids:
                base = type_ids[0]

        for product in products:
# La règle standard est: Prix de vente = Prix de base * (1 + coeff) + surcharge
# Pour un tarif spécial, le coeff vaut -1 est la surcharge est égale au prix spécial
# Donc Prix de vente = Prix de base * (1-1) + prix spécial = prix spécial
# Le prix de base importe peu car il n'intervient pas dans le calcul
            if 'promo' in context and context['promo'] == True:
                # Création des items pour un cumul promo + tarif spécial
                product_id = product[2].get('product_id')
                p_data = prod_obj.read(cr, uid, product_id, ['name'])
                sequence = 1
                if product[2].get('sequence'):
                   sequence = product[2].get('sequence')
                if sequence == 1:
                   # création d'un item pour un tarif special
                   item_id = item_obj.create(cr, uid, {'sequence': sequence,
                                                       'name': p_data.get('name'),
                                                       'product_id': product_id,
                                                       'base': base_special,
                                                       'price_discount' :-1.0,
                                                       'price_surcharge': product[2].get('prix_special'),
                                                       'price_version_id': version_id})
                else:
                   # création d'un item pour une promo
                   p_data = prod_obj.read(cr, uid, product_id, ['name'])
                   item_id = item_obj.create(cr, uid, {'sequence': sequence,
                                                       'name': p_data.get('name'),
                                                       'product_id': product[2].get('product_id'),
                                                       'base': base,
                                                       'price_version_id': version_id})

            else: 
                # Création des items pour un tarif spécial uniquement
                product_id = product[2].get('product_id')
                sequence = 1
                if product[2].get('sequence'):
                    sequence = product[2].get('sequence')
                p_data = prod_obj.read(cr, uid, product_id, ['name'])
                item_id = item_obj.create(cr, uid, {'sequence': 1,
                                                    'name': p_data.get('name'), 
                                                    'product_id': product_id,
                                                    'base': base_special,
                                                    'price_discount' :-1.0,
                                                    'price_surcharge': product[2].get('prix_special'),
                                                    'price_version_id': version_id})
            items.append(item_id)

        return items


    def _create_tarif_special_client(self, cr, uid, data, args, context={}):
        '''
            Créer les différentes versions et lignes de prix
        '''
        print "==============================================="
        print "DEBUT create_tarif_special_client data = %s" %data['form']
        print "DEBUT create_tarif_special_client contex = %s" %context
        pool_obj = pooler.get_pool(cr.dbname)
        pricelist_obj = pool_obj.get('product.pricelist')
        version_obj = pool_obj.get('product.pricelist.version')
        promo_obj = pool_obj.get('product.pricelist.promo')
        product_obj = pool_obj.get('product.product')
        client_obj = pool_obj.get('res.partner')

        # A priori, lorsqu'un wizard est appelé plusieurs fois, on récupère au deuxième appel le contexte
        # tel qu'on l'avait laissé au premier appel. Il faut donc le réinitialiser.
        if 'promo' in context:
            context['promo'] = False

        # Sauvegarde des données saisies (il faudra les restaurer lors de la création des version contenant les cumul promo + tarifs spéciaux) 
        context['data_ori'] = data
        # Création de la table des tarifs spéciaux que l'on remplit avec les données saisies
        tarifs_speciaux_obj = pooler.get_pool(cr.dbname).get('product.tarifs.speciaux')
        tarif_special_client_obj = pooler.get_pool(cr.dbname).get('product.tarif.special.client')

        tarifs_speciaux_id = tarifs_speciaux_obj.create(cr, uid, {
                                                                 'name' : data['form']['title'],
                                                                 'start_date': data['form']['start_date'],
                                                                 'end_date': data['form']['end_date']
                                                                 })
        products = data['form']['products']
        for product in products:
            tarif_special_client = tarif_special_client_obj.create(cr, uid, {
                                                                            'product_id': product[2].get('product_id'),
                                                                            'tarif_id' : tarifs_speciaux_id,
                                                                            'prix_special' : product[2].get('prix_special'),
                                                                             })

        ## On cherche les promos qui pourraient se cumuler à cette version à tarifs spéciaux 
        data['form']['promo_av_ids'] = promo_obj.search(cr, uid, [('start_date', '<=', data['form']['start_date']), \
                                                  ('end_date', '>=', data['form']['start_date']), \
                                                  ('end_date', '<=', data['form']['end_date']) ])

        data['form']['promo_ap_ids'] = promo_obj.search(cr, uid, [('end_date', '>=', data['form']['end_date']), \
                                                  ('start_date', '<=', data['form']['end_date']), \
                                                  ('start_date', '>=',data['form']['start_date'])])

        data['form']['promo_pdt_ids'] = promo_obj.search(cr, uid, [('end_date', '<=', data['form']['end_date']), \
                                                                   ('start_date', '>=', data['form']['start_date'])])
        print "av_ids = %s" %data['form']['promo_av_ids']
        print "ap_ids = %s" %data['form']['promo_ap_ids']
        print "pdt_ids = %s" %data['form']['promo_pdt_ids']

        ## On récupère ensuite la liste de prix initiale servant de base et on la duplique 
        ## ou alors on part de la liste de prix déjà associée au client aucune liste de prix n'a été saisie
        client = client_obj.browse(cr, uid, data['form']['client'])
        if data['form']['tarif_initial'] :
           pricelist_id = pricelist_obj.copy(cr, uid, data['form']['tarif_initial'], {'name': data['form']['title'],
                                                                         'tarif_special': True })
           client_obj.write(cr, uid, client.id, {'property_product_pricelist': pricelist_id})
           new_pricelist = True
        else:
           pricelist_id = client.property_product_pricelist.id
           new_pricelist = False

        ## Création de la nouvelle version du tarif 
        if new_pricelist is True:
           new_version = self._define_new_tarif_special_client(cr, uid, data, pricelist_id,context=context)
        else:
           new_version = self._redefine_existing_tarif_special_client(cr, uid, data, pricelist_id,context=context)
        if new_version:
           version_obj.write(cr, uid, [new_version], {'active': True, 'name': data['form']['title']})
           new_items = self._create_item(cr, uid, data, new_version, context=context)

        ## OK, arrivé à ce stade, la version des prix à tarifs spéciaux a été mise en place et a "poussé" les autres versions
        pricelist = pricelist_obj.browse(cr, uid, pricelist_id)
        if not 'promo' in context or context['promo'] is False:
            # Si la liste de prix peut accueillier des promos, il faut y cumuler les éventuelles promos déjà existantes
            if pricelist.promo_jaune or pricelist.promo_blanche:
                if data['form']['promo_av_ids']:
                    # On a une promo qui empiètait sur le début du tarif spécial. Sa date de fin a déjà été reculée à la date de début du tarif spécial
                    # Il reste maintenant à créer une nouvelle version allant de la date de début du tarif spécial à la date initiale de fin de promo,
                    # et contenant le cumul des produits de la promo et tous les produits du tarif spécial
                    context['promo'] = True
                    data = context['data_ori']
                    data['form']['tarif_initial'] = False

                    promo_av = promo_obj.browse(cr, uid, data['form']['promo_av_ids'])
                    for promo in promo_av:
                        data['form']['title'] += " + " + promo.name
                        data['form']['end_date'] = promo.end_date
                        products = data['form']['products'] 
                        for product in promo.product_ids:
                            products.append((0,0,{'sequence' : 3, 'prix_vente_initial': 0.00, 'product_id': product.id, 'prix_special': 0.00}))
                        data['form']['products'] = products
                        pl_version = self._redefine_existing_tarif_special_client(cr, uid, data, pricelist_id, context=context)
                        if pl_version:
                            version_obj.write(cr, uid, [pl_version], {'active': True})
                            pl_new_items = self._create_item(cr, uid, data, pl_version, context=context)
                if data['form']['promo_ap_ids']:
                    # On a une promo qui empiétait sur la fin du tarif spécial. Sa date de début a déjà été repoussée à la date de fin du tarif spécial.
                    # Il reste maintenant à créer une nouvelle version allant de la date initiale de début de promo à la date de fin du tarif spécial,
                    # et contenant le cumul des produits de la promo et tous les produits du tarif spécial
                    context['promo'] = True
                    data = context['data_ori']
                    data['form']['tarif_initial'] = False

                    promo_ap = promo_obj.browse(cr, uid, data['form']['promo_ap_ids'])
                    for promo in promo_ap:
                        data['form']['title'] += " + " + promo.name
                        data['form']['start_date'] = promo.start_date
                        products = data['form']['products']
                        for product in promo.product_ids:
                            products.append((0,0,{'sequence' : 3, 'prix_vente_initial': 0.00, 'product_id': product.id, 'prix_special': 0.00}))
                        data['form']['products'] = products
                        pl_version = self._redefine_existing_tarif_special_client(cr, uid, data, pricelist_id, context=context)
                        if pl_version:
                            version_obj.write(cr, uid, [pl_version], {'active': True})
                            pl_new_items = self._create_item(cr, uid, data, pl_version, context=context)

                if data['form']['promo_pdt_ids']:
                    # On a une promo dont les dates sont comprises à l'intérieur du tarif spécial. Elle a été supprimée
                    # Il faut la recréer en y rajoutant les produits du tarif spécial
                    context['promo'] = True
                    promo_pdt = promo_obj.browse(cr, uid, data['form']['promo_pdt_ids'])
                    for promo in promo_pdt:
                        data = context['data_ori']
                        data['form']['title'] += " + " + promo.name
                        data['form']['start_date'] = promo.start_date
                        data['form']['end_date'] = promo.end_date
                        products = data['form']['products']
                        for product in promo.product_ids:
                            products.append((0,0,{'sequence' : 3 , 'prix_vente_initial': 0.00, 'product_id': product.id, 'prix_special': 0.00}))
                        data['form']['products'] = products
                        pl_version = self._redefine_existing_tarif_special_client(cr, uid, data, pricelist_id, context=context)
                        if pl_version:
                            version_obj.write(cr, uid, [pl_version], {'active': True})
                            pl_new_items = self._create_item(cr, uid, data, pl_version, context=context)

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
        'error_pricelist': {
            'actions': [],
            'result': {'type': 'form',
                       'arch': _error_pricelist_form,
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

