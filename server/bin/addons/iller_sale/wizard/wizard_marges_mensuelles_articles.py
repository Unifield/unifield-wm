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

class wizard_marges_articles(osv.osv):
    _name = "wizard.marges.articles"
    _columns = {
        'date_debut': fields.date(string="Date début", required=True),
        'date_fin': fields.date(string="Date fin", required=True),
        'article': fields.many2one("product.product", string="Article", required=False),
        'famille_article': fields.many2one("product.category", string="Famille d'articles", required=False),
    }

    _defaults = {
        'date_debut': lambda *a: (datetime.datetime.now() + datetime.timedelta(days=-1)).strftime('%Y-%m-%d'),
        'date_fin': lambda *a: datetime.datetime.now().strftime('%Y-%m-%d'),
    }

    def action_imprimer_rapport(self, cr, uid, ids, context={}):
        datas = {'ids': context.get('active_ids', [])}
        res = self.read(cr, uid, ids, ['date_debut', 'date_fin', 'article', 'famille_article'], context=context)
        art = res[0].get('article', False)
        famille = res[0].get('famille_article', False)
        if (not art and not famille) or (art and famille):
            raise osv.except_osv('Erreur', "Veuillez remplir un seul des champs article ou famille d'articles.")
        res = res and res[0] or {}
        datas['form'] = res
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'marges.articles',
            'datas': datas,
                }

wizard_marges_articles()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
