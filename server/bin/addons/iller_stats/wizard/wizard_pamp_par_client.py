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

class wizard_pamp_par_client(osv.osv_memory):
    _name = "wizard.pamp.par.client"
    _description = "P.A.M.P. par client et par article sur une periode"

    _columns = {
        'partner_deb_id': fields.many2one('res.partner', string="Client de début", required=True, 
            help="Code client à partir duquel nous commençons le traitement"),
        'partner_fin_id': fields.many2one('res.partner', string="Client de fin", required=True,
            help="Code client jusqu'auquel aller pour l'édition"),
        'date_debut': fields.date(string="Date de début", help="Date de début de la période sur laquelle chercher.", required=True),
        'date_fin': fields.date(string="Date de fin", help="Date de fin de la période sur laquelle chercher.", required=True),
    }

    _defaults= {
        'date_fin': lambda *a: time.strftime('%Y-%m-%d'),
    }

    def action_confirmer(self, cr, uid, ids, context={}):
        """
        Valide les données saisies, remplit les lignes d'un tableau pour édition et renvoie la vue contenant les données résultantes.
        """
        # Vérification des éléments
        wizard = self.browse(cr, uid, ids[0], context=context)
        clt_deb_ref = wizard.partner_deb_id.ref
        clt_fin_ref = wizard.partner_fin_id.ref
        if clt_fin_ref < clt_deb_ref:
            raise osv.except_osv(_('Attention'), _('La référence du partenaire de fin doit être supérieure à celle du partenaire de début !'))
        # vérification des dates
        if wizard.date_fin1 < wizard.date_debut1:
            raise osv.except_osv(_('Erreur'), _('La date de fin de la période 1 doit être antérieure à celle de début.'))
        # Préparation des données
        partner_obj = self.pool.get('res.partner')
        partner_ids = partner_obj.search(cr, uid, [('ref', '>=', clt_deb_ref), ('ref', '<=', clt_fin_ref)])
        if not partner_ids:
            raise osv.except_osv(_('Information'), _('Aucun client trouvé.'))
        eppc_obj = self.pool.get('edition.pamp.par.client')
        prod_obj = self.pool.get('product.product')
        # On vide la table d'éléments déjà existants
        eppc_ids = eppc_obj.search(cr, uid, [], context=context)
        eppc_obj.unlink(cr, uid, eppc_ids, context=context)
        # On traite chaque client
        for partner in partner_obj.browse(cr, uid, partner_ids, context=context):
            sql = """SELECT *, (marge/ca*100) AS pourcent FROM
                (SELECT id, qte, val_cons, ca, (ca - val_cons) AS marge
                    FROM
                        (SELECT p.id, SUM(ail.quantity) AS qte, SUM(ail.quantity*pt.standard_price) AS val_cons, SUM(ail.price_subtotal) AS ca
                        FROM account_invoice_line AS ail, account_invoice AS ai, product_product AS p, product_template AS pt
                        WHERE ail.invoice_id = ai.id
                        AND ail.product_id = p.id
                        AND p.product_tmpl_id = pt.id
                        AND ai.state in ('open', 'paid')
                        AND ai.partner_id = %s
                        GROUP BY p.id
                        ORDER BY p.id)
                    AS ma_table)
                AS super_table;"""
            cr.execute(sql, (partner.id,))
            res = cr.fetchall()
            if not res:
                continue
            designation = partner.ref + ' ' + partner.name
            if partner.address and partner.address[0].name:
                designation += ' ' + partner.address[0].name
            if partner.address and partner.address[0].zip:
                designation += ' ' + partner.address[0].zip
            if partner.address and partner.address[0].city:
                designation += ' ' + partner.address[0].city
            partner_vals = {
                'designation': designation,
                'est_client': True,
            }
            eppc_obj.create(cr, uid, partner_vals, context=context)
            for element in res:
                prod_id = element[0]
                qte = element[1]
                val_cons = element[2]
                ca = element[3]
                marge = element[4]
                pourcent = element[5]
                produit = prod_obj.browse(cr, uid, [prod_id], context=context)[0]
                vals = {
                    'designation': produit.default_code + ' ' + produit.name,
                    'quantite': qte,
                    'val_cons': val_cons,
                    'ca_ht': ca,
                    'marge': marge,
                    'marge_sur_ca': round(pourcent, 2),
                }
                eppc_obj.create(cr, uid, vals, context=context)

        # Récupération de l'id de la vue à afficher
        irmd_obj = self.pool.get('ir.model.data')
        view_ids = irmd_obj.search(cr, uid, [('name', '=', 'edition_pamp_par_client_tree'), ('model', '=', 'ir.ui.view')])
        # Préparation de l'élément permettant de trouver la vue à  afficher
        if view_ids:
            view = irmd_obj.read(cr, uid, view_ids[0])
            view_id = (view.get('res_id'), view.get('name'))
        else:
            raise osv.except_osv(_('Erreur'), _("Impossible d'afficher le résultat : vue non trouvée."))
        return {
            'type': 'ir.actions.act_window',
                'res_model': 'edition.pamp.par.client',
                'view_type': 'form',
                'view_mode': 'tree,form',
                'view_id': view_id,
                }

wizard_pamp_par_client()

class edition_pamp_par_client(osv.osv_memory):
    _name = "edition.pamp.par.client"
    _description = "Edition P.A.M.P / client / article sur 1 periode"

    _order = 'id asc'

    _columns = {
        'designation': fields.char(string="Désignation", size=100, required=True),
        'quantite': fields.char(string="Quantité", size=15),
        'val_cons': fields.char(string="Val. cons.", size=15),
        'ca_ht': fields.char(string="CA. HT", size=15),
        'marge': fields.char(string="Marge", size=15),
        'marge_sur_ca': fields.char(string="% Marge / CA HT", size=15),
        'est_client': fields.boolean(string="Est un client ?"),
    }

    _defaults = {
        'est_client': lambda *a: False,
    }

edition_pamp_par_client()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
