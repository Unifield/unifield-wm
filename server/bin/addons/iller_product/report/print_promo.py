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

class print_promo(report_sxw.rml_parse):

        def __init__(self, cr, uid, name, context):
            super(print_promo, self).__init__(cr, uid, name, context)
            self.localcontext.update({
                'getPrix': self._getPrix,
                'getDoublon': self._getDoublon,
                'time': time,
            })

        def _getPrix(self, product_id, type, promo_id):
            cr = self.cr
            uid = self.uid
            b_conf_obj = self.pool.get('pricelist.promo.configuration')
            p_obj = self.pool.get('product.product')
            promo_obj = self.pool.get('product.pricelist.promo')
            b_conf_ids = b_conf_obj.search(cr, uid, [])

            promo = promo_obj.browse(cr, uid, promo_id)
            
            b_coeff = 1.00
            if b_conf_ids:
                if type == 'jaune':
                    b_coeff = b_conf_obj.browse(cr, uid, b_conf_ids[0]).bareme_jaune.valeur
                else:
                    b_coeff = b_conf_obj.browse(cr, uid, b_conf_ids[0]).bareme_page2.valeur

            prix_vente = p_obj.read(cr, uid, product_id, ['list_price']).get('list_price')

            return prix_vente*b_coeff

        def _getDoublon(self, product_id, promo_id):
            promo_obj = self.pool.get('product.pricelist.promo')
            
            for product in promo_obj.browse(self.cr, self.uid, promo_id).product_ids:
                if product.product_id.id == product_id:
                    return '*'

            return ''



report_sxw.report_sxw('report.print.promo','product.pricelist.promo','addons/iller_product/report/print_promo.rml',parser=print_promo)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
