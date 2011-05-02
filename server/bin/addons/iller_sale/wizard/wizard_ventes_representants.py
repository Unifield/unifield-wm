#!/usr/bin/env python
#-*- encoding:utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution    
#    Copyright (C) 2011 TeMPO Consulting. All Rights Reserved
#    TeMPO Consulting (<http://www.tempo-consulting.fr/>).
#    Author: Olivier DOSSMANN
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
import datetime

class wizard_ventes_representants(osv.osv_memory):
    _name = "wizard.ventes.representants"
    _columns = {
        'date_debut': fields.date(string="Date début", required=True),
        'date_fin': fields.date(string="Date fin", required=True),
        'representant': fields.many2one("res.users", string="Représentant", required=False),
    }

    _defaults = {
        'date_debut': lambda *a: (datetime.datetime.now() + datetime.timedelta(days=-1)).strftime('%Y-%m-%d'),
        'date_fin': lambda *a: datetime.datetime.now().strftime('%Y-%m-%d'),
    }

    def action_imprimer_rapport(self, cr, uid, ids, context={}):
        datas = {'ids': context.get('active_ids', [])}
        res = self.read(cr, uid, ids, ['date_debut', 'date_fin', 'representant'], context=context)
        res = res and res[0] or {}
        datas['form'] = res
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'ventes.representants',
            'datas': datas,
                }

wizard_ventes_representants()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
