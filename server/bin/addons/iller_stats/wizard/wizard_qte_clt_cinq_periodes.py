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

class wizard_qte_clt_cinq_periodes(osv.osv_memory):
    _name = "wizard.qte.clt.cinq.periodes"
    _description = "Wizard quantite commandee par client et par article"

    _columns = {
        'partner_deb_id': fields.many2one('res.partner', string="Client de début", required=True, 
            help="Code client à partir duquel nous commençons le traitement"),
        'partner_fin_id': fields.many2one('res.partner', string="Client de fin", required=True,
            help="Code client jusqu'auquel aller pour l'édition"),
        'date_debut1': fields.date(string="Date de début", help="Date de début de la période sur laquelle chercher.", required=True),
        'date_fin1': fields.date(string="Date de fin", help="Date de fin de la période sur laquelle chercher.", required=True),
        'date_debut2': fields.date(string="Date de début", help="Date de début de la période sur laquelle chercher.", required=True),
        'date_fin2': fields.date(string="Date de fin", help="Date de fin de la période sur laquelle chercher.", required=True),
        'date_debut3': fields.date(string="Date de début", help="Date de début de la période sur laquelle chercher.", required=True),
        'date_fin3': fields.date(string="Date de fin", help="Date de fin de la période sur laquelle chercher.", required=True),
        'date_debut4': fields.date(string="Date de début", help="Date de début de la période sur laquelle chercher.", required=True),
        'date_fin4': fields.date(string="Date de fin", help="Date de fin de la période sur laquelle chercher.", required=True),
        'date_debut5': fields.date(string="Date de début", help="Date de début de la période sur laquelle chercher.", required=True),
        'date_fin5': fields.date(string="Date de fin", help="Date de fin de la période sur laquelle chercher.", required=True),
    }

    _defaults= {
        'date_fin1': lambda *a: time.strftime('%Y-%m-%d'),
        'date_fin2': lambda *a: time.strftime('%Y-%m-%d'),
        'date_fin3': lambda *a: time.strftime('%Y-%m-%d'),
        'date_fin4': lambda *a: time.strftime('%Y-%m-%d'),
        'date_fin5': lambda *a: time.strftime('%Y-%m-%d'),
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
        if wizard.date_fin2 < wizard.date_debut2:
            raise osv.except_osv(_('Erreur'), _('La date de fin de la période 2 doit être antérieure à celle de début.'))
        if wizard.date_fin3 < wizard.date_debut3:
            raise osv.except_osv(_('Erreur'), _('La date de fin de la période 3 doit être antérieure à celle de début.'))
        if wizard.date_fin4 < wizard.date_debut4:
            raise osv.except_osv(_('Erreur'), _('La date de fin de la période 4 doit être antérieure à celle de début.'))
        if wizard.date_fin5 < wizard.date_debut5:
            raise osv.except_osv(_('Erreur'), _('La date de fin de la période 5 doit être antérieure à celle de début.'))
        # Préparation des données
        partner_obj = self.pool.get('res.partner')
        partner_ids = partner_obj.search(cr, uid, [('ref', '>=', clt_deb_ref), ('ref', '<=', clt_fin_ref)])
        if not partner_ids:
            raise osv.except_osv(_('Information'), _('Aucun client trouvé.'))
        eqccp_obj = self.pool.get('edition.qte.clt.cinq.periodes')
        prod_obj = self.pool.get('product.product')
        # On vide la table d'éléments déjà existants
        eqccp_ids = eqccp_obj.search(cr, uid, [], context=context)
        eqccp_obj.unlink(cr, uid, eqccp_ids, context=context)
        # On traite chaque client
        for partner in partner_obj.browse(cr, uid, partner_ids, context=context):
            sql_produits = """SELECT p.id
                FROM account_invoice_line AS ail, account_invoice AS ai, product_product AS p
                WHERE ail.invoice_id = ai.id
                AND ail.product_id = p.id
                AND ai.partner_id = %s
                AND ai.state in ('open', 'paid')
                AND date_invoice >= %s
                AND date_invoice <= %s
                GROUP BY p.id
                ORDER BY p.id
            """
            sql_qte = """SELECT SUM(ail.quantity) AS qte
                FROM account_invoice_line AS ail, account_invoice AS ai, product_product AS p
                WHERE ail.invoice_id = ai.id
                AND ail.product_id = p.id
                AND ai.partner_id = %s
                AND ai.state in ('open', 'paid')
                AND date_invoice >= %s
                AND date_invoice <= %s
                GROUP BY p.default_code
                ORDER BY p.default_code;
            """
            # Identifiants des articles pour la période 1
            prod_periode1 = []
            cr.execute(sql_produits, (partner.id, wizard.date_debut1, wizard.date_fin1,))
            prod_periode1 = [x[0] for x in cr.fetchall()]
            # Identifiants des articles pour la période 2
            prod_periode2 = []
            cr.execute(sql_produits, (partner.id, wizard.date_debut2, wizard.date_fin2,))
            prod_periode2 = [x[0] for x in cr.fetchall()]
            # Identifiants des articles pour la période 3
            prod_periode3 = []
            cr.execute(sql_produits, (partner.id, wizard.date_debut3, wizard.date_fin3,))
            prod_periode3 = [x[0] for x in cr.fetchall()]
            # Identifiants des articles pour la période 4
            prod_periode4 = []
            cr.execute(sql_produits, (partner.id, wizard.date_debut4, wizard.date_fin4,))
            prod_periode4 = [x[0] for x in cr.fetchall()]
            # Identifiants des articles pour la période 5
            prod_periode5 = []
            cr.execute(sql_produits, (partner.id, wizard.date_debut5, wizard.date_fin5,))
            prod_periode5 = [x[0] for x in cr.fetchall()]
            # On concatène tous les identifiants puis on les trie
            prod_periodes_ids = prod_periode1 + prod_periode2 + prod_periode3 + prod_periode4 + prod_periode5
            var_tmp = {}
            for i in prod_periodes_ids:
                try: var_tmp[i] += 1
                except KeyError: var_tmp[i] = 1
            prod_ids = var_tmp.keys()
            prod_ids.sort()
            if prod_ids:
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
                eqccp_obj.create(cr, uid, partner_vals, context=context)
            for product in prod_obj.browse(cr, uid, prod_ids, context=context):
                vals = {'designation': product.default_code + ' ' + product.name}
                # On cherche les quantités pour chaque période
                for date_deb, date_fin, champ in [(wizard.date_debut1, wizard.date_fin1, 'periode1'), 
                    (wizard.date_debut2, wizard.date_fin2, 'periode2'), 
                    (wizard.date_debut3, wizard.date_fin3, 'periode3'), 
                    (wizard.date_debut4, wizard.date_fin4, 'periode4'), 
                    (wizard.date_debut5, wizard.date_fin5, 'periode5')]:
                    cr.execute(sql_qte, (partner.id, date_deb, date_fin,))
                    res = cr.fetchall()
                    if res:
                        vals.update({champ: int(res[0][0])})
                eqccp_obj.create(cr, uid, vals, context=context)
        # Récupération de l'id de la vue à afficher
        irmd_obj = self.pool.get('ir.model.data')
        view_ids = irmd_obj.search(cr, uid, [('name', '=', 'edition_qte_clt_cinq_periodes_tree'), ('model', '=', 'ir.ui.view')])
        # Préparation de l'élément permettant de trouver la vue à  afficher
        if view_ids:
            view = irmd_obj.read(cr, uid, view_ids[0])
            view_id = (view.get('res_id'), view.get('name'))
        else:
            raise osv.except_osv(_('Erreur'), _("Impossible d'afficher le résultat : vue non trouvée."))
        context = {
            'periode1': wizard.date_debut1 + '\n' + wizard.date_fin1,
            'periode2': wizard.date_debut2 + '\n' + wizard.date_fin2,
            'periode3': wizard.date_debut3 + '\n' + wizard.date_fin3,
            'periode4': wizard.date_debut4 + '\n' + wizard.date_fin4,
            'periode5': wizard.date_debut5 + '\n' + wizard.date_fin5,
        }
        return {
            'type': 'ir.actions.act_window',
                'res_model': 'edition.qte.clt.cinq.periodes',
                'view_type': 'form',
                'view_mode': 'tree,form',
                'view_id': view_id,
                'context': context,
                }

wizard_qte_clt_cinq_periodes()

class edition_qte_clt_cinq_periodes(osv.osv_memory):
    _name = "edition.qte.clt.cinq.periodes"
    _description = "Quantite commandee / client / article sur 5 periodes"

    _order = 'id asc'

    _columns = {
        'designation': fields.char(string="Désignation", size=100, required=True),
        'periode1': fields.integer(string="Période 1", required=True),
        'periode2': fields.integer(string="Période 2", required=True),
        'periode3': fields.integer(string="Période 3", required=True),
        'periode4': fields.integer(string="Période 4", required=True),
        'periode5': fields.integer(string="Période 5", required=True),
        'est_client': fields.boolean(string="Est un client ?"),
    }

    _defaults = {
        'est_client': lambda *a: False,
    }

    def fields_view_get(self, cr, uid, view_id=None, view_type='tree', context=None, toolbar=False):
        """
        Remplace les champs "periode1" à "periode5" par les périodes données dans le contexte
        """
        # Récupération
        res = super(edition_qte_clt_cinq_periodes, self).fields_view_get(cr, uid, view_id, view_type, context, toolbar)
        # Mise à jour des champs
        if 'fields' in res:
            fields = res.get('fields')
            for i in range(1, 6, 1):
                periode = 'periode' + str(i)
                if periode in fields and context.get(periode, False):
                    periode_arch = fields.get(periode)
                    res.get('fields').get(periode).update({'string': context.get(periode)})
        return res

edition_qte_clt_cinq_periodes()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
