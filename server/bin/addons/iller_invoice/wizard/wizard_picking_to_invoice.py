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

from osv import osv
from osv import fields
from datetime import datetime, timedelta
from tools.translate import _
import calendar

class wizard_picking_to_invoice(osv.osv_memory):
    _name = 'wizard.picking.to.invoice'

    _columns = {
        'journal_id': fields.many2one('account.journal', string="Journal de destination", required=True),
    }

    def _get_last_date_from(self, cr, uid, mode=None, context={}):
        """
        Donne la date actuelle retranchée d'un nombre X de jours selon :
         + m: un mois avant
         + s: une semaine avant (7 jours)
         + d: 10 jours avant
         + r: ce jour
        Sinon ne retourne rien
        @mode : mode de paiement du client (m, s, d, r ou autre)
        """
        # Initialisation de variables
        last_date = False
        if mode:
            # Date du jour
            ce_jour = datetime.today()
            # On crée la date en fonction du mode de paiement
            if mode == 'm':
                # Vérification du mois d'avant dans le cas où mois = 1
                mois = ce_jour.month-1
                annee = ce_jour.year
                if ce_jour.month == 1:
                    mois = 12
                    annee = ce_jour.year-1
                # Vérification du dernier jour du mois d'avant
                dernier_jour = calendar.monthrange(annee, mois)[1]
                jour = ce_jour.day
                if jour > dernier_jour:
                    jour = dernier_jour
                last_date = datetime(annee, mois, jour)
            elif mode == 's':
                last_date = ce_jour - timedelta(days=7)
            elif mode =='d':
                last_date = ce_jour - timedelta(days=10)
            elif mode == 'r':
                last_date = ce_jour
        return last_date

    def action_make_invoices(self, cr, uid, ids, context={}):
        """
        Génération des factures pour chaque client en fonction de leur délai de
        paiement.
        """
        if isinstance(ids, (int, long)):
            ids = [ids]
        # TODO: Faire la boucle en prenant tout les partenaires de la table 
        #+ stock_picking ayant des bons de livraisons en état terminé et à 
        #+ facturer.
        # Préparation d'éléments
        res_partner_obj = self.pool.get('res.partner')
        # On récupère tout les clients (id + mode de facturation) trié par id
        res = res_partner_obj.search(cr, uid, [('customer', '=', 't')], order='id ASC', context=context)
        # Début de traitement que dans le cas où la requête renvoie un résultat
        if res:
            # liste des clients sans mode de paiement
            client_sans_mode = []
            # liste des bons de livraisons terminées et à facturer par client
            bon_a_facturer = {}
            for client in res_partner_obj.browse(cr, uid, res, context=context):
                client_id = client.id or False
                client_mode = client.facturation_bl or False
                # Si le mode de facturation est renseigné on commence la 
                #+ vérification
                if client_mode:
                    # Recherche de toutes les préparations de ce client non 
                    #+ facturées
                    last_date = self._get_last_date_from(cr, uid, client_mode, context=context)
                    # Si pas de date retournée, on ajoute le client dans la 
                    #+ liste de ceux n'ayant aucun mode de paiement puis on 
                    #+ passe au client suivant (#INTERRUPTION de la boucle)
                    if not last_date:
                        client_sans_mode.append(client_id)
                        continue
                    # Récupération des livraisons à facturer
                    sp_obj = self.pool.get('stock.picking')
                    sp_ids = sp_obj.search(cr, uid, [('invoice_state', '=', '2binvoiced'), ('address_id.partner_id', '=', client_id), ('state', '=', 'done')]) or None
                    # Tri des éléments à facturer
                    if sp_ids:
                        bon_du_client = []
                        for sp_id in sp_ids:
                            # Recherche des dates du bon de livraison
                            sp_date = datetime.strptime(sp_obj.read(cr, uid, sp_id, ['date_done']).get('date_done'), '%Y-%m-%d %H:%M:%S')
                            # Si la date de la facture est inférieure à 
                            #+ last_date, alors on récupère l'identifiant de la
                            #+ livraison
                            if sp_date < last_date:
                                # Ajout du bon de livraison dans les éléments à 
                                #+ facturer du client
                                bon_du_client.append(sp_id)
                        # Si le client possède des éléments à facturer, on 
                        #+ l'ajoute dans la liste des 'bon_a_facturer'
                        if bon_du_client:
                            bon_a_facturer[client_id] = bon_du_client
                else:
                    client_sans_mode.append(client_id)
        # Début de la facturation si une liste a été fournie (bon_a_facturer)
        bon_reussis = []
        if bon_a_facturer:
            # Préparation de certains éléments
            wizard = self.browse(cr, uid, ids)[0]
            journal_id = wizard.journal_id.id
            for bon in bon_a_facturer:
                factures_reussies = sp_obj.action_invoice_create(cr, uid, bon_a_facturer[bon], journal_id, group=True, type='out_invoice', context=context)
                # On ajoute les valeurs de la liste de factures réussies
                bon_reussis += factures_reussies.values()
        if bon_reussis:
            domain = [('id', 'in', bon_reussis)]
            return { 'type': 'ir.actions.act_window',
                    'res_model': 'account.invoice',
                    'view_type': 'form',
                    'view_mode': 'tree,form',
                    'domain': domain,
            }
        else:
            raise osv.except_osv(_('Information'), _("Aucun bon de livraison n'a été facturé !"))

wizard_picking_to_invoice()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
