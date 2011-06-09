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

class wizard_articles_par_client(osv.osv_memory):
    _name = "wizard.articles.par.client"

    _columns = {
        'partner_ids': fields.many2many('res.partner', 'wiz_art_clt_rel', 'wizard_id', 'partner_id', string="Client(s)", help="Choisir les clients dont vous \
            désirez éditer les articles. Maintenez la touche CTRL de votre clavier pour en sélectionner plusieurs. Utilisez la touche majuscule pour \
            sélectionner une plage de clients.", required=True),
        'date_debut': fields.date(string="Date de début", help="Date de début de la période sur laquelle chercher les articles  pour un ou plusieurs clients \
            donnés.", required=True),
        'date_fin': fields.date(string="Date de fin", help="Date de fin de la période sur laquelle chercher les articles pour un ou plusieurs clients \
            donnés.", required=True),
        'est_decoupe': fields.boolean(string="Découpe uniquement ?", help="Cochez cette case pour n'afficher que les articles provenant de la découpe."),
        'famille_uniquement': fields.boolean(string="Uniquement les familles ?", help="Cochez cette case pour n'afficher que le total pour chaque famille \
            d'articles pour un ou plusieurs clients donnés."),
        'exclusion_magasin': fields.boolean(string="Exclusion magasin, code 090300 ?", help="Cochez cette case pour exclure le code 090300 (magasin)"),
    }

    _defaults = {
        'date_fin': lambda *a: time.strftime('%Y-%m-%d'),
        'est_decoupe': lambda *a: False,
        'famille_uniquement': lambda *a: False,
        'exclusion_magasin': lambda *a: False,
    }

    def action_confirmer(self, cr, uid, ids, context={}):
        """
        Vérifie les données saisies puis renvoie la liste des articles des clients choisis
        """
        # Préparation des variables
        if isinstance(ids, (int, long)):
            ids = [ids]
        wizard = self.browse(cr, uid, ids[0], context=context)
        partner_ids = [x.id for x in wizard.partner_ids] or []
        date_deb = wizard.date_debut
        date_fin = wizard.date_fin
        decoupe_seulement = wizard.est_decoupe or False
        famille_seulement = wizard.famille_uniquement or False
        exclue_magasin = wizard.exclusion_magasin or False

        if date_fin <= date_deb:
            raise osv.except_osv(_('Attention'), _('La date de fin doit être supérieure à celle de début.'))

        # Recherche des éléments à afficher suivant les paramètres suivant :
        # - factures de type "out_invoice" (sortie, donc que pour les clients)
        # - suivant les clients données par l'utilisateur dans le wizard
        # - supérieur à la date de début donnée
        # - inférieur à la date de fin donnée
        sql = """SELECT c.id AS categ_id, p.id AS p_id, p.default_code, pt.name, COUNT(ail.quantity) AS quantity, SUM(ail.price_unit*ail.quantity) AS total, AVG(ail.discount) AS remise
                FROM product_product AS p, account_invoice_line AS ail, account_invoice AS ai, product_template AS pt, product_category AS c
                WHERE ail.invoice_id = ai.id
                AND ail.product_id = p.id
                AND ail.product_id = pt.id
                AND pt.categ_id = c.id
                AND ai.state in ('open', 'paid')
                AND ai.date_invoice >= %s
                AND ai.date_invoice <= %s
                AND ai.partner_id in %s
                AND pt.categ_id = %s
                GROUP BY c.id, p.id, p.default_code, pt.name
                ORDER BY p.id;"""
        sql_decoupe = """SELECT c.id AS categ_id, p.id AS p_id, p.default_code, pt.name, COUNT(ail.quantity) AS quantity, SUM(ail.price_unit*ail.quantity) AS total, AVG(ail.discount) AS remise
                FROM product_product AS p, account_invoice_line AS ail, account_invoice AS ai, product_template AS pt, product_category AS c
                WHERE ail.invoice_id = ai.id
                AND ail.product_id = p.id
                AND ail.product_id = pt.id
                AND pt.categ_id = c.id
                AND ai.state in ('open', 'paid')
                AND ai.date_invoice >= %s
                AND ai.date_invoice <= %s
                AND ai.partner_id in %s
                AND pt.categ_id = %s
                AND p.code_affectation = 'DECP'
                GROUP BY c.id, p.id, p.default_code, pt.name
                ORDER BY p.id;"""

        # On cherche l'ensemble des familles
        cat_obj = self.pool.get('product.category')
        apc_obj = self.pool.get('articles.par.client')
        cat_ids = cat_obj.search(cr, uid, [], context=context, order="id")
        # on vide la table osv_memory entière avant de la remplir avec les articles cherchés
        apc_ids = apc_obj.search(cr, uid, [], context=context)
        apc_obj.unlink(cr, uid, apc_ids, context=context)
        # On parcours chaque famille pour afficher les produits du résultat qui correspondent
        total_qte = 0
        total = 0
        for cat in cat_obj.browse(cr, uid, cat_ids, context=context):
            requete = sql
            if decoupe_seulement:
                requete = sql_decoupe
            cr.execute(requete, (str(date_deb), str(date_fin), tuple(partner_ids), str(cat.id),))
            res = cr.fetchall()
            # On s'occupe des produits de la catégorie
            for el in res:
                # récupération des valeurs
                cat_id = el[0]
                p_id = el[1]
                p_code = el[2]
                p_name = el[3]
                qte = el[4]
                ca = el[5]
                remise = el[6]
                prix_moyen = ca / qte
                # On saute le produit 090300 si c'est demandé en option
                if p_code == '090300' and exclue_magasin:
                    continue
                vals = {
                    'nom': p_code + ' ' + p_name,
                    'quantite': qte,
                    'ca_net': ca,
                    'prix_moyen': round(prix_moyen, 3),
                    'remise': remise,
                }
                # On ne crée pas les lignes produits si l'utilisateur a coché "Uniquement les familles"
                if not famille_seulement:
                    apc_obj.create(cr, uid, vals, context=context)
                total += ca
                total_qte += qte
            if total > 0:
                famille_vals = {
                    # nom = 10 espaces + TOTAL FAMILLE + nom de la catégorie
                    'nom': " * * * " + "TOTAL FAMILLE : " + cat.name + " * * * ",
                    'quantite': total_qte,
                    'ca_net': total,
                    'est_total': True,
                }
                apc_obj.create(cr, uid, famille_vals, context=context)
            # on remet les totals à 0 pour la catégorie suivante
            total_qte = 0
            total = 0
        # Récupération de l'id de la vue à afficher
        irmd_obj = self.pool.get('ir.model.data')
        view_ids = irmd_obj.search(cr, uid, [('name', '=', 'articles_par_client_tree'), ('model', '=', 'ir.ui.view')])
        # Préparation de l'élément permettant de trouver la vue à  afficher
        if view_ids:
            view = irmd_obj.read(cr, uid, view_ids[0])
            view_id = (view.get('res_id'), view.get('name'))
        else:
            raise osv.except_osv(_('Erreur'), _("Impossible d'afficher le résultat : vue non trouvée."))
        return {
            'type': 'ir.actions.act_window',
                'res_model': 'articles.par.client',
                'view_type': 'form',
                'view_mode': 'tree,form',
                'view_id': view_id,
                }

wizard_articles_par_client()

class articles_par_client(osv.osv_memory):
    _name = "articles.par.client"
    _description = "Edition des articles par client"
    _order = "id"

    _columns = {
        'nom': fields.char(string="Désignation", size=255, help="Code + Nom du produit", required=True),
        'quantite': fields.integer(string="Quantité", required=True),
        'ca_net': fields.integer(string="C.A. Net", required=True),
        'prix_moyen': fields.integer(string="Prix moyen"),
        'remise': fields.integer(string="Remise en %"),
        'est_total': fields.boolean(string="Ligne = total famille ?", help="Définit si la ligne est un total famille ou pas."),
    }

    _defaults = {
        'est_total': lambda *a: False,
    }

articles_par_client()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
