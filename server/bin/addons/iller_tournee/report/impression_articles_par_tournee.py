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
from tools.translate import _

class impression_articles_par_tournee(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        """
        Initialisation du 'parser'
        """
        super(impression_articles_par_tournee, self).__init__(cr, uid, name, context)
        self.localcontext.update({
            'getSaleOrderLineByType': self.get_sale_order_line_by_type,
            'getType': self.get_type,
            'getSelection': self.get_selection,
            'time': time,
        })

    def get_sale_order_line_by_type(self, tournee_id, date, type_article):
        """
        Retourne des objets sale.order.line correspondant à un type donné
        """
        # Préparation des objets
        so_obj = self.pool.get('sale.order')
        sol_obj = self.pool.get('sale.order.line')
        # Récupération des ids de commandes correspondant à la recherche fournie
        commandes_ids = so_obj.search(self.cr, self.uid, [('tournee_id', '=', tournee_id), ('date_order', '=', date), ('state', '=', 'progress')])
        res = []
        # Si le type d'article est 0, alors on prend tout les types de la base
        if type_article == '0':
            # On parcours chaque type afin de récupérer les objets 
            #+ correspondants
            for i in ['0', '1', '2', '3']:
                res.append([])
                res_id = sol_obj.search(self.cr, self.uid, [('order_id', 'in', commandes_ids), ('product_id.liste_prepa', '=', i)])
                for j in res_id:
                    sol = sol_obj.browse(self.cr, self.uid, j)
                    res[int(i)].append(sol)
        else:
            # Si le type est autre que 0 alors on ne retourne que les objets de 
            #+ ce type
            res.append([])
            res_id = sol_obj.search(self.cr, self.uid, [('order_id', 'in', commandes_ids), ('product_id.liste_prepa', '=', type_article)])
            for i in res_id:
                sol = sol_obj.browse(self.cr, self.uid, i)
                res[0].append(sol)
        # On crée le résultat final en supprimant les éléments vides (pour un 
        #+ meilleur affichage)
        res_epure = []
        # Parcours des éléments récupérés
        for i in res:
            if not i:
                continue
            else:
                # Suppression des éléments vides
                res_epure.append(i)
        return res_epure

    def get_selection(self, o, field):
        """
        Retourne le libellé d'un champ sélection
        """
        sel = self.pool.get(o._name).fields_get(self.cr, self.uid, [field])
        res = dict(sel[field]['selection']).get(getattr(o,field),getattr(o,field))
        name = '%s,%s' % (o._name, field)
        tr_ids = self.pool.get('ir.translation').search(self.cr, self.uid, [('type', '=', 'selection'), ('name', '=', name),('src', '=', res)])
        if tr_ids:
            return self.pool.get('ir.translation').read(self.cr, self.uid, tr_ids, ['value'])[0]['value']
        else:
            return res

    def get_type(self, sale_order_line_browse):
        """
        Retourne le type (liste_prepa) du premier élément d'un ensemble de 
        lignes de commandes.
        @sale_order_line_browse : un tableau contenant un ensemble de 
        sale.order.line considérés comme du même type !
        """
        if not sale_order_line_browse:
            return False
        else:
            res = self.get_selection(sale_order_line_browse[0].product_id, 'liste_prepa')
            if res == 'Rien':
                res = 'Divers'
            return res

report_sxw.report_sxw('report.articles.par.tournee','sale.order.line','addons/iller_tournee/report/report_articles_par_tournee.rml', parser=impression_articles_par_tournee)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
