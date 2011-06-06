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
import time
import datetime
from tools.translate import _

class wizard_gibier(osv.osv_memory):
    _name = "wizard.gibier"

    _columns = {
        'date_debut': fields.date(string="Date de début", required=True),
        'date_fin': fields.date(string="Date de fin", required=True),
        'type': fields.selection([('e', 'Entrée'), ('s', 'Sortie'), ('t', 'Tout')], string="Type", required=True)
    }

    _defaults = {
        'date_fin': lambda *a: time.strftime('%Y-%m-%d'),
        'type': lambda *a: 't',
    }

    def action_confirmer(self, cr, uid, ids, context={}):
        """
        Vérifie les dates saisies ; récupère les données du wizard, puis renvoie
        """
        # Préparation de variables
        wizard = self.browse(cr, uid, ids[0], context=context)
        date_deb = wizard.date_debut
        date_fin = wizard.date_fin
        type = wizard.type
        irmd_obj = self.pool.get('ir.model.data')
        if date_fin < date_deb:
            raise osv.except_osv(_('Attention'), _('La date de fin doit être supérieure à celle de début.'))
        # Récupération de l'id de la vue à afficher
        view_ids = irmd_obj.search(cr, uid, [('name', '=', 'gibier_entree_sortie_tree'), ('model', '=', 'ir.ui.view')])
        # Préparation de l'élément permettant de trouver la vue à  afficher
        if view_ids:
            view = irmd_obj.read(cr, uid, view_ids[0])
            view_id = (view.get('res_id'), view.get('name'))
        else:
            raise osv.except_osv(_('Erreur'), _("Impossible d'afficher le résultat : vue non trouvée."))
        # Préparation des éléments
        sm_obj = self.pool.get('stock.move')
        # Recherche des stock.move qui correspondent
        if type == 't':
            sm_ids = sm_obj.search(cr, uid, [('picking_id.type', 'in', ['in', 'out']), ('date', '>=', date_deb), ('date', '<=', date_fin)])
        elif type == 'e':
            sm_ids = sm_obj.search(cr, uid, [('picking_id.type', '=', 'in'), ('date', '>=', date_deb), ('date', '<=', date_fin)])
        elif type == 's':
            sm_ids = sm_obj.search(cr, uid, [('picking_id.type', '=', 'out'), ('date', '>=', date_deb), ('date', '<=', date_fin)])
        else:
            raise osv.except_osv(_('Erreur'), _('Type entréee/sortie inconnu.'))

        # Traitement
        ges_obj = self.pool.get('gibier.entree.sortie')
        # on vide la table osv_memory entière
        ges_ids = ges_obj.search(cr, uid, [], context=context)
        ges_obj.unlink(cr, uid, ges_ids, context=context)
        for sm in sm_obj.browse(cr, uid, sm_ids, context=context):
            type_ligne = 'i'
            if sm.picking_id.type == 'in':
                type_ligne = 'e'
            elif sm.picking_id.type == 'out':
                type_ligne = 's'
            vals = {
                'type': type_ligne,
                'date': datetime.datetime.strptime(sm.date_planned, '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d'),
                'origine': (sm.address_id and sm.address_id.partner_id.ref) or None,
                'designation': sm.name,
                'nom': (sm.address_id and sm.address_id.partner_id.name) or None,
                'article': sm.product_id.default_code,
                'designation': sm.product_id.name,
                'qte': sm.product_qty,
            }
            ges_obj.create(cr, uid, vals, context=context)
        return {
            'type': 'ir.actions.act_window',
                'res_model': 'gibier.entree.sortie',
                'view_type': 'form',
                'view_mode': 'tree,form',
                'view_id': view_id,
                }

wizard_gibier()

class gibier_entree_sortie(osv.osv_memory):
    _name = 'gibier.entree.sortie'
    _order = 'date'

    _columns = {
        'type': fields.selection([('e', 'E'), ('s', 'S'), ('i', 'I')], string="Type", help="Définit le type, Entrée (E) ou Sortie (S) pour l'article désigné.\
            Si le type est méconnu, alors on affiche I (inconnu)."),
        'date': fields.date(string="Date"),
        'origine': fields.char(string="Origine", size=6, help="Code du client ou du fournisseur rattaché à l'article."),
        'nom': fields.char(string="Nom", size=60,help="Nom du client/fournisseur."),
        'article': fields.char(string="Article", size=6, help="Code de l'article."),
        'designation': fields.char(string="Désignation", size=255, help="Désignation de l'article."),
        'qte': fields.integer(string="Quantité", help="Quantité de la commande pour l'article donné."),
    }

gibier_entree_sortie()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
