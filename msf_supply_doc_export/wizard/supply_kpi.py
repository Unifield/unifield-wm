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
import threading
import pooler
import logging
from datetime import datetime
from datetime import timedelta


class supply_kpi(osv.osv):
    _name = 'supply.kpi'
    _description = 'Supply Key Performance Indicators'

    col_map = {
        'dim_3a': {
            'dim_3a_supplier_checkbox':         ['name',            'Partner Name', 1],
            'dim_3a_supplier_type_checkbox':    ['partner_type',    'Partner Type', 2],
            'dim_3a_zone_checkbox':             ['zone',            'Zone', 3],
            'dim_3a_order_type_checkbox':       ['order_type',      'Order Type', 4],
            'dim_3a_order_category_checkbox':   ['categ',           'Order Category', 5],
            'dim_3a_priority_checkbox':         ['priority',        'Priority', 6],
            'dim_3a_product_checkbox':          ['default_code',    'Product', 7],
            'dim_3a_main_type_checkbox':        ['pn_main_type',    'Main Type', 8],
            'dim_3a_group_checkbox':            ['pn_group',        'Group', 9],
            'dim_3a_family_checkbox':           ['pn_family',       'Family', 10],
            'dim_3a_root_checkbox':             ['pn_root',         'Root', 11],
            },

        'dim_6a': {

            'dim_6a_year_checkbox':             ['sm_created_year', 'Year', 1],
            'dim_6a_month_checkbox':            ['sm_created_month', 'Month', 2],
            'dim_6a_currency':                  ['currency_code',   'Currency', 4],  # 3 is for state
            'dim_6a_reason_type_checkbox':      ['reason_type',     'Reason Type', 5],
            'dim_6a_product_checkbox':          ['product_qty',     'Product quantity', 6],
            'dim_6a_main_type_checkbox':        ['pn_main_type',    'Main Type', 7],
            'dim_6a_group_checkbox':            ['pn_group',        'Group', 8],
            'dim_6a_family_checkbox':           ['pn_family',       'Family', 9],
            'dim_6a_root_checkbox':             ['pn_root',         'Root', 10],

            },

        'dim_8b': {

            'dim_8b_year_checkbox':             ['po_created_year', 'Year', 1],
            'dim_8b_month_checkbox':            ['po_created_month', 'Month', 2],
            'dim_8b_week_checkbox':             ['po_created_week', 'Week', 3],
            'dim_8b_order_category_checkbox':   ['categ',           'Order category', 5],  # 4 is for state
            'dim_8b_order_type_checkbox':       ['order_type',      'Order Type', 6],
            'dim_8b_priority_checkbox':         ['priority',        'Priority', 7],
            'dim_8b_partner_type_checkbox':     ['partner_type',    'Partner Type', 8],
            'dim_8b_partner_checkbox':          ['name',            'Partner', 9],
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

    def get_sql_report(self, cr, uid, ids, prefix, aggregate, fields, context=None):
        supply_kpi_brw = self.browse(cr, uid, ids, context=None)[0]
        # get fields in the correct order
        cols = self.col_map[prefix]
        fields.extend([cols[key] for key in cols if getattr(supply_kpi_brw, key)])
        fields.sort(key=lambda x: x[2])   # use the numeric ranking, element 3, to sort

        # build header list
        group_by = ', '.join([elem[0] for elem in fields])
        # possible to have no selectable and no static group by fields, in which case no group by is needed
        if group_by:
            group_by = 'GROUP BY ' + group_by + ' ORDER BY ' + group_by

        # build select for data
        selects = ', '.join([elem[0] for elem in fields])
        sql = "SELECT " + aggregate[0] + ', ' + selects + ' FROM dimension_' + prefix[4:] + ' ' + group_by
        cr.execute(sql)
        return sql

    """
    def prepare_report_data(self, cr, uid, ids, prefix, aggregate, fields, context=None):
        supply_kpi_brw = self.browse(cr, uid, ids, context=None)[0]
        # get fields in the correct order
        cols = self.col_map[prefix]
        fields.extend([cols[key] for key in cols if getattr(supply_kpi_brw, key)])
        fields.sort(key=lambda x: x[2])   # use the numeric ranking, element 3, to sort

        # build header list
        group_by = ', '.join([elem[0] for elem in fields])
        # possible to have no selectable and no static group by fields, in which case no group by is needed
        if group_by:
            group_by = 'GROUP BY ' + group_by + ' ORDER BY ' + group_by

        headers = [aggregate[1]]
        headers.extend([elem[1] for elem in fields])

        # build select for data
        selects = ', '.join([elem[0] for elem in fields])
        sql = "SELECT " + aggregate[0] + ', ' + selects + ' FROM dimension_' + prefix[4:] + ' ' + group_by
        cr.execute(sql)
        # organise returned data for report
        report_lines_dict = cr.dictfetchall()   # list of dicts
        # sort data according to order in the fields list & convert to list of lists
        report_lines = []
        for line in report_lines_dict:
            sorted_line = list()
            sorted_line.append(line[aggregate[2]])   # sorted_line assignment split into 2 statements for readability
            for i, elem in enumerate(fields):
                # Replace & by AND
                if isinstance(line[elem[0]], basestring):
                    sorted_line.append(line[elem[0]].replace("&", "AND"))
                else:
                    sorted_line.append(line[elem[0]])
            report_lines.append(sorted_line)
        return {'report_header': headers, 'report_lines': report_lines}
    """

    def default_get(self, cr, uid, ids, context=None):

        kpi_ids = super(supply_kpi, self).search(cr, uid, [('create_uid', '=', uid)], context=context)
        kpi_id = super(supply_kpi, self).read(cr, uid, kpi_ids, context=context)
        if not kpi_id:
            kpi_id = super(supply_kpi, self).default_get(cr, uid, ids, context=context)
        else:
            kpi_id = kpi_id[0]

        if kpi_id:
            kss_obj = self.pool.get('supply.kpi.summary')
            kss_ids = kss_obj.search(cr, uid, [(uid, '=', uid)], context=context)

            if kss_ids:
                kss = kss_obj.browse(cr, uid, kss_ids[0], context)
                kpi_id['dim_3a'] = kss.dim_3a
                kpi_id['dim_6a'] = kss.dim_6a
                kpi_id['dim_6a_currency'] = kss.dim_6a_currency

        return kpi_id

    def check_kpi_running(self, cr, uid, context=None):
        args = [('running', '=', True)]
        kpi_id = self.search(cr, uid, args, context=context)
        kpi_obj = self.browse(cr, uid, kpi_id, context=context)

        # if refresh start begin one hour or more, we suppose it's not finish :
        # For example during a refresh, the server restart.
        for kpi in kpi_obj:
            if isinstance(kpi['refresh_dttm'], basestring):
                refresh_time = datetime.strptime(kpi['refresh_dttm'], "%Y-%m-%d %H:%M:%S.%f")
                time_outdated = datetime.now() - timedelta(minutes=60)
                if refresh_time >= time_outdated:
                    return True
        return False

    def refresh_thread(self, cr, uid, kpi_id, context=None):
        print "Start refreshing KPI at " + str(datetime.now())
        logging.info("KPI: Start refreshing KPI at " + str(datetime.now()))
        cr = pooler.get_db(cr.dbname).cursor()
        kpi_obj = self.pool.get('kpi.refresh')
        kpi_obj.truncate_tables(cr, uid)
        kpi_obj.refresh_data(cr, uid)
        values = {'running': False}
        super(supply_kpi, self).write(cr, uid, kpi_id, values, context=context)
        print "Stop refreshing KPI at " + str(datetime.now())
        logging.info("KPI: Stop refreshing KPI at " + str(datetime.now()))
        self.default_get(cr, uid, None, context)
        cr.commit()
        cr.close()

    def button_refresh(self, cr, uid, ids, context=None):
        if not self.check_kpi_running(cr, uid, context=None):
            args = [('create_uid', '=', uid)]
            kpi_id = self.search(cr, uid, args, context=context)
            values = {'running': True, 'refresh_dttm': datetime.now()}
            super(supply_kpi, self).write(cr, uid, kpi_id, values, context=context)
            refresh = threading.Thread(None, self.refresh_thread, None, (cr, uid, kpi_id), {'context': context})
            refresh.start()
            return self.default_get(cr, uid, ids, context)
        else:
            raise osv.except_osv("Refresh data",
                                 "You can not update the data for the moment: a refresh is already running")

    def button_3a(self, cr, uid, ids, context=None):
        if not self.check_kpi_running(cr, uid, context=None):
            prefix = 'dim_3a'
            aggregate = ['round(sum(pct_ontime)::numeric,2) as sum', 'Total', 'sum']
            fields = [['state', 'State', -1]]
            sql = self.get_sql_report(cr, uid, ids, prefix, aggregate, fields, context=None)

            return {
                'type': 'ir.actions.report.xml',
                'report_name': 'kpi.detail_xls',
                'datas': {"sql": sql, "aggregate": aggregate, "fields": fields},
                'nodestroy': True,
                'context': context,
            }
        else:
            raise osv.except_osv("Refresh data",
                                 "You can not export data for the moment: a refresh is already running")

    def button_6a(self, cr, uid, ids, context=None):
        if not self.check_kpi_running(cr, uid, context=None):
            prefix = 'dim_6a'
            # 0: sql command, 1: report heading, 2: sql column name
            aggregate = ['round(sum(value)::numeric,2) as sum', 'Total', 'sum']
            fields = []
            sql = self.get_sql_report(cr, uid, ids, prefix, aggregate, fields, context=None)
            #data = self.prepare_report_data(cr, uid, ids, prefix, aggregate, fields, context=None)
            return {
                'type': 'ir.actions.report.xml',
                'report_name': 'kpi.detail_xls',
                'datas': {"sql": sql, "aggregate": aggregate, "fields": fields},
                'nodestroy': True,
                'context': context,
            }
        else:
            raise osv.except_osv("Refresh data",
                                 "You can not export data for the moment: a refresh is already running")

    def button_8b(self, cr, uid, ids, context=None):
        if not self.check_kpi_running(cr, uid, context=None):
            prefix = 'dim_8b'
            # 0: sql command, 1: report heading, 2: sql column name
            aggregate = ['round(sum(cnt)::numeric,2) as sum', 'Total', 'sum']
            fields = [['state', 'State', 4]]
            sql = self.get_sql_report(cr, uid, ids, prefix, aggregate, fields, context=None)
            #data = self.prepare_report_data(cr, uid, ids, prefix, aggregate, fields, context=None)
            return {
                'type': 'ir.actions.report.xml',
                'report_name': 'kpi.detail_xls',
                'datas': {"sql": sql, "aggregate": aggregate, "fields": fields},
                'nodestroy': True,
                'context': context,
            }
        else:
            raise osv.except_osv("Refresh data",
                                 "You can not export data for the moment: a refresh is already running")

    def create(self, cr, uid, values, context=None):
        args = [('create_uid', '=', uid)]
        res_ids = super(supply_kpi, self).search(cr, uid, args, context=context)
        if res_ids:
            if res_ids[0]:
                # Force update first record
                res_ids = res_ids[0]
            super(supply_kpi, self).write(cr, uid, [res_ids], values, context=context)
            return res_ids
        else:
            return super(supply_kpi, self).create(cr, uid, values, context=context)

    def write(self, cr, uid, ids, values, context=None):
        return super(supply_kpi, self).write(cr, uid, ids, values, context=context)

supply_kpi()


class supply_kpi_summary(osv.osv):
    _name = 'supply.kpi.summary'
    _description = 'Supply KPI Summary Fields'

    _columns = {
        'dim_3a': fields.float("PO Lines on time", readonly=True),
        'dim_6a': fields.float('Value of expired loss', readonly=True),
        'dim_6a_currency': fields.char('Currency', size=3, readonly=True),
        'dim_8b': fields.float('Number of Purchase order lines', readonly=True),
    }

    def create(self, cr, uid, vals, context=None):
        return super(supply_kpi_summary, self).create(cr, uid, vals, context=context)

    def write(self, cr, uid, ids, vals, context=None):
        return super(supply_kpi_summary, self).write(cr, uid, vals, context=context)

supply_kpi_summary()