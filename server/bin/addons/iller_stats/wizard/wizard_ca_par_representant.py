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
from tools.translate import _
import calendar

class wizard_ca_par_representant(osv.osv_memory):
    _name = "wizard.ca.par.representant"
    _description = "Wizard pour le C.A et le poids vendu par représentant"

    _columns = {
        'representant_deb_ref': fields.many2one('res.users', string="Représentant début", required=True, 
            help="Permet de sélectionner le représentant de début sur lesquel étudier le C.A."),
        'representant_fin_ref': fields.many2one('res.users', string="Représentant fin", required=True, 
            help="Permet de sélectionner le représentant de début sur lesquel étudier le C.A."),
        'annee_debut': fields.integer(string='Année de début', size=4, required=True, 
            help="Date à partir de laquelle nous effectuons le suivi."),
        'annee_fin': fields.integer(string='Année de fin', size=4, required=True, 
            help="Date jusqu'à laquelle nous effectuons le suivi."),
        'tous_representants': fields.boolean(string="Tous les représentants ?"),
    }

    _defaults = {
        'annee_debut': lambda *a: int(time.strftime('%Y')),
        'annee_fin': lambda *a: int(time.strftime('%Y')),
        'tous_representants': lambda *a: False,
    }

    def creation_lignes_annee(self, cr, uid, ids, date_deb=None, date_fin=None, total=False, context={}):
        """
        Crée des lignes de 'edition_ca_par_representant'.
        NB: 
         - ids : liste d'identifiant des représentants
         - total : définit si la ligne est une ligne de total final ou pas
        """
        # Vérification des valeurs fournies
        if not ids:
            raise osv.except_osv(_('Erreur'), _('Paramètre manquant.'))
        if isinstance(ids, (int, long)):
            ids = [ids]
        if not date_deb and not date_fin:
            raise osv.except_osv(_('Erreur'), _('Il manque une ou plusieurs dates.'))
        # Préparation de certains objets
        ecpr_obj = self.pool.get('edition.ca.par.representant')
        sql = """SELECT SUM(ai.amount_total) AS ca, SUM(ail.quantity) AS qte, COUNT(ai.partner_id) AS CLI
            FROM account_invoice AS ai, account_invoice_line AS ail
            WHERE ai.state in ('open', 'paid')
            AND ai.user_id in %s
            AND ail.invoice_id = ai.id
            AND ai.date_invoice >= %s
            AND ai.date_invoice <= %s;
        """
        # On boucle sur chaque année
        for annee in range(date_deb, date_fin+1, 1):
            # initialisation de quelques valeurs
            total_repr_annee = 0
            total_repr_qte_annee = 0
            total_repr_clt_annee = 0
            repr_annee_vals = {}        # données pour le total de l'année pour le C.A
            repr_annee_qte_vals = {}    # données pour le total de l'année pour le poids/quantité
            repr_annee_clt_vals = {}    # données pour le total de l'année pour le nombre de clients
            # puis on boucle sur chaque mois pour un représentant donné
            for mois in range (1, 13, 1):
                # création des dates de début et de fin
                periode_deb = str(annee) + '-' + str(mois) + '-' + '01'
                periode_fin = str(annee) + '-' + str(mois) + '-' + str(calendar.monthrange(annee, mois)[1])
                # execution SQL
                cr.execute(sql, (tuple(ids), str(periode_deb), str(periode_fin)))
                res = cr.fetchall()
                # récupération des données
                chiffre_affaire = (res[0][0] and res[0][0]) or 0.0
                quantite = (res[0][1] and res[0][1]) or 0.0
                clt = (res[0][2] and res[0][2]) or 0.0
                champ = 'mois' + str(mois)
                # mise à jour des lignes
                repr_annee_vals.update({champ: str(chiffre_affaire)})
                repr_annee_qte_vals.update({champ: str(quantite)})
                repr_annee_clt_vals.update({champ: str(clt)})
                # mise à jour des totaux
                total_repr_annee += chiffre_affaire
                total_repr_qte_annee += quantite
                total_repr_clt_annee += clt
            # On complète les données avant de les ajouter
            designation_deb = '- ' + str(annee) + ' '
            if total:
                designation_deb = '* - ' + str(annee) + ' '
            designation_ca = designation_deb + 'C.A.'
            designation_qte = designation_deb + 'QTÉ'
            designation_clt = designation_deb + 'N.CLI'
            repr_annee_vals.update({'designation': designation_ca, 'total': str(total_repr_annee)})
            repr_annee_qte_vals.update({'designation': designation_qte, 'total': str(total_repr_qte_annee)})
            repr_annee_clt_vals.update({'designation': designation_clt, 'total': str(total_repr_clt_annee)})
            # Ajout des lignes
            ecpr_obj.create(cr, uid, repr_annee_vals, context=context)
            ecpr_obj.create(cr, uid, repr_annee_qte_vals, context=context)
            ecpr_obj.create(cr, uid, repr_annee_clt_vals, context=context)
        return True

    def action_confirmer(self, cr, uid, ids, context={}):
        """
        Valide les données saisies et renvoie le C.A par mois pour chaque année donnée dans la plage citée.
        """
        # Récupération des données
        user_obj = self.pool.get('res.users')
        wizard = self.browse(cr, uid, ids[0], context=context)
        representant_deb = None
        representant_fin = None
        if wizard.representant_deb_ref and wizard.representant_deb_ref.code_saler:
            representant_deb = wizard.representant_deb_ref.code_saler
        if wizard.representant_fin_ref and wizard.representant_fin_ref.code_saler:
            representant_fin = wizard.representant_fin_ref.code_saler
        if not representant_deb or not representant_fin:
            raise osv.except_osv(_('Erreur'), _("Le champ 'Code Vendeur' est manquant pour l'un des représentant sélectionné."))
        representant_fin = wizard.representant_fin_ref.code_saler
        tous_representants = wizard.tous_representants
        representant_ids = user_obj.search(cr, uid, [('code_saler', '>=', representant_deb), ('code_saler', '<=', representant_fin)])
        if tous_representants:
            representant_ids = user_obj.search(cr, uid, [], context=context)
        if not representant_ids:
            raise osv.except_osv(_('Erreur'), _('Aucun représentant trouvé.'))
        date_deb = wizard.annee_debut
        date_fin = wizard.annee_fin
        # Vérification de la validité des données
        if date_fin < date_deb:
            raise osv.except_osv(_('Attention'), _('La date de fin saisie doit être supérieure à celle de début !'))
        # Préparation de certaines données
        ecpr_obj = self.pool.get('edition.ca.par.representant')
        representants = user_obj.browse(cr, uid, representant_ids, context=context)
        # TODO: AJOUTER ICI TOUS LES REPRESENTANTS SI LA CASE A ÉTÉ COCHÉE
        # on vide la table osv_memory entière
        ecpr_ids = ecpr_obj.search(cr, uid, [], context=context)
        ecpr_obj.unlink(cr, uid, ecpr_ids, context=context)
        # On boucle sur chaque représentant
        for representant in representants:
            # Initialisation de quelques valeurs
            total_repr = 0          # total C.A du représentant pour la période donnée
            total_repr_qte = 0      # total du poids des ventes effectuées par le représentant
            total_repr_clt = 0      # total du nombre de clients différents que ce vendeur a réussi à obtenir/vendre
            # On veut obtenir la ligne suivante (répartie sur la premier colonne, puis les suivantes en laissant la colonne 2 libres) : 
            # REPRÉSENTANT : 1  GREINER  JEAN  PIERRE  N
            repr_vals = {'designation': 'REPRÉSENTANT ' + str(representant.code_saler or None) + ' : ' + str(representant.name[:100])}
            ecpr_obj.create(cr, uid, repr_vals, context=context)
            # On ajoute les lignes pour le représentant
            self.creation_lignes_annee(cr, uid, [representant.id], date_deb, date_fin, total=False, context=context)

        # On s'occupe de la ligne de total de la fin de l'édition
        ecpr_obj.create(cr, uid, {'designation': '* TOTAL : '}, context=context)
        self.creation_lignes_annee(cr, uid, [x.id for x in representants], date_deb, date_fin, total=True, context=context)

        # Récupération de l'id de la vue à afficher
        irmd_obj = self.pool.get('ir.model.data')
        view_ids = irmd_obj.search(cr, uid, [('name', '=', 'edition_ca_par_representant_tree'), ('model', '=', 'ir.ui.view')])
        # Préparation de l'élément permettant de trouver la vue à  afficher
        if view_ids:
            view = irmd_obj.read(cr, uid, view_ids[0])
            view_id = (view.get('res_id'), view.get('name'))
        else:
            raise osv.except_osv(_('Erreur'), _("Impossible d'afficher le résultat : vue non trouvée."))
        return {
            'type': 'ir.actions.act_window',
                'res_model': 'edition.ca.par.representant',
                'view_type': 'form',
                'view_mode': 'tree,form',
                'view_id': view_id,
                }

wizard_ca_par_representant()

class edition_ca_par_representant(osv.osv_memory):
    _name = "edition.ca.par.representant"
    _description = "Edition du C.A/POIDS par representant et par an."

    _order = 'id asc'

    _columns = {
        'designation': fields.char(string="Désignation", size=122, help="Libellé de la ligne", required=True),
        'mois1': fields.char(string="JAN", size=10),
        'mois2': fields.char(string="FÉV", size=10),
        'mois3': fields.char(string="MAR", size=10),
        'mois4': fields.char(string="AVR", size=10),
        'mois5': fields.char(string="MAI", size=10),
        'mois6': fields.char(string="JUIN", size=10),
        'mois7': fields.char(string="JUIL", size=10),
        'mois8': fields.char(string="AOÛ", size=10),
        'mois9': fields.char(string="SEP", size=10),
        'mois10': fields.char(string="OCT", size=10),
        'mois11': fields.char(string="NOV", size=10),
        'mois12': fields.char(string="DÉC", size=10),
        'total': fields.char(string="TOTAL", size=30),
    }

edition_ca_par_representant()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
