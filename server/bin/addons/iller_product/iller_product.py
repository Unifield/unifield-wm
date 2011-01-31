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
import pooler
import time

class product_price_history(osv.osv):
    _name = 'product.price.history'
    _description = 'Historique Prix Achat'
    _order = 'name desc'

    _columns = {
        'name': fields.date('Valable à partir du',required=True,select=1),
        'nouveau_prix_achat': fields.float('Prix d\'achat',required=True, digits=(16,2)),
        'nouveau_prix_vente': fields.float('Prix de vente', required=True, digits=(16,2)),
        'product_id': fields.many2one('product.product','Product',ondelete='cascade', select=1),
        'fin' : fields.char(size=1, string=' '),
        'comment': fields.char(size=128, string='Commentaire'),
    }
    _defaults = {
        'name': lambda *a: time.strftime('%Y-%m-%d'),
    }

product_price_history()


class product_product(osv.osv):
    _inherit = 'product.product'
    _name = 'product.product'


    def write(self, cr, uid, ids, vals, context={}):
        '''
            Calcul des tarifs en fonction des prix d'achat
        '''
        history_obj = self.pool.get('product.price.history')
        history_id = history_obj.search(cr, uid, [('name', '=', datetime.now())])
        for prd in self.browse(cr, uid, ids):
            vals['list_price'] = vals.get('prix_achat', prd.prix_achat)*vals.get('coeff_depart', prd.coeff_depart)
            vals['prix_blanche'] = vals.get('prix_achat', prd.prix_achat)*vals.get('coeff_blanche', prd.coeff_blanche)

            if 'prix_achat' in vals:
                data_history = {'name': datetime.now(),
                                'nouveau_prix_achat': vals.get('prix_achat'),
                                'nouveau_prix_vente': vals.get('prix_achat')*vals.get('coeff_depart', prd.coeff_depart),
                                'product_id': prd.id,
                                'comment': 'Prix modifié depuis la fiche du produit'}
                if history_id and len(history_id) > 0:
                    self.pool.get('product.price.history').write(cr, uid, history_id[0], data_history)
                else:
                    self.pool.get('product.price.history').create(cr, uid, data_history)

            if 'coeff_depart' in vals and not 'prix_achat' in vals:
                data_history = {'name': datetime.now(),
                                'nouveau_prix_achat': prd.prix_achat,
                                'nouveau_prix_vente': prd.prix_achat*vals.get('coeff_depart', prd.coeff_depart),
                                'product_id': prd.id,
                                'comment': 'Prix modifié depuis la fiche du produit'}
                if history_id and len(history_id) > 0:
                    self.pool.get('product.price.history').write(cr, uid, history_id[0], data_history)
                else:
                    self.pool.get('product.price.history').create(cr, uid, data_history)
                                                                        

        return super(product_product, self).write(cr, uid, ids, vals, context=context)


    def price_get(self, cr, uid, ids, ptype='list_price', context={}):
        res = {}
        if not context:
            context = {}
        product_uom_obj = self.pool.get('product.uom')
        for product in self.browse(cr, uid, ids, context=context):
            res[product.id] = product[ptype] or 0.0
            if ptype == 'list_price':
                res[product.id] = (res[product.id] * (product.price_margin or 1.0)) + \
                        product.price_extra
            if ptype in ('list_price') and context.get('datestandard'):
                cr.execute('''SELECT nouveau_prix_vente FROM product_price_history WHERE product_id=%s  AND name<=%s ORDER BY name desc LIMIT 1''',(product.id,context['datestandard']))
                ret = cr.fetchone()
                if ret:
                    res[product.id] = ret[0]
            if ptype in ('prix_achat') and context.get('datestandard'):
                cr.execute('''SELECT nouveau_prix_achat FROM product_price_history WHERE product_id=%s AND name<=%s ORDER BY name desc LIMIT 1''',(product.id,context['datestandard']))
                ret = cr.fetchone()
                if ret:
                    res[product.id] = ret[0]
            if ptype in ('prix_blanche') and context.get('datestandard'):
                cr.execute('''SELECT nouveau_prix_achat FROM product_price_history WHERE product_id=%s AND name<=%s ORDER BY name desc LIMIT 1''',(product.id,context['datestandard']))
                ret = cr.fetchone()
                if ret:
                    res[product.id] = ret[0] * product.coeff_blanche

            if 'uom' in context:
                uom = product.uos_id or product.uom_id
                res[product.id] = product_uom_obj._compute_price(cr, uid,
                        uom.id, res[product.id], context['uom'])
        return res


    _columns = {
        'prix_achat': fields.float(digits=(16, int(config['price_accuracy'])), string='Prix d\'achat'),
        'coeff_depart': fields.float(digits=(16,2), string='Coeff. départ'),
        'type_cond': fields.selection([('0000', 'PIECE'), ('0001', 'KILO'), ('0002', 'CARTON'), ('0003', 'BARQUETTE')], 
                                                                                            string='Type conditionnement'),
        'type_preselec': fields.selection([('0', 'Facturation pièce/carton'), ('1', 'Facturation Kilo')], string='Type préselection'),
        'coeff_blanche': fields.float(digits=(16,2), string='Coeff. blanche'),
        'coeff_jaune': fields.many2one('product.pricelist.bareme', string='Barème promo jaune'),
        'prix_blanche': fields.float(digits=(16, int(config['price_accuracy'])), string='Prix blanche'),
        'prix_decembre': fields.float(digits=(16, int(config['price_accuracy'])), string='Prix décembre'),

        'type_pesee': fields.selection([('0', 'Poids variable'), ('1', 'Prix fixe'), ('2', 'Poids fixe'),
                                        ('7', 'Négoce pièce'), ('8', 'Négoce poids')], string='Type de pesée'),
        'code_affectation': fields.selection([('DECP', 'Découpe'), ('PREP', 'Préparation')], string='Code Affectation'),
        'liste_prepa': fields.selection([('0', 'Rien'), ('1', 'Congelé'), ('2', 'Salaison'), ('3', 'Volaille')],
                                                string='Liste préparation', required=True),
        'price_history': fields.one2many('product.price.history', 'product_id', 'Historique des Prix'),

    }

    _defaults = {
        'cost_method': lambda *a: 'average',
        'type_cond': lambda *a: '0001',
        'type_preselec': lambda *a: '1',
        'coeff_blanche': lambda *a: 1.00,
    }


    def coeff_price_change(self, cr, uid, ids, prix_achat, coeff_depart, coeff_blanche, context={}):
        return {'value': {'list_price': prix_achat*coeff_depart, 'prix_blanche': prix_achat*coeff_blanche}}


    def promo_blanche_change(self, cr, uid, ids, coeff_blanche, prix_achat, context={}):
        return {'value': {'prix_blanche': coeff_blanche*prix_achat}}


    def preselec_onchange(self, cr, uid, ids, type_cond, type_preselec, context={}):
        if type_preselec == '1':
            return {'value': {'type_cond': '0001', 'type_preselec': '1'}}
        elif type_preselec == '0' and type_cond == '0001':
            return {'value': {}, 'warning': {'title': 'Impossible', 'message':
                'Le type de préselection à la pièce ou au carton est incompatible avec le conditionnement KILO'}}

        return {'value': {}}


    def cond_onchange(self, cr, uid, ids, type_cond, type_preselec, context={}):
        if type_cond == '0001':
            return {'value': {'type_cond': '0001', 'type_preselec': '1'}}
        elif type_preselec == '0' and type_cond == '0001':
            return {'value': {}, 'warning': {'title': 'Impossible', 'message':
                'Le type de conditionnement KILO est incompatible avec le type de préselection à la pièce/carton'}}

        return {'value': {}}


product_product()
