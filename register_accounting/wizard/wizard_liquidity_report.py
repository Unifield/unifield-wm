# encoding: utf-8
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2011 MSF, TeMPO consulting
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
from osv import osv, fields
import time

class wizard_liquidity_report(osv.osv_memory):
    _name = "wizard.liquidity.report"

    _columns = {
        'report_period': fields.many2one('account.period', 'Period'),
    }

   

    def _get_current_period(self, cr, uid, context=None):
        period_date = datetime.date.today()
        period_id = self.pool.get('account.period').get_period_from_date(
            cr, uid, period_date.strftime('%Y-%m-%d'))[0]
        return period_id or False

    def button_run_liquidity_report(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        wizard = self.browse(cr, uid, ids[0], context=context)
        data = {}
        data['ids'] = context.get('active_ids', [])
        data['model'] = context.get('active_model', 'ir.ui.menu')
        if wizard.report_period:
            data['report_period'] = wizard.report_period.id

        return {'type': 'ir.actions.report.xml', 
                'report_name': 'report.liquidity.position.2', 
                'datas': data,
                'context': context}

    
wizard_liquidity_report()