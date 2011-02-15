#!/usr/bin/env python
#-*- encoding:utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution    
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    Tempo Consulting (<http://www.tempo-consulting.fr/>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from report import report_sxw
from osv import osv
import time
import locale

class impression_commandes_par_tournee(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(impression_commandes_par_tournee, self).__init__(cr, uid, name, context)
        self.localcontext.update({
            'getSaleOrder': self.get_sale_order,
            'getProducts': self.get_products,
            'time': time,
            'locale': locale,
        })

    def get_sale_order(self, sale_order_id):
        so_obj = self.pool.get('sale.order')
        return so_obj.browse(self.cr, self.uid, sale_order_id)

    def get_products(self, sale_order):
        print sale_order
        sol_obj = self.pool.get('sale.order.line')
        res = []
        
        sol_ids = sol_obj.search(self.cr, self.uid, [('order_id', '=', sale_order.id)])
        for sol in sol_obj.browse(self.cr, self.uid, sol_ids):
            res.append(sol)

        return res

report_sxw.report_sxw('report.commandes.par.tournee','sale.order','addons/iller_tournee/report/report_commandes_par_tournee.rml', parser=impression_commandes_par_tournee)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
