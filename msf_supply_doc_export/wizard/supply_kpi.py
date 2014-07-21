#!/usr/bin/env python
# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
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

from osv import osv
from osv import fields
from tools.translate import _
from lxml import etree

import time
from datetime import datetime



class supply_kpi(osv.osv):
    _name = 'supply.kpi'
    _description = 'Supply Key Performance Indicators'
    
    col_map = {'dim_3a': {
            'dim_3a_supplier_checkbox': ['name','Partner Name',1],
            'dim_3a_supplier_type_checkbox': ['partner_type','Partner Type',2],
            'dim_3a_zone_checkbox': ['zone','Zone',3],
            'dim_3a_order_type_checkbox': ['order_type','Order Type',4],
            'dim_3a_order_category_checkbox': ['categ','Order Category',5],
            'dim_3a_priority_checkbox': ['priority','Priority',6],
            'dim_3a_product_checkbox': ['default_code','Product',7],
            'dim_3a_main_type_checkbox': ['pn_main_type','Main Type',8],
            'dim_3a_group_checkbox': ['pn_group','Group',9],
            'dim_3a_family_checkbox': ['pn_family','Family',10],
            'dim_3a_root_checkbox': ['pn_root','Root',11],
            }
    }

    
    
    _columns = {
         'running': fields.boolean(string='Is the KPI data generation running ?', readonly=True),
         'refresh_dttm': fields.datetime('KPIs last refreshed', readonly=True),
         'dim_3a': fields.float("PO Lines on time", readonly=True),
         'dim_3a_supplier_checkbox': fields.boolean(string='Supplier'),
         'dim_3a_supplier_type_checkbox': fields.boolean(string='Supplier Type'),
         'dim_3a_zone_checkbox': fields.boolean(string='Zone'),
         'dim_3a_order_type_checkbox': fields.boolean(string='Order Type'),
         'dim_3a_order_category_checkbox': fields.boolean(string='Order Category'),
         'dim_3a_priority_checkbox': fields.boolean(string='Priority'),
         'dim_3a_product_checkbox': fields.boolean(string='Product'),
         'dim_3a_main_type_checkbox': fields.boolean(string='Main Type'),
         'dim_3a_group_checkbox': fields.boolean(string='Group'),
         'dim_3a_family_checkbox': fields.boolean(string='Family'),
         'dim_3a_root_checkbox': fields.boolean(string='Root'),
         
         'dim_6a': fields.float('Value of expired loss', readonly=True),
         'dim_6a_currency': fields.char('Currency', size=3, readonly=True),
         'dim_6a_reason_type_checkbox': fields.boolean(string='Reason type'),
         'dim_6a_product_checkbox': fields.boolean(string='Product'),
         'dim_6a_main_type_checkbox': fields.boolean(string='Main Type'),
         'dim_6a_group_checkbox': fields.boolean(string='Group'),
         'dim_6a_family_checkbox': fields.boolean(string='Family'),
         'dim_6a_root_checkbox': fields.boolean(string='Root'),
         'dim_6a_month_checkbox': fields.boolean(string="Month"),
         'dim_6a_year_checkbox': fields.boolean(string="Year"),
         
         'dim_8b': fields.float('Number of Purchase order lines', readonly=True),
         'dim_8b_order_category_checkbox': fields.boolean(string='Order Category'),
         'dim_8b_order_type_checkbox': fields.boolean(string='Order Type'),
         'dim_8b_priority_checkbox': fields.boolean(string='Priority'),
         'dim_8b_partner_type_checkbox': fields.boolean(string='Partner Type'),
         'dim_8b_partner_checkbox': fields.boolean(string='Partner'),
         'dim_8b_week_checkbox': fields.boolean(string="Week"),
         'dim_8b_month_checkbox': fields.boolean(string="Month"),
         'dim_8b_year_checkbox': fields.boolean(string="Year"),

    }
    
    def button_refresh(self, cr, uid, ids, context=None):
        print 'refresh button pressed'
        self.running = True
        self.refresh_dttm = datetime.now()
        kpi_obj = self.pool.get('kpi.refresh') 
        kpi_obj.truncate_tables(cr, uid)
        kpi_obj.refresh_data(cr,uid)
        return True
    
    
    def prepare_report_data(self, cr, uid, ids, prefix, aggregate, fields, context=None):
             
        supply_kpi = self.browse(cr, uid, ids, context=None)[0]  
        cols = self.col_map[prefix]
        fields.extend([cols[key] for key in cols if getattr(supply_kpi,key)])
        fields.sort(key=lambda x: x[2])   # use the numeric ranking, element 3, to sort
        print 'fields:', fields
        group_by = ', '.join([elem[0] for elem in fields]) 
        if group_by:       # possible to have no selectable and no static group by fields, in which case no group by is needed
            group_by = 'group by ' + group_by
        headers = [aggregate[1]]
        headers.extend([elem[1] for elem in fields])
        selects = ', '.join([elem[0] for elem in fields])
        sql = "select " + aggregate[0] + ', ' + selects + ' from dimension_' + prefix[4:] + ' ' + group_by
        print sql
        cr.execute(sql)
        report_lines_dicts = cr.dictfetchall()   # list of dicts
        print 'report_lines_dicts:', report_lines_dicts
        report_lines = [x.values() for x in report_lines_dicts]  # convert to list of lists
        print 'report_lines list:', report_lines
        
        return {'report_header': headers, 'report_lines': report_lines }
    
    
    def button_3a(self, cr, uid, ids, context=None):
        print 'button 3a pressed'
        prefix='dim_3a'
        aggregate = ['sum(cnt)','Total']
        fields = [['state','State',-1]]
        
        datas = self.prepare_report_data(cr, uid, ids, prefix, aggregate, fields, context=None)
        print 'datas sfc:', datas
        
        #datas = {'ids': ids, 'report_header': 'header', 'report_parms': 'report_parms'}  
        return {                                                                
            'type': 'ir.actions.report.xml',                                    
            'report_name': 'kpi.detail_xls',                                       
            'datas': datas,                                                     
            'nodestroy': True,                                                  
            'context': context,  
        }
    
    def button_6a(self, cr, uid, ids, context=None):
        print 'button 6a pressed'
        return True
        
    def button_8b(self, cr, uid, ids, context=None):
        print 'button 8b pressed'
        return True
        

    def create(self, cr, uid, vals, context=None):
        return super(supply_kpi, self).create(cr, uid, vals, context=context)
    

    def write(self, cr, uid, ids, vals, context=None):
        return super(supply_kpi, self).write(cr, uid, vals, context=context)
       
    
    
supply_kpi()