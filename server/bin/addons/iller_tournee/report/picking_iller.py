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
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import time
from report import report_sxw
from osv import osv

class picking_iller(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(picking_iller, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time,
            'get_weight':self.get_weight,
        })
        
    def get_weight(self, move_lines):
        
        res = {}
        str_res = ''

        for move_line in move_lines:
            
            if move_line.product_uom.name not in res:
                res[move_line.product_uom.name] = 0
                
            res[move_line.product_uom.name] += move_line.product_qty
            
        for i in res:
            str_res += '%s %s \n\r' %(res[i], i)
            
        return str_res
        
report_sxw.report_sxw('report.stock.picking.iller','stock.picking','addons/iller_tournee/report/picking_iller.rml',parser=picking_iller)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

