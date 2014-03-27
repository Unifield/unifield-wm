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
from datetime import datetime
from datetime import timedelta
from wizard.wizard_pricelist_configure_tarif_special_client import wizard_configure_tarif_special_client as wiz_tarif
import time
import netsvc
from tools.translate import _

def rounding(f, r):
    if not r:
        return f
    return round(f / r) * r

class product_bareme_matrice(osv.osv):
    _name = 'product.bareme.matrice'
    _description = 'Matrice des prix pour les baremes'

    _columns = {
        'bareme_id':fields.many2one('product.pricelist.bareme', string=u'Numéro de barème', required=True),
        'valeur': fields.float(digits=(16,2), string='Nouvelle valeur'),
        'prix_produit': fields.float(digits=(16,2), string=u'Prix de départ du produit'),
    }

    _defaults = {
        'valeur': lambda *a: 0.0,
        'prix_produit': lambda *a: 0.0,
    }

product_bareme_matrice()


class product_pricelist_bareme(osv.osv):
    _name = 'product.pricelist.bareme'
    _description = 'Product Pricelist Bareme'

    def write(self, cr, uid, ids, vals, context={}):
        '''
            Losrque la valeur du barème change, on modifie le taux de
            multiplication de tous les éléments des listes de prix qui
            contiennent ce barème.
        '''
        item_obj = self.pool.get('product.pricelist.item')
        if 'valeur' in vals:
            for bareme_id in ids:
                item_ids = item_obj.search(cr, uid, [('bareme_id', '=', bareme_id)], context=context)
                item_obj.write(cr, uid, item_ids, {'price_discount': float(vals.get('valeur'))-1})

        return super(product_pricelist_bareme, self).write(cr, uid, ids, vals, context={})

    _columns = {
        'name': fields.char(size=64, string='Nom'),
        'valeur': fields.float(digits=(16,6), string='Valeur'),
        'special': fields.boolean(string='Special ?'),
        'bareme_matrice_ids': fields.one2many('product.bareme.matrice', 'bareme_id', string='Matrice des prix'),
    }

    _defaults = {
        'special': lambda *a: False,
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
    }

pricelist_promo_configuration()


class product_tarifs_speciaux(osv.osv):
    _name = 'product.tarifs.speciaux'
    _description = 'Tarifs Spéciaux'

    def write(self, cr, uid, ids, vals, context=None):
        res = False
        if 'product_id' in vals and vals['product_id']:
            obj_item = self.pool.get('product.pricelist.item')
            if not vals['product_id'][0][2]:
 
                #Recherche des items correspondant à l'id de la ligne de tarif à supprimer
                item_ids = obj_item.search(cr, uid, [('tarif_special_id', '=', vals['product_id'][0][1])], context=context)
                
                obj_item.unlink(cr, uid, item_ids, context=context)
                res = super(product_tarifs_speciaux, self).write(cr, uid, ids, vals, context=context)
            else:
                res = super(product_tarifs_speciaux, self).write(cr, uid, ids, vals, context=context)
                data = {}
                # Parcours des tarifs spéciaux
                for tarifs_spec in self.browse(cr, uid, ids, context=context):
                
                    # Parcours des lignes de tarifs
                    for product_tarif in tarifs_spec.product_id:
                        # Si la ligne de tarif n'est pas reliée à un pricelist item alors on crée la ligne de tarif spécial
                        if not product_tarif.item_id:
                            if not context:
                                context= {}
                            # Création des lignes de tarifs pour chaque nouveau produit
                            # Ajout dans le contexte de l'id de l'objet tarifs spéciaux pour indiquer au wizard
                            # les actions à faire pour ce cas spécifique
                            context['tarif_speciaux_id'] = tarifs_spec.id
                            
                            # Construction de la variable data contenant le produit à créer
                            data['form']= {
                                'end_date': tarifs_spec.end_date,
                                'title': tarifs_spec.name,
                                'client': tarifs_spec.client.id, 
                                'products': [
                                            (0, 0, {
                                                'prix_vente_initial': 0.0, 
                                                'product_id': product_tarif.product_id.id, 
                                                'prix_special': product_tarif.prix_special
                                            })
                                ], 
                                'start_date': tarifs_spec.start_date
                            }
                            
                            data['ids']= ids
                            data['report_type']= 'pdf'
                            data['model']= 'ir.ui.menu'
                            data['id']= tarifs_spec.id
                            
                            args = {}
                            #random pour générer le nom
                            import random
                            #~ random.seed(tarifs_spec.id)
                            rand_res = random.random()
                            name_random = tarifs_spec.name + str(rand_res)
                            wiz_obj = wiz_tarif(name_random)
                            wiz_tarif._create_tarif_special_client(wiz_obj, cr, uid, data, args, context=context)
                            #Suppression de la clé du dictionnaire contenant le nom du wizard
                            del netsvc.SERVICES['wizard.%s' % name_random]
                            del wiz_obj
                        else:
                            
                            #Parcours des différentes listes de prix reliées 
                            for it_id in product_tarif.item_id:
                                # On récupère le record du pricelist item relié à la ligne de tarif
                                item_record = obj_item.browse(cr, uid, it_id.id, context=context)
                                # S'il y a des différences entre la ligne de tarif et la liste de prix
                                if item_record.price_surcharge != product_tarif.prix_special or item_record.product_id.id != product_tarif.product_id.id:
                                    # On met à jour la liste de prix correspondante 
                                    obj_item.write(cr, uid, item_record.id, {  
                                                                            'product_id':product_tarif.product_id.id,
                                                                            'price_surcharge':product_tarif.prix_special,
                                                                        }, context=context)
        if not res:
            res = super(product_tarifs_speciaux, self).write(cr, uid, ids, vals, context=context)

        return res

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


class product_pricelist_version(osv.osv):
    _name = 'product.pricelist.version'
    _inherit = 'product.pricelist.version'

    _columns = {
        'base_ok': fields.boolean(string='Base ?'),
        'tarifs_specs_id': fields.many2one('product.tarifs.speciaux', string='Tarifs spéciaux', invisible=True, ondelete='cascade'),
    }

product_pricelist_version()


class product_tarif_special_client(osv.osv):
    _name = 'product.tarif.special.client'
    _description = 'Tarif spécial pour un client'
    _rec_name = 'product_id'

    _columns = {
            'product_id': fields.many2one('product.product', 'Produit'),
            'tarif_id': fields.many2one('product.tarifs.speciaux', 'Tarifs Spéciaux'),
            'item_id': fields.one2many('product.pricelist.item', 'tarif_special_id',string='Liste de vente', invisible=True),
            'prix_special': fields.float(digits=(16, int(config['price_accuracy'])), string='Prix spécial', required=True),

    }

product_tarif_special_client()


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
        'tarif_special_id': fields.many2one('product.tarif.special.client', string='Tarif spécial client', invisible=True),  
    }

    def bareme_change(self, cr, uid, ids, bareme_id, base_id, context={}):
        if not base_id:
          return {'value': {'price_discount': 0.0}}
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
            'price_discount': fields.float('Price Discount', digits=(16,6)),
            
            'tarif_special_choice': fields.selection([('oui', 'Oui'), ('non', 'Non')], string=u'Tarif spécial'),
            'mea_choice': fields.selection([('oui', 'Oui'), ('non', 'Non')], string='Mise en avant'),
            'promo_choice': fields.selection([('oui', 'Oui'), ('non', 'Non')], string='Promo'),
            'tarif_choice': fields.selection([('blanche', 'Blanche'), ('jaune', 'Jaune')], string='Tarification'),
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
            
            if partner:
                tarif_noel = self.pool.get('res.partner').browse(cr, uid, partner, context=context).prix_noel_choice
                if (date_start <= date_commande) and (date_commande <= date_end) and tarif_noel == 'oui':
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
        matrice_obj = self.pool.get('product.bareme.matrice')

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
                raise osv.except_osv(_('Attention !'),
                        _('Pas de version active pour cette liste de prix !\n' \
                                'Veuillez en créer ou en activer une.'))

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
                    raise osv.except_osv(_('Attention !'),
                            _('Ne peut pas déterminer la catégorie de produits, ' \
                                    'vous avez défini des catégories de produits cycliques !'))
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

                # Si notre list item a un bareme
                if 'bareme_id' in res and res['bareme_id']:
                    # On recherche dans la matrice s'il y a une correspondance prix départ/bareme
                    matrice_ids = matrice_obj.search(cr, uid, [('bareme_id', '=', res['bareme_id']), ('prix_produit', '=', price)], context=context)
                    # S'il y a une correspondance on applique le prix, sinon on fait le traitement par défaut
                    if matrice_ids:
                        matrice = matrice_obj.read(cr, uid, matrice_ids[0], ['valeur'], context=context)
                        price = matrice['valeur']
                    else:
                        price = price * (1.0+(res['price_discount'] or 0.0))
                else:
                    price = price * (1.0+(res['price_discount'] or 0.0))

                #Traitement spécial pour le cas RUNGIEST
                if partner:
                    partner_record = self.pool.get('res.partner').browse(cr, uid, partner, context=context)
                    #Si le partenaire est RUNGIEST
                    if  partner_record.ref == '160053' and res['price_discount'] != -1:
                        prod = product_obj.browse(cr, uid, [prod_id], context=context)
                        if prod:
                            #On récupère le produit concerné et on regarde son type d'affectation
                            price = prod[0].prix_achat
                            #Si DECP alors prix d'achat * 1.1, sinon prix d'achat * 1.05
                            if prod[0].code_affectation == 'DECP':
                                price = price * 1.14
                            else:
                                price = price * 1.07

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
        promo_ids = promo_obj.search(cr, uid, [('start_date', '>=', datetime.now())])
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
        j = 0
        if 'product_ids' in vals:
            for promo_in in vals.get('product_ids', []):
                
                vals['product_ids'][i][2].update({'name': seq_max})
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
        for promo_in in self.pool.get('product.pricelist.promo.in').browse(cr, uid, data['form']['product_ids']):
            product_ids.append((promo_in.product_id.id,promo_in.prix_jaune))

        base = 1
        bareme = 15
        coeff = 1.136300

        if b_conf_id and len(b_conf_id) > 0:
            bareme = self.pool.get('pricelist.promo.configuration').browse(cr, uid, b_conf_id[0]).bareme_jaune.id
            coeff = self.pool.get('pricelist.promo.configuration').browse(cr, uid, b_conf_id[0]).bareme_jaune.valeur

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
                p_data = prod_obj.read(cr, uid, product[0], ['name'])
                item_id = item_obj.create(cr, uid, {'sequence': 3,
                                                    'name': p_data.get('name'), 
                                                    'product_id': product[0],
                                                    'base': base,
                                                    'price_version_id': version_id})
                items.append(item_id)

        elif type == 'jaune':
            ## On recherche le bareme mis dans la configuration
            b_conf_id = self.pool.get('pricelist.promo.configuration').search(cr, uid, [])
            b_conf = self.pool.get('pricelist.promo.configuration').browse(cr, uid, b_conf_id)
            coeff = b_conf[0].bareme_jaune.valeur

            ## On recherche le type de prix qui correspond au prix de vente classique
            type_ids = self.pool.get('product.price.type').search(cr, uid, [('name', '=', 'Prix promo jaune')])
            if type_ids:
                base = type_ids[0]

            ## Si la promo est de type jaune, on applique
            ## le barème c15 pour chaque produit
            for product in product_ids:
                p_data = prod_obj.read(cr, uid, product[0], ['name'])
                if product[1]:
                    item_id = item_obj.create(cr, uid, {'sequence': 3,
                                                    'name': p_data.get('name'), 
                                                    'product_id': product[0],
                                                    'base': base,
                                                    'bareme_id': bareme,
                                                    'price_discount': -1,
                                                    'price_surcharge': product[1],
                                                    'price_version_id': version_id})
                else:
                    item_id = item_obj.create(cr, uid, {'sequence': 3,
                                                    'name': p_data.get('name'), 
                                                    'product_id': product[0],
                                                    'base': base,
                                                    'bareme_id': bareme,
                                                    'price_discount': coeff-1,
                                                    'price_version_id': version_id})
                items.append(item_id)

        return items


    def _create_history(self, cr, uid, promo_in, data):
        p_history_obj = self.pool.get('product.price.history')
        p_obj = self.pool.get('product.product')

        p_history_data1 = {'product_id': promo_in.product_id.id,
                           'name': data['form']['end_date'],
                           'nouveau_prix_achat': promo_in.product_id.prix_achat,
                           'nouveau_prix_vente': promo_in.product_id.prix_achat*promo_in.product_id.coeff_depart,
                           'nouveau_prix_blanche': promo_in.product_id.prix_achat*promo_in.product_id.coeff_blanche,
                          }
        p_history_data2 = {'product_id': promo_in.product_id.id,
                           'name': data['form']['start_date'],
                           'nouveau_prix_achat': promo_in.new_prix_achat,
                           'nouveau_prix_vente': promo_in.new_prix_achat*promo_in.product_id.coeff_depart,
                           'nouveau_prix_blanche': promo_in.product_id.prix_achat*promo_in.product_id.coeff_blanche,
                           'comment': 'Promo \'%s\'' %data['form']['name'],
                          }

        history1_ids = p_history_obj.search(cr, uid, [('product_id', '=', promo_in.product_id.id), ('name', '=', data['form']['end_date'])])
        if history1_ids and len(history1_ids) > 0:
            p_history_obj.write(cr, uid, history1_ids, p_history_data1)
        else:
            p_history_obj.create(cr, uid, p_history_data1)

        history2_ids = p_history_obj.search(cr, uid, [('product_id', '=', promo_in.product_id.id), ('name', '=', data['form']['start_date'])])
        if history2_ids and len(history2_ids) > 0:
            p_history_obj.write(cr, uid, history2_ids, p_history_data2)
        else:
            p_history_obj.create(cr, uid, p_history_data2)

        return True


    def _draft_promo(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'draft'})
        return True



    def _create_promo(self, cr, uid, ids, context={}):
        '''
            Créer les différentes versions et lignes de prix
        '''
        pricelist_obj = self.pool.get('product.pricelist')
        version_obj = self.pool.get('product.pricelist.version')
        tarifs_speciaux_obj = self.pool.get('product.tarifs.speciaux')
        product_ids = []
        data = {}
        data['form'] = self.read(cr, uid, ids[0])
        for promo_in in self.pool.get('product.pricelist.promo.in').browse(cr, uid, data['form']['product_ids']):
            product_ids.append(promo_in.product_id.id)
            if promo_in.new_prix_achat and promo_in.new_prix_achat != 0.00:
                self._create_history(cr, uid, promo_in, data)

        data = {}
        data['form'] = self.read(cr, uid, ids[0])

        # Sauvegarde des données saisies (il faudra les restaurer lors de la création des version contenant les cumul promo + tarifs spéciaux) 
        data_ori = data['form'].copy()

        blanche_ids = pricelist_obj.search(cr, uid, [('tarif_choice', '=', 'blanche'), ('type', '=', 'sale'), ('promo_choice', '=', 'oui'), ('mea_choice', '=', 'non'), ('tarif_special_choice', '=', 'non')])
        jaune_ids = pricelist_obj.search(cr, uid, [('tarif_choice', '=', 'jaune'), ('type', '=', 'sale'), ('promo_choice', '=', 'oui'), ('mea_choice', '=', 'non'), ('tarif_special_choice', '=', 'non')])
        
        ## On cherche la version de base pour la liste de prix
        ## On cherche la version en cours pendant la promo
        ## On lui donne une date de fin qui correspond au début-1jour de la promo
        for list in pricelist_obj.browse(cr, uid, blanche_ids):
            new_version = self._define_promo(cr, uid, data, list, context=context)
            if new_version:
                version_obj.write(cr, uid, [new_version], {'active': True, 'name': data['form']['name']})
                new_items = self._create_item(cr, uid, data, new_version, 'blanche', context=context)

        for list in pricelist_obj.browse(cr, uid, jaune_ids):
            new_version = self._define_promo(cr, uid, data, list, context=context)
            if new_version:
                version_obj.write(cr, uid, [new_version], {'active': True, 'name': data['form']['name']})
                new_items = self._create_item(cr, uid, data, new_version, 'jaune',context=context)

            self.write(cr, uid, ids, {'state': 'done'})

        return True

product_pricelist_promo()


class pricelist_mea_configuration(osv.osv):
    _name = 'pricelist.mea.configuration'
    _description = 'Ecran de configuration des mea'

    def create(self, cr, uid, values, context=None):
        if len(self.search(cr, uid, [])) > 0:
            raise osv.except_osv('Erreur', 'Impossible de créer une nouvelle configuration - Veuillez modifier les valeurs dans la configuration actuelle')
        return super(pricelist_mea_configuration, self).create(cr, uid, values, context=context)

    def unlink(self, cr, uid, ids, context=None):
        raise osv.except_osv('Erreur', 'Impossible de supprimer cette configuration - Veuillez modifier les valeurs dans la configuration actuelle')

        return False

    _columns = {
        'name': fields.char(size=64, string='Nom', required=True, readonly=True),
        'bareme_jaune': fields.many2one('product.pricelist.bareme', string='Barème jaune', required=True),
    }

pricelist_mea_configuration()


class product_in_promo(osv.osv):
    _name = 'product.pricelist.promo.in'
    _description = 'Produit dans la promo'
    _order = 'name'


    def onchange_prix_blanche(self, cr, uid, ids, product_id, prix_blanche, context=None):
        v = {}
        product_obj = self.pool.get('product.product')
        if product_id and prix_blanche:
            for p in product_obj.browse(cr, uid, [product_id], context=context):
                if p.prix_blanche != prix_blanche:
                    coeff_blanche = prix_blanche / p.prix_achat
                    product_obj.write(cr, uid, [p.id], {'coeff_blanche':coeff_blanche})
                v['prix_blanche'] = prix_blanche
        return {'value': v}

    def _get_prix_jaune(self, cr, uid, ids, field_name, arg, context=None):
        b_conf_id = self.pool.get('pricelist.promo.configuration').search(cr, uid, [])
        b_conf = self.pool.get('pricelist.promo.configuration').browse(cr, uid, b_conf_id)
        b_coeff = b_conf[0].bareme_jaune.valeur
        res = {}
        for promo_in in self.browse(cr, uid, ids, context=context):
            if promo_in.product_id:
                res[promo_in.id] = promo_in.product_id.prix_blanche*b_coeff
            else:
                res[promo_in.id] = False

        return res


    def _get_prix_achat(self, cr, uid, ids, field_name, arg, context={}):
        history_obj = self.pool.get('product.price.history')

        res = {}

        for pinp in self.browse(cr, uid, ids, context=context):
            history_ids = history_obj.search(cr, uid, [('product_id', '=', pinp.product_id.id), ('name', '<=', datetime.now())], 0, 1, 'name desc')
            if history_ids:
                h = history_obj.browse(cr, uid, history_ids[0], context=context)
                if not h.comment or len(h.comment) < 5 or h.comment[5:] != 'Promo':
                    res[pinp.id] = h.nouveau_prix_achat

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
                v['prix_jaune'] = p.prix_blanche*b_coeff
                v['prix_achat'] = p.prix_achat
        return {'value': v}
            

    _columns = {
        'name': fields.integer(string='Séquence', readonly=True),
        'product_id': fields.many2one('product.product', string='Produit', required='1'),
        'promo_id': fields.many2one('product.pricelist.promo', ondelete='cascade'),
        'prix_blanche': fields.related('product_id', 'prix_blanche', string='Prix blanche', readonly=True),
        'prix_jaune': fields.function(_get_prix_jaune, method=True, string='Prix jaune', readonly=True, store=False,),
        'prix_achat': fields.function(_get_prix_achat, method=True, string='Prix achat', readonly=True, store=False),
#        'prix_achat': fields.related('product_id', 'prix_achat', string='Prix achat', readonly=True),
        'new_prix_achat': fields.float(digits=(16,2), string='Nouveau prix d\'achat'),
        
    }

product_in_promo()


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

class product_pricelist_mea(osv.osv):
    _name = 'product.pricelist.mea'
    _description = 'MEA'

    def create(self, cr, uid, vals, context=None):
        if not context:
            context={}
        seq_max = len(vals.get('product_ids', []))
        i = 0
        j = 0
        if 'product_ids' in vals:
            for promo_in in vals.get('product_ids', []):
                vals['product_ids'][i][2].update({'name': seq_max})
                seq_max -= 1
                i += 1

        return super(product_pricelist_mea, self).create(cr, uid, vals, context=context)


    _columns = {
            'name': fields.char(size=64, string='Nom', required=True),
            'start_date': fields.date(string='Date de début', required=True),
            'end_date': fields.date(string='Date de fin', required=True),
            'product_ids': fields.one2many('product.pricelist.mea.in', 
                                           'promo_id',
                                           string='Produits'),
            'state': fields.selection([('draft', 'Brouillon'), ('done', 'Validée')], string='État'),
        }

    _defaults = {
        'state': lambda *a: 'draft',
    }

    def _draft_mea(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'draft'})
        return True
    def _define_mea(self, cr, uid, data, list, context={}):
        '''
            Créé la nouvelle version de liste de prix correspondant à la mea pour
            la liste de prix list
        '''
        version_obj = self.pool.get('product.pricelist.version')
        item_obj = self.pool.get('product.pricelist.item')

        name = data['form']['name']
        end_date = data['form']['end_date']
        start_date = data['form']['start_date']

        ## La version précédente s'arrête à j-1 du début de la mea
        n_end_date = (datetime.strptime(end_date, '%Y-%m-%d')+timedelta(days=1)).strftime('%Y-%m-%d')
        ## La version précédente démare à j+1 de la fin de la mea
        n_start_date = (datetime.strptime(start_date, '%Y-%m-%d')-timedelta(days=1)).strftime('%Y-%m-%d')

        ## On cherche la version de base
        base_version = False
        base_ids = version_obj.search(cr, uid, [('pricelist_id', '=', list.id), ('base_ok', '=', True)])
        if not base_ids:
            base_ids = version_obj.search(cr, uid, [('pricelist_id', '=', list.id)])
            if not base_ids:
                return False
        base_version = base_ids[0]

        # On cherche si la mea englobe une ou plusieurs promos existantes
        included_ids = version_obj.search(cr, uid, [('pricelist_id', '=', list.id), \
                                                    ('date_end', '<=', end_date), \
                                                    ('date_start', '>=', start_date)])
        if included_ids:
            for included_id in included_ids:
                version_obj.unlink(cr, uid, [included_id])

        ## On cherche si la mea se situe à l'intérieur d'une version existante
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
            du type de mea
        '''
        
        item_obj = self.pool.get('product.pricelist.item')
        prod_obj = self.pool.get('product.product')
        b_conf_id = self.pool.get('pricelist.mea.configuration').search(cr, uid, [])

        product_ids = []
        for promo_in in self.pool.get('product.pricelist.mea.in').browse(cr, uid, data['form']['product_ids']):
            product_ids.append((promo_in.product_id.id, promo_in.new_prix_jaune, promo_in.new_prix_blanche))

        base = 1
        bareme = 15
        coeff = 1.136300

        items = []
        
        if type == 'blanche':
            ## On recherche le type de prix qui correspond au prix
            ## mea blanche
            type_ids = self.pool.get('product.price.type').search(cr, uid, [('name', '=', 'Prix promo blanche')])
            if type_ids:
                base = type_ids[0]

            ## Si la mea est de type blanche, on applique
            ## le prix mea blanche pour chaque produit
            for product in product_ids:
                p_data = prod_obj.read(cr, uid, product[0], ['name'])
                if product[2]:
                    item_id = item_obj.create(cr, uid, {'sequence': 3,
                                                    'name': p_data.get('name'), 
                                                    'product_id': product[0],
                                                    'base': base,
                                                    'price_discount': -1,
                                                    'price_surcharge': product[2],
                                                    'price_version_id': version_id})
                else:
                    item_id = item_obj.create(cr, uid, {'sequence': 3,
                                                    'name': p_data.get('name'), 
                                                    'product_id': product[0],
                                                    'base': base,
                                                    'price_version_id': version_id})

                items.append(item_id)
        elif type == 'jaune':
            ## On recherche le bareme mis dans la configuration
            b_conf_id = self.pool.get('pricelist.mea.configuration').search(cr, uid, [])
            b_conf = self.pool.get('pricelist.mea.configuration').browse(cr, uid, b_conf_id)
            coeff = b_conf[0].bareme_jaune.valeur

            ## On recherche le type de prix qui correspond au prix de vente classique
            type_ids = self.pool.get('product.price.type').search(cr, uid, [('name', '=', 'Prix promo jaune')])
            if type_ids:
                base = type_ids[0]

            ## Si la mea est de type jaune, on applique
            ## le barème c15 pour chaque produit
            for product in product_ids:
                p_data = prod_obj.read(cr, uid, product[0], ['name'])
                if product[1]:
                    item_id = item_obj.create(cr, uid, {'sequence': 3,
                                                    'name': p_data.get('name'), 
                                                    'product_id': product[0],
                                                    'base': base,
                                                    'bareme_id': bareme,
                                                    'price_discount': -1,
                                                    'price_surcharge': product[1],
                                                    'price_version_id': version_id})
                else:
                    item_id = item_obj.create(cr, uid, {'sequence': 3,
                                                    'name': p_data.get('name'), 
                                                    'product_id': product[0],
                                                    'base': base,
                                                    'bareme_id': bareme,
                                                    'price_discount': coeff-1,
                                                    'price_version_id': version_id})
                items.append(item_id)

        return items

    def _create_mea(self, cr, uid, ids, context={}):
        '''
            Créer les différentes versions et lignes de prix pour les MEA
        '''
        pricelist_obj = self.pool.get('product.pricelist')
        version_obj = self.pool.get('product.pricelist.version')
        tarifs_speciaux_obj = self.pool.get('product.tarifs.speciaux')
        promo_obj = self.pool.get('product.pricelist.promo')
        product_ids = []
        data = {}
        data['form'] = self.read(cr, uid, ids[0])
        for mea_in in self.pool.get('product.pricelist.mea.in').browse(cr, uid, data['form']['product_ids']):
            product_ids.append(mea_in.product_id.id)
            if mea_in.new_prix_achat and mea_in.new_prix_achat != 0.00:
                promo_obj._create_history(cr, uid, mea_in, data)

        data = {}
        data['form'] = self.read(cr, uid, ids[0])

        # Sauvegarde des données saisies (il faudra les restaurer lors de la création des version contenant les cumul mea + tarifs spéciaux) 
        data_ori = data['form'].copy()

        ## On récupère toutes les listes de prix où les mea s'appliquent (mea jaune ou blanche à oui)
        blanche_ids = pricelist_obj.search(cr, uid, [('tarif_choice', '=', 'blanche'), ('type', '=', 'sale'), ('mea_choice', '=', 'oui'), ('tarif_special_choice', '=', 'non')])
        jaune_ids = pricelist_obj.search(cr, uid, [('tarif_choice', '=', 'jaune'), ('type', '=', 'sale'), ('mea_choice', '=', 'oui'), ('tarif_special_choice', '=', 'non')])
        
        ## On cherche la version de base pour la liste de prix
        ## On cherche la version en cours pendant la mea
        ## On lui donne une date de fin qui correspond au début-1jour de la mea
        for list in pricelist_obj.browse(cr, uid, blanche_ids):
            new_version = self._define_mea(cr, uid, data, list, context=context)
            if new_version:
                version_obj.write(cr, uid, [new_version], {'active': True, 'name': data['form']['name']})
                new_items = self._create_item(cr, uid, data, new_version, 'blanche', context=context)

        for list in pricelist_obj.browse(cr, uid, jaune_ids):
            new_version = self._define_mea(cr, uid, data, list, context=context)
            if new_version:
                version_obj.write(cr, uid, [new_version], {'active': True, 'name': data['form']['name']})
                new_items = self._create_item(cr, uid, data, new_version, 'jaune',context=context)

        self.write(cr, uid, ids, {'state': 'done'})

        return True


product_pricelist_mea()


class product_in_mea(osv.osv):
    _name = 'product.pricelist.mea.in'
    _description = 'Produit dans la mea'
    _order = 'name'
        
    def _get_prix_achat(self, cr, uid, ids, field_name, arg, context=None):
        history_obj = self.pool.get('product.price.history')

        res = {}

        for pinp in self.browse(cr, uid, ids, context=context):
            history_ids = history_obj.search(cr, uid, [('product_id', '=', pinp.product_id.id), ('name', '<=', datetime.now())], 0, 1, 'name desc')
            if history_ids:
                h = history_obj.browse(cr, uid, history_ids[0], context=context)
                if not h.comment or len(h.comment) < 3 or h.comment[3:] != 'Mea':
                    res[pinp.id] = h.nouveau_prix_achat

        return res


    def onchange_product(self, cr, uid, ids, product_id, context=None):
        v = {}
        product_obj = self.pool.get('product.product')
        if product_id:
            for p in product_obj.browse(cr, uid, [product_id]):
                v['prix_blanche'] = 0.0
                v['prix_jaune'] = 0.0
                v['prix_achat'] = p.prix_achat
        return {'value': v}

    def _check_prix_blanche(self, cr, uid, ids, context=None):
        for this in self.browse(cr, uid, ids, context=context):
            if not this.new_prix_blanche or this.new_prix_blanche <= 0:
                raise osv.except_osv(_('Attention %s - %s !') % (this.product_id.name.strip(), this.new_prix_blanche), u'Le prix blanche doit être supérieur à 0 : (produit : %s, prix blanc : %s)' % (this.product_id.name.strip(), this.new_prix_blanche))
                return False
        return True

    def _check_prix_jaune(self, cr, uid, ids, context=None):
        for this in self.browse(cr, uid, ids, context=context):
            if not this.new_prix_jaune or this.new_prix_jaune <= 0:
                raise osv.except_osv(_('Attention %s - %s !') % (this.product_id.name.strip(), this.new_prix_jaune), u'Le prix jaune doit être supérieur à 0 : (produit : %s, prix blanc : %s)' % (this.product_id.name.strip(), this.new_prix_jaune))
                return False
        return True

    _columns = {
        'name': fields.integer(string='Séquence', readonly=True),
        'product_id': fields.many2one('product.product', string='Produit', required='1'),
        'promo_id': fields.many2one('product.pricelist.mea', ondelete='cascade'),
        'new_prix_blanche': fields.float(digits=(16,2), string='Prix blanche', required=True),
        'new_prix_jaune': fields.float(digits=(16,2), string='Prix jaune', required=True),
        'prix_achat': fields.function(_get_prix_achat, method=True, string='Prix achat', readonly=True, store=False),
        'new_prix_achat': fields.float(digits=(16,2), string='Nouveau prix d\'achat'),
    }

    _constraints = [
        (_check_prix_blanche,
            'Le prix blanche doit avoir un prix supérieur à 0.00',
            ['new_prix_blanche', 'product_id']),
        (_check_prix_jaune,
            'Le prix jaune doit avoir un prix supérieur à 0.00',
            ['new_prix_jaune', 'product_id'])]


product_in_mea()

