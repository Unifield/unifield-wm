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
from datetime import datetime

class impression_produits_a_expedier_par_tournee(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        """
        Initialisation du 'parser'
        """
        super(impression_produits_a_expedier_par_tournee, self).__init__(cr, uid, name, context)
        self.localcontext.update({
            'getObjects': self.get_objects,
            'time': time,
        })

    def get_objects(self, tournee_id, date):
        """
        Retourne des listes de colisages
        """
        sp_obj= self.pool.get('stock.picking')
        la_date = datetime.strptime(date, '%Y-%m-%d')
        min_date = datetime(la_date.year, la_date.month, la_date.day, 0, 0 ,0).__str__()
        max_date = datetime(la_date.year, la_date.month, la_date.day, 23, 59 ,59).__str__()
        # Récupération des ids de commandes correspondant à la recherche fournie
        res_ids = sp_obj.search(self.cr, self.uid, [('tournee_id', '=', tournee_id), ('max_date', '>=', min_date), ('max_date', '<=', max_date), ('state', '=', 'confirmed')])
        # Création du résultat
        res = []
        for sp in res_ids:
            res.append(sp_obj.browse(self.cr, self.uid, sp))
        return res

report_sxw.report_sxw('report.produits.a.expedier.par.tournee','stock.picking','addons/iller_tournee/report/report_produits_a_expedier_par_tournee.rml', parser=impression_produits_a_expedier_par_tournee, header=False)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
