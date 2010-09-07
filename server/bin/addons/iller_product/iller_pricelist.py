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

class product_pricelist_bareme(osv.osv):
    _name = 'product.pricelist.bareme'
    _description = 'Product Pricelist Bareme'


    def write(self, cr, uid, ids, vals, context={}):
        item_obj = self.pool.get('product.pricelist.item')
        if 'valeur' in vals:
            for id in ids:
                item_ids = item_obj.search(cr, uid, [('bareme_id', '=', id)], context=context)
                item_obj.write(cr, uid, item_ids, {'price_discount': float(vals.get('valeur'))-1})

        return super(product_pricelist_bareme, self).write(cr, uid, ids, vals, context={})


    _columns = {
        'name': fields.char(size=64, string='Nom'),
        'valeur': fields.float(digits=(16,6), string='Valeur'),
    }

product_pricelist_bareme()


class product_pricelist_item(osv.osv):
    _name = 'product.pricelist.item'
    _inherit = 'product.pricelist.item'

    def write(self, cr, uid, ids, vals, context={}):
        bareme_obj = self.pool.get('product.pricelist.bareme')
        if 'bareme_id' in vals:
            bareme = bareme_obj.read(cr, uid, vals.get('bareme_id'), ['valeur'], context)
            vals['price_discount'] = bareme.get('valeur')-1

        return super(product_pricelist_item, self).write(cr, uid, ids, vals, context=context)


    _columns = {
        'bareme_id': fields.many2one('product.pricelist.bareme', string='Barème'),
    }

    def bareme_change(self, cr, uid, ids, bareme_id, context={}):
        if bareme_id:
            discount = self.pool.get('product.pricelist.bareme').read(cr, uid, bareme_id, ['valeur'], context)
            return {'value': {'price_discount': discount.get('valeur')-1}}

product_pricelist_item()
