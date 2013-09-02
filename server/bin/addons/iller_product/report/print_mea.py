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

class print_mea(report_sxw.rml_parse):

        def __init__(self, cr, uid, name, context):
            super(print_mea, self).__init__(cr, uid, name, context)
            self.localcontext.update({
                'getPrix': self._getPrix,
                'getDoublon': self._getDoublon,
                'time': time,
            })

        def _getPrix(self, product_id, price_type, promo_id):
            cr = self.cr
            uid = self.uid
            b_conf_obj = self.pool.get('pricelist.mea.configuration')
            p_obj = self.pool.get('product.product')
            b_conf_ids = b_conf_obj.search(cr, uid, [])
            
            b_coeff = 1.00
            if b_conf_ids:
                if price_type == 'jaune':
                    b_coeff = b_conf_obj.browse(cr, uid, b_conf_ids[0]).bareme_jaune.valeur

            prix_vente = p_obj.read(cr, uid, product_id, ['list_price']).get('list_price')

            return prix_vente*b_coeff

        def _getDoublon(self, product_id, promo_id):
            mea_obj = self.pool.get('product.pricelist.mea')
            
            for product in mea_obj.browse(self.cr, self.uid, mea_id).product_ids:
                if product.product_id.id == product_id:
                    return '*'

            return ''



report_sxw.report_sxw('report.print.mea','product.pricelist.mea','addons/iller_product/report/print_mea.rml',parser=print_mea)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
