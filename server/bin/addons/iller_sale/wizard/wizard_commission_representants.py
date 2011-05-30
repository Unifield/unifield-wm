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

class wizard_commission_representant(osv.osv_memory):
    _name = "wizard.commission.representant"
    _columns = {
        'mois': fields.selection([(1, "Janvier"), (2, "Février"), (3, "Mars"), (4, "Avril"), (5, "Mai"), (6, "Juin"), (7, "Juillet"), 
            (8, "Août"), (9, "Septembre"), (10, "Octobre"), (11, "Novembre"), (12, "Décembre")], string="Mois", required=True, 
            help="L'année utilisée pour la génération du rapport dépend du mois en cours. Exemple : Nous sommes en Juin 2011. Vous choisissez Avril, \
            C'est Avril 2011 qui sera sur le rapport. Vous choississez Décembre, c'est Décembre 2010 qui sera utilisé pour la génération du rapport."),
        'representant': fields.many2one("res.users", string="Représentant", required=False, help="Si laissé vide tout les représentants seront utilisés."),
    }

    _defaults = {
        'mois': lambda *a: datetime.datetime.now().month,
        'representant': lambda self,cr,uid,context: uid,
    }

    def action_valider(self, cr, uid, ids, context={}):
        """
        Valide le formulaire et envoie le résultat pour la génération du rapport
        """
        datas = {'ids': context.get('active_ids', [])}
        res = self.read(cr, uid, ids, ['mois', 'representant'], context=context)
        res = res and res[0] or {}
        datas['form'] = res
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'commission.representants',
            'datas': datas,
                }

wizard_commission_representant()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
