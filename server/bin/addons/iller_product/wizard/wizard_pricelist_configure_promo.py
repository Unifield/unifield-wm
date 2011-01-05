#!/usr/bin/env python
# -*- coding: UTF8 -*-

from osv import osv
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
    <field name="start_date" on_change="start_date_change(start_date,end_date)" required="1" />
    <field name="end_date" on_change="end_date_change(start_date,end_date)" required="1" />
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


class wizard_configure_promo(osv.osv):
      _name="wizard.pricelist.configure.promo"

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

wizard_configure_promo()

class wizard_configure_promo(wizard.interface):

    def _valid_form(self, cr, uid, data, args, context={}):
        '''
            Vérifie que la date de début est inférieure à la date de fin
            et qu'au moins un produit est fourni pour la promo
        '''
        if data['form']['start_date'] > data['form']['end_date']:
            return 'error_date'
        if len(data['form']['product_ids'][0][2]) < 1:
            return 'error_product'

        return 'create'


    def _define_promo(self, cr, uid, data, list, context={}):
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

        # Il reste maintenant à rajouter les produits relatifs à un éventuel tarif spécial se déroulant en même temps que la promo
        if data['form'].get('ts_products'):
            base_special = 1
            items = []
            type_ids = pool_obj.get('product.price.type').search(cr, uid, [('name', '=', 'Prix Special')])
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


    def _create_promo(self, cr, uid, data, args, context={}):
        '''
            Créer les différentes versions et lignes de prix
        '''
        pool_obj = pooler.get_pool(cr.dbname)
        pricelist_obj = pool_obj.get('product.pricelist')
        version_obj = pool_obj.get('product.pricelist.version')
        tarifs_speciaux_obj = pooler.get_pool(cr.dbname).get('product.tarifs.speciaux')

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
                version_obj.write(cr, uid, [new_version], {'active': True, 'name': data['form']['title']})
                new_items = self._create_item(cr, uid, data, new_version, 'blanche', context=context)

        for list in pricelist_obj.browse(cr, uid, jaune_ids):
            new_version = self._define_promo(cr, uid, data, list, context=context)
            if new_version:
                version_obj.write(cr, uid, [new_version], {'active': True, 'name': data['form']['title']})
                new_items = self._create_item(cr, uid, data, new_version, 'jaune',context=context)

        promo_obj = pooler.get_pool(cr.dbname).get('product.pricelist.promo')

        promo_obj.create(cr, uid, {'name': data['form']['title'],
                                   'start_date': data['form']['start_date'],
                                   'end_date': data['form']['end_date'],
                                   'product_ids': [(6,0,data['form']['product_ids'][0][2])]})

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
                 data['form']['title'] += " + " + ts.name
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
                data['form']['title'] += " + " + ts.name
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
                 data['form']['title'] += " + " + ts.name
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
               data['form']['title'] += " + " + ts.name
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

