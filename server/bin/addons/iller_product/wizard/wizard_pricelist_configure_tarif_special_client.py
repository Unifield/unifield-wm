#!/usr/bin/env python
# -*- coding: UTF8 -*-

import wizard
import pooler
from datetime import datetime
from datetime import timedelta
from osv import fields, osv


_configure_form = """<?xml version="1.0" encoding="utf-8" ?>
<form string="Configurer un tarif spécial pour un client">
    <separator colspan="4" string="Informations Generales" />
    <field name="title" colspan="4" />
    <field name="client" required="1" />
    <field name="tarif_initial" help="Si un tarif est saisi, il sera pris comme base à la place du tarif existant"/>
    <newline/>
    <field name="start_date" on_change="start_date_change(start_date,end_date)" required="1" />
    <field name="end_date" on_change="end_date_change(start_date,end_date, client, tarif_initial)" required="1" />
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
        <label colspan="4" string="Le client n\'a pas pas droit au tarif spécial !" />
            </form>
            """

class wizard_configure_tarif_special_client(osv.osv):
    _name="wizard.pricelist.configure.tarif.special.client"

    def start_date_change (self, cr, uid, ids, start_date, end_date):
        if end_date is False or start_date is False:
            return {}
        if start_date > end_date:
            raise osv.except_osv( ('Attention'), ('La date de fin est inférieure à la date de départ'))
        return {}

    def end_date_change (self, cr, uid, ids, start_date, end_date, client, tarif_initial):
        if start_date is False or end_date is False:
            return {}
        if start_date > end_date:
            raise osv.except_osv( ('Attention'), ('La date de fin est inférieure à la date de départ'))
        # Arrivé ici, toutes les données ont à priori été saisies
        # On vérifie que, si au tarif initial n'a été saisi, le tarif associé au client est bien un tarif spécial
        pool_obj = pooler.get_pool(cr.dbname)
        pricelist_obj = pool_obj.get('product.pricelist')
        partner_obj = pool_obj.get('res.partner')

        if tarif_initial is False:
            partner = partner_obj.browse(cr, uid, client)
            pricelist_id = partner.property_product_pricelist.id
            if pricelist_obj.browse(cr, uid, pricelist_id).tarif_special_choice == 'non':
                raise osv.except_osv( ('Attention'), ('Le tarif de ce client n\'est pas un tarif spécial'))

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
        client = client_obj.browse(cr, uid, data['form']['client'])
        if client.tarif_special_choice == 'non':
            return 'error_pricelist'

        return 'create'


    def _redefine_existing_tarif_special_client(self, cr, uid, data, pricelist_id, context):
        '''
        Créé la nouvelle version de liste de prix avec les tarifs spéciaux 
        et "décale" les versions existantes
        '''
        pool_obj = pooler.get_pool(cr.dbname)
        version_obj = pool_obj.get('product.pricelist.version')
        pricelist_item_obj = pool_obj.get('product.pricelist.item')

        name = data['form']['title']
        end_date = data['form']['end_date']
        start_date = data['form']['start_date']

        ## La version précédente s'arrête à j-1 du début de la nouvelle version avec les prix spéciaux 
        n_end_date = (datetime.strptime(end_date, '%Y-%m-%d')+timedelta(days=1)).strftime('%Y-%m-%d')
        ## La version précédente démare à j+1 de la fin de la nouvelle version avec les prix spéciaux 
        n_start_date = (datetime.strptime(start_date, '%Y-%m-%d')-timedelta(days=1)).strftime('%Y-%m-%d')

        ## On cherche la version de base
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
        if included_ids:
            for included_id in included_ids:
                version_obj.unlink(cr, uid, [included_id])

        ## On cherche si la nouvelle version se situe à l'intérieur d'une version existante
        version_ids = version_obj.search(cr, uid, [('pricelist_id', '=', pricelist_id), \
                                                   ('date_start', '<=', start_date),\
                                                   ('date_end', '>=', end_date)])

        if version_ids:
            v_data = version_obj.read(cr, uid, version_ids[0], ['date_start', 'date_end', 'name'])
            # Si les 2 dates de début coincident, il suffit de modifier la date de début de la version qui englobe
            if v_data.get('date_start') == start_date:
                version_obj.write(cr, uid, [version_ids[0]], {'date_start': n_end_date})
                return version_obj.copy(cr, uid, version_ids[0], {'date_end': end_date,
                                                                  'date_start': start_date,
                                                                  'base_ok': False,
                                                                  'name': name})
            else:
                # Si les 2 dates de fin coincident, il suffit de modifier la date de fin de la version qui englobe
                if v_data.get('date_end') == end_date:
                    version_obj.write(cr, uid, [version_ids[0]], {'date_end': n_start_date})
                    return version_obj.copy(cr, uid, version_ids[0], {'date_end': end_date,
                                                                      'date_start': start_date,
                                                                      'base_ok': False,
                                                                      'name': name})
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
                    return version_obj.copy(cr, uid, version_ids[0], {'date_start': start_date,
                                                                      'date_end': end_date,
                                                                      'base_ok': False,
                                                                      'name': name})

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
            new_before = False
            new_after = False
            before_date_end = False
            after_date_start = False
            if before_ids:
                before_date_end = version_obj.browse(cr, uid, before_ids[0], context=context).date_end
                version_obj.write(cr, uid, before_ids, {'date_end': n_start_date})
                new_before = version_obj.copy(cr, uid, before_ids[0], {'date_start': start_date,
                                                                       'date_end': before_date_end,
                                                                       'name': name,
                                                                       'base_ok': False})
            if after_ids:
                after_date_start = version_obj.browse(cr, uid, after_ids[0], context=context).date_start
                version_obj.write(cr, uid, after_ids, {'date_start': n_end_date})
                new_after = version_obj.copy(cr, uid, after_ids[0], {'date_start': after_date_start,
                                                                     'date_end': end_date,
                                                                     'name': name,
                                                                     'base_ok': False})

            if new_before and new_after:
                new_version = version_obj.copy(cr, uid, base_version, {
                                    'date_start': (datetime.strptime(before_date_end, '%Y-%m-%d')+timedelta(days=1)).strftime('%Y-%m-%d'),
                                    'date_end': (datetime.strptime(after_date_start, '%Y-%m-%d')-timedelta(days=1)).strftime('%Y-%m-%d'),
                                    'base_ok': False,
                                    'name': name})
                return [new_version, new_before, new_after]
            elif new_before and not new_after:
                new_version = version_obj.copy(cr, uid, base_version, {
                                    'date_start': (datetime.strptime(before_date_end, '%Y-%m-%d')+timedelta(days=1)).strftime('%Y-%m-%d'),
                                    'date_end': end_date,
                                    'base_ok': False,
                                    'name': name})
                return [new_version, new_before]
            elif new_after and not new_before:
                new_version = version_obj.copy(cr, uid, base_version, {
                                    'date_start': start_date,
                                    'date_end': (datetime.strptime(after_date_start, '%Y-%m-%d')-timedelta(days=1)).strftime('%Y-%m-%d'),
                                    'base_ok': False,
                                    'name': name})
                return [new_version, new_after]

        new_version =  version_obj.copy(cr, uid, base_version, {'date_start': start_date,
                                                                'date_end': end_date,
                                                                'base_ok': False,
                                                                'name': name})

        return new_version

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
        
        tarif_spec_obj = pool_obj.get('product.tarif.special.client')

        base = 1
        base_specal = 1
        items = []
        type_ids = pool_obj.get('product.price.type').search(cr, uid, [('name', '=', 'Prix Special')])
        if type_ids:
            base_special = type_ids[0]
        if type_ids and (not 'promo' in context or context['promo'] == False):
            base = type_ids[0]
        elif type_ids and (not 'mea' in context or context['mea'] == False):
            base = type_ids[0]
        else:
            type_ids = pool_obj.get('product.price.type').search(cr, uid, [('name', '=', 'Prix promo blanche')])
            if type_ids:
                base = type_ids[0]
        
        for product in products:
            # Création des items pour un tarif spécial uniquement
            product_id = product[2].get('product_id')
            sequence = 1
            if product[2].get('sequence'):
                sequence = product[2].get('sequence')
            p_data = prod_obj.name_get(cr, uid, [product_id])
            item_ids = item_obj.search(cr, uid, [('sequence', '=', 1),
                                                 ('price_version_id', '=', version_id),
                                                 ('product_id', '=', product_id),
                                                 ('base', '=', base_special),])
            item_data = {'sequence': 1,
                         'name': p_data[0][1],
                         'product_id': product_id,
                         'base': base_special,
                         'type_tarif': 'special',
                         'price_discount' :-1.0,
                         'price_surcharge': product[2].get('prix_special'),
                         'price_version_id': version_id}

            if item_ids:
                item_obj.write(cr, uid, item_ids, item_data)
                items.extend(item_ids)
            else:
                item_id = item_obj.create(cr, uid, item_data)
                items.append(item_id)

        return items


    def _create_tarif_special_client(self, cr, uid, data, args, context={}):
        
        '''
            Créer les différentes versions et lignes de prix
        '''
        pool_obj = pooler.get_pool(cr.dbname)
        pricelist_obj = pool_obj.get('product.pricelist')
        pricelist_item_obj = pool_obj.get('product.pricelist.item')
        version_obj = pool_obj.get('product.pricelist.version')
        promo_obj = pool_obj.get('product.pricelist.promo')
        product_obj = pool_obj.get('product.product')
        client_obj = pool_obj.get('res.partner')
        mea_obj = pool_obj.get('product.pricelist.mea')

        # A priori, lorsqu'un wizard est appelé plusieurs fois, on récupère au deuxième appel le contexte
        # tel qu'on l'avait laissé au premier appel. Il faut donc le réinitialiser.
        if 'promo' in context:
            context['promo'] = False
        if 'mea' in context:
            context['mea'] = False
        # On met dans le contexte une variable indiquant qu'on est dans un tarif spécial pour indiquer à 
        # l'écriture de la liste de prix qu'on doit faire le fonctionnement par défaut (dans iller_partner/partner.py : surcharge du write)
        context['is_tarif_speciaux'] = True

        # Sauvegarde des données saisies (il faudra les restaurer lors de la création des version contenant les cumul promo + tarifs spéciaux) 
        data_ori = data['form'].copy()
        # Création de la table des tarifs spéciaux que l'on remplit avec les données saisies
        tarifs_speciaux_obj = pooler.get_pool(cr.dbname).get('product.tarifs.speciaux')
        tarif_special_client_obj = pooler.get_pool(cr.dbname).get('product.tarif.special.client')

        tarifs_speciaux_ids = tarifs_speciaux_obj.search(cr, uid, [('client', '=', data['form']['client']),
                                                                   ('name', '=', data['form']['title']),
                                                                   ('start_date', '=', data['form']['start_date']),
                                                                   ('end_date', '=', data['form']['end_date'])])
        if tarifs_speciaux_ids:
            tarifs_speciaux_id = tarifs_speciaux_ids[0]
        elif 'tarif_speciaux_id' in context:
            tarifs_speciaux_id = context['tarif_speciaux_id']
        else:
            tarifs_speciaux_id = tarifs_speciaux_obj.create(cr, uid, {
                                                                     'client': data['form']['client'],
                                                                     'name' : data['form']['title'],
                                                                     'start_date': data['form']['start_date'],
                                                                     'end_date': data['form']['end_date']
                                                                     })
        products = data['form']['products']

        for product in products:
            tarif_product = tarif_special_client_obj.search(cr, uid, [('product_id', '=', product[2].get('product_id')),
                                                                      ('tarif_id', '=', tarifs_speciaux_id),])
            if not tarif_product:
                tarif_special_client = tarif_special_client_obj.create(cr, uid, {
                                                                                'product_id': product[2].get('product_id'),
                                                                                'tarif_id' : tarifs_speciaux_id,
                                                                                'prix_special' : product[2].get('prix_special'),
                                                                                 })
      
        # Liste de stockage des items ids à insérer dans le m2o de pricelist item
        item_list = []
        ## On récupère ensuite la liste de prix initiale servant de base et on la duplique 
        ## ou alors on part de la liste de prix déjà associée au client aucune liste de prix n'a été saisie
        client = client_obj.browse(cr, uid, data['form']['client'])

        if client.tarif_special_choice == 'oui' and client.property_product_pricelist.tarif_special_choice == 'oui':
            pricelist_id = client.property_product_pricelist.id
            new_pricelist = False
        else:
            if data['form']['tarif_initial'] :
                previous_pricelist = data['form']['tarif_initial']
                pricelist_id = pricelist_obj.copy(cr, uid, data['form']['tarif_initial'], {'name': 'CSP %s %s' % (client.ref, client.name),
                                                                                            'tarif_special_choice': 'oui',
                                                                                            'promo_choice': client.promo_choice,
                                                                                            'mea_choice': client.mea_choice,
                                                                                          })
                client_obj.write(cr, uid, client.id, {'property_product_pricelist': pricelist_id}, context=context)
                new_pricelist = True
            else:
                # On récupère la liste de prix du client correspondant à ses paramètres
                if client.promo_choice == 'non' and client.mea_choice == 'non':
                    pricelist_ids = pricelist_obj.search(
                            cr, uid, [
                                        ('promo_choice', '=', client.promo_choice or 'non'),
                                        ('mea_choice', '=', client.mea_choice or 'non'),
                                        ('name', 'ilike',  client.tarif_general_choice or 'NU01')
                                    ], context=context)
                else:
                    pricelist_ids = pricelist_obj.search(
                            cr, uid, [
                                        ('tarif_choice', '=', client.tarif_choice or 'blanche'),
                                        ('promo_choice', '=', client.promo_choice or 'non'),
                                        ('mea_choice', '=', client.mea_choice or 'non'),
                                        ('name', 'ilike',  client.tarif_general_choice or 'NU01')
                                    ], context=context)
                # Si les paramètres du client sont bien paramétrés on copie la liste de prix associée
                if pricelist_ids:
                    previous_pricelist = pricelist_ids[0]
                    # On copie la liste de prix pour en créer une par rapport au tarif spécial
                    pricelist_id = pricelist_obj.copy(cr, uid, pricelist_ids[0],
                                                        {
                                                            'name': 'CSP %s %s' % (client.ref, client.name),
                                                            'tarif_special_choice': 'oui',
                                                            'promo_choice': 'non',
                                                            'mea_choice': 'non',
                                                        }, context=context)
                    client_obj.write(cr, uid, client.id, {'property_product_pricelist': pricelist_id}, context=context)
                    new_pricelist = True
                else:
                    pricelist_id = previous_pricelist = client.property_product_pricelist.id
                    new_pricelist = False
 
        new_version = version_obj.search(cr, uid, [('tarifs_specs_id', '=', tarifs_speciaux_id)], context=context)
        if new_version:
            new_items = []
            for new_vers in new_version:
                new_items += self._create_item(cr, uid, data, new_vers, context=context)
            item_list += new_items
        else:
            ## Création de la nouvelle version du tarif 
            if new_pricelist is True:
                new_versions = [self._define_new_tarif_special_client(cr, uid, data, pricelist_id,context=context)]
            else:
                new_versions = self._redefine_existing_tarif_special_client(cr, uid, data, pricelist_id, context=context)
            if isinstance(new_versions, (int, long)):
                new_versions = [new_versions]
            if new_versions:
                for new_version in new_versions:
                    version_obj.write(cr, uid, [new_version], {'active': True, 'name': data['form']['title'], 'tarifs_specs_id':tarifs_speciaux_id})
                    new_items = self._create_item(cr, uid, data, new_version, context=context)
                    item_list += new_items
                
                    all_item_id = pricelist_item_obj.search(cr, uid, [('name', '=', 'Tous les produits'), ('price_version_id', '=', [new_version])], context=context)
                    record = pricelist_item_obj.browse(cr, uid, all_item_id, context=context);
                    if record:
                        if record[0].price_version_id.pricelist_id.id != record[0].base_pricelist_id.id and new_pricelist:
                            pricelist_item_obj.write(cr, uid, record[0].id, {'base_pricelist_id': previous_pricelist})

        ## OK, arrivé à ce stade, la version des prix à tarifs spéciaux a été mise en place et a "poussé" les autres versions
        pricelist = pricelist_obj.browse(cr, uid, pricelist_id)
        # Boucle sur les produits pour pouvoir écrire le m2o de pricelist_item 
        # avec le tarif spécial client correspondant
        for product in products:
            
            # Récupération des items ids correspondant à la liste créée et le produit en cours
            item_ids = pricelist_item_obj.search(cr, uid, [
                                                            ('product_id', '=', product[2].get('product_id')),
                                                            ('id', 'in', item_list),
                                                        ], context=context)

            # Récupération du tarif special client correspondant au produit en cours et aux tarifs spéciaux
            tarif_special_id = tarif_special_client_obj.search(cr, uid, [
                                                                            ('product_id', '=', product[2].get('product_id')),
                                                                            ('tarif_id', '=', tarifs_speciaux_id),
                                                                        ], context=context)
            # Parcours des items id sélectionnés par rapport au produit 
            for item_id in item_ids:
                
                if tarif_special_id and item_id:
                    # Ecriture dans l'objet tarif spécial client des différents items ids (m2o)
                    pricelist_item_obj.write(cr, uid, item_id , {'tarif_special_id':tarif_special_id[0]}, context=context)
                    
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

