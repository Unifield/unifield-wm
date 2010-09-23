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
import pooler
import time

class product_product(osv.osv):
    _inherit = 'product.product'
    _name = 'product.product'


    def write(self, cr, uid, ids, vals, context={}):
        if 'prix_achat' in vals:
            for prd in self.browse(cr, uid, ids):
                vals['old_purchase_price'] = prd.prix_achat
                vals['list_price'] = vals.get('prix_achat', prd.standard_price)*vals.get('coeff_depart', prd.coeff_depart)

            if 'coeff_blanche' in vals:
                vals['prix_blanche'] = vals.get('prix_achat', prd.standard_price)*vals.get('coeff_blanche', prd.coeff_blanche)

        return super(product_product, self).write(cr, uid, ids, vals, context=context)


    _columns = {
        'prix_achat': fields.float(digits=(16, int(config['price_accuracy'])), string='Prix d\'achat'),
        'old_purchase_price': fields.float(digits=(16, int(config['price_accuracy'])), string='Ancien prix d\'achat', readonly=True),
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
    }

    _defaults = {
        'cost_method': lambda *a: 'average',
        'type_cond': lambda *a: '0001',
        'type_preselec': lambda *a: '1',
    }


    def coeff_price_change(self, cr, uid, ids, standard_price, coeff_depart, context={}):
        return {'value': {'list_price': standard_price*coeff_depart}}


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
