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
import calendar
from tools.translate import _
import datetime

class impression_commission_representants(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        """
        Initialisation du 'parser'
        """
        super(impression_commission_representants, self).__init__(cr, uid, name, context)
        self.localcontext.update({
            'getRepresentants': self.get_representants,
            'getNomMois': self.get_nom_mois,
            'getAnnee': self.get_annee,
            'getDateCourante': self.get_date_courante,
            'getCommission': self.get_commission,
            'time': time,
            'locale': locale,
        })

    def get_representants(self, representant=None):
        """
        Donne le représentant fourni par le formulaire, ou la liste complète des représentants si ce champ est vide
        """
        user_obj= self.pool.get('res.users')
        users = []
        if representant:
            users.append(user_obj.browse(self.cr, self.uid, representant))
        else:
            for id in user_obj.search(self.cr, self.uid, []):
                users.append(user_obj.browse(self.cr, self.uid, id))
        return users

    def get_nom_mois(self, mois=None, context={}):
        """
        Retourne le nom du mois, en Français pour le numéro donné en paramètre.
        """
        if not type(mois) == int:
            raise osv.except_osv(_('Erreur'), _('Est attendu un entier pour donner le numéro du mois.'))
        ensemble = ['Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin', 'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre']
        return ensemble[mois-1]

    def get_annee(self, mois=None, context={}):
        """
        Donne l'année en fonction du numéro du mois donné sur une plage restreinte de 12 mois.
        C'est à dire que si le mois donné est ultérieur à la date actuelle, l'année donnée sera l'année précédente.
        Exemple : 
          - Nous sommes en Mai 2011.
          - Je donne le mois de Juin.
          - la fonction me retourne 2010 car Juin n'est pas encore arrivé.
        """
        if not mois:
            raise osv.except_osv(_('Erreur'), _('Un élément est manquant : "mois".'))
        ce_jour = datetime.datetime.now()
        res = ce_jour.year
        if mois > ce_jour.month:
            res = ce_jour.year - 1
        return res

    def get_date_courante(self, context={}):
        """
        Retourne la date courante
        """
        return time.strftime('%d/%m/%Y')

    def get_commission(self, representant=None, mois=None, context={}):
        """
        Donne la commission pour un représentant donné sur le mois donné
        """
        if not mois:
            raise osv.except_osv(_('Erreur'), _('Un élément est manquant : "mois".'))
        if not representant:
            raise osv.except_osv(_('Erreur'), _('Un élément est manquant : "représentant"'))
        # Préparation des dates
        annee = self.get_annee(mois)
        dernier_jour_du_mois = calendar.monthrange(annee, mois)[1]
        # Date de début et de fin
        debut_mois = datetime.datetime(annee, mois, 1)
        fin_mois = datetime.datetime(annee, mois, dernier_jour_du_mois)
        # Formatage des dates pour l'ORM / postgresql
        date_deb = debut_mois.strftime('%Y-%m-%d')
        date_fin = fin_mois.strftime('%Y-%m-%d')
        # Préparation de la requête
        inv = self.pool.get('account.invoice')
        # Requête sur l'ensemble des factures
        inv_ids = inv.search(self.cr, self.uid, [('date_invoice', '>=', date_deb), ('date_invoice', '<=', date_fin), ('user_id', '=', representant)], 
            context=context)
        if isinstance(inv_ids, (int, long)):
            inv_ids = [inv_ids]
        total = 0
        for invoice in inv.browse(self.cr, self.uid, inv_ids, context=context):
            total += invoice.commission
        return total

report_sxw.report_sxw('report.commission.representants','account.invoice','addons/iller_sale/report/report_commission_representants.rml', parser=impression_commission_representants)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
