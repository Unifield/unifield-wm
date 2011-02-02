# -*- encoding: utf-8 -*-
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
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more detaila
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from report import report_sxw
from osv import osv
import pooler
import time

class print_cat(report_sxw.rml_parse):

        def __init__(self, cr, uid, name, context):
            super(print_cat, self).__init__(cr, uid, name, context)
            self.localcontext.update({
                'getCategory': self.get_category,
                'getProducts': self.get_products,
                'getPrice': self.get_price,
                'getBareme': self.get_bareme,
            })

        def get_category(self, category_id):
            """
                Retourne le nom de la catégorie category_id
            """
            if not category_id:
                return False

            return self.pool.get('product.category').browse(self.cr, self.uid, [category_id])[0].name

        def get_products(self, category_id):
            """
                Retourne tous les produits contenus dans
                la catégorie category_id
            """
            product_obj = self.pool.get('product.product')
            res = []
            
            product_ids = product_obj.search(self.cr, self.uid, [('categ_id', '=', category_id)])
            for p in product_obj.browse(self.cr, self.uid, product_ids):
                res.append(p)

            return res

        def get_price(self, prix_vente, bareme_id):
            """
                Retourne le prix de vente multiplié
                par la valeur du barème bareme_id
            """
            if not bareme_id:
                return False

            bareme_obj = self.pool.get('product.pricelist.bareme')
            
            valeur = bareme_obj.browse(self.cr, self.uid, [bareme_id])[0].valeur

            return valeur*prix_vente

        def get_bareme(self, bareme_id):
            """
                Retourne le nom du bareme bareme_id
            """
            if not bareme_id:
                return False

            bareme_obj = self.pool.get('product.pricelist.bareme')
            return bareme_obj.browse(self.cr, self.uid, [bareme_id])[0].name


report_sxw.report_sxw('report.category.pricelist','wizard.print.pricelist.cat','addons/iller_product/report/print_cat.rml',parser=print_cat)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
