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

class impression_ventes_representants(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        """
        Initialisation du 'parser'
        """
        super(impression_ventes_representants, self).__init__(cr, uid, name, context)
        self.localcontext.update({
            'getRepresentants': self.get_representants,
            'getNbreCmdes': self.get_nombre_commandes,
            'getTotalVentes': self.get_total_ventes,
            'time': time,
            'locale': locale,
        })

    def get_representants(self, representant=None):
        """
        Donne le représentant fourni par le formulaire, ou la liste complète des représentants si ce champ est vide
        """
        user_obj= self.pool.get('res.users')
        if representant:
            return user_obj.browse(self.cr, self.uid, representant[0])
        users = []
        for id in user_obj.search(self.cr, self.uid, []):
            users.append(user_obj.browse(self.cr, self.uid, id))
        return users

    def get_commandes(self, user_id=None, date_deb=None, date_fin=None):
        """
        Renvoie les commandes faites par un vendeur sur une période donnée
        """
        if user_id == None or date_deb == None or date_fin == None:
            return False
        sale_obj = self.pool.get('sale.order')
        res = sale_obj.search(self.cr, self.uid, [('state', '=', 'done'), ('user_id', '=', user_id), 
            ('date_order', '>=', date_deb), ('date_order', '<=', date_fin)])
        return res

    def get_nombre_commandes(self, user_id=None, date_deb=None, date_fin=None):
        """
        Renvoie le nombre de commandes faites par l'utilisateur sur une période donnée
        """
        if user_id == None or date_deb == None or date_fin == None:
            return False
        cmdes = self.get_commandes(user_id, date_deb, date_fin)
        res = len(cmdes) or 0
        return res

    def get_total_ventes(self, user_id=None, date_deb=None, date_fin=None):
        """
        Donne le total des ventes effectuées par le vendeur pour une période donnée.
        """
        if user_id == None or date_deb == None or date_fin == None:
            return False
        total = 0
        for cmd_id in self.get_commandes(user_id, date_deb, date_fin):
            total += self.pool.get('sale.order').browse(self.cr, self.uid, cmd_id).amount_total
        return total

report_sxw.report_sxw('report.ventes.representants','sale.order','addons/iller_sale/report/report_ventes_representants.rml', parser=impression_ventes_representants)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
