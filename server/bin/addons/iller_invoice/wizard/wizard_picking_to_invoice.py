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
import threading
import pooler
import base64
import time
import netsvc
from tools import ustr


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

    def _generation_factures(self, cr, uid, ids, clients=[], context={}):
        """
        Renvoie une chaîne décrivant de manière assez détaillée le 
        résultat - positif ou négatif - de la création des factures 
        pour chaque client en fonction de leur délai de paiement.
        """
        # Vérifications diverses
        if isinstance(ids, (int, long)):
            ids = [ids]
        if not len(clients):
            return False

        # Préparation des éléments
        res = ''
        res_partner_obj = self.pool.get('res.partner')
        so_obj = self.pool.get('stock.picking')
        partner_address_obj = self.pool.get('res.partner.address')
        inv_obj = self.pool.get('account.invoice')

        # Début de traitement
        # liste des clients sans mode de paiement
        client_sans_mode = []
        # liste des bons de livraisons terminées et à facturer par client
        bon_a_facturer = {}
        print """###
            Processus de génération des factures à partir des bons d'expéditions 
            suivant le délai de paiement des clients : débuté."""
        for client in res_partner_obj.browse(cr, uid, clients, context=context):
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
                sp_ids = so_obj.search(cr, uid, [('invoice_state', '=', '2binvoiced'), 
                    ('address_id.partner_id', '=', client_id), ('state', '=', 'done')]) or None

                # Tri des éléments à facturer
                if sp_ids:
                    bon_du_client = []
                    for sp_id in sp_ids:
                        # Recherche des dates du bon de livraison
                        sp_date = datetime.strptime(so_obj.read(cr, uid, sp_id, ['date_done']).get('date_done'), 
                            '%Y-%m-%d %H:%M:%S')
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
        bon_non_reussis = []
        if bon_a_facturer:
            # Préparation de certains éléments
            wizard = self.browse(cr, uid, ids)[0]
            journal_id = wizard.journal_id.id
            for bon in sorted(bon_a_facturer):
                factures_reussies = []
                try:
                    factures_reussies = so_obj.action_invoice_create(cr, uid, bon_a_facturer[bon], journal_id, True, 'out_invoice', context=context)
                    invoice_ids = factures_reussies.values()
                    # On appelle toutes les méthodes nécessaires pour la génération de la facture
                    # avec les dates/move lines/number
                    for invoice_id in invoice_ids:
                        wf_service = netsvc.LocalService("workflow")
                        wf_service.trg_validate(uid, 'account.invoice', invoice_id, 'invoice_open', cr)

                except Exception,e:
                    print str(e)
                    bon_non_reussis += bon_a_facturer[bon]
                    continue
                finally:
                    # On ajoute les valeurs de la liste de factures réussies
                    bon_reussis += factures_reussies

            # On fait le point sur les bons réussis et non réussis
            res += "Des bons de livraison sont à facturer : \n"
            res += '----------\n'
            clients = sorted(bon_a_facturer)
            for clt in clients:
                data = res_partner_obj.read(cr, uid, clt, ['id', 'name'], context=context)
                nom = str(data.get('name', False))
                data_id = str(data.get('id', False))
                bon_ids = str(bon_a_facturer[clt])
                res += "CLIENT %s \t:\t %s \t\t\t(ID BONS : %s)" % (data_id, nom, bon_ids)
                res += "\n"
            res += '----------\n'
            # les réussis
            res += '\n'
            res += "Bons dont la génération est arrivée à terme : \n"
            res += '----------\n'
            if bon_reussis:
                res += 'ID\t\tRéf\t\tOrigine\t\tClient\n'
                for bon_reussi in sorted(bon_reussis):
                    data = so_obj.read(cr, uid, int(bon_reussi), ['id', 'name', 'origin', 'address_id'], context=context)
                    data_id = str(data.get('id', False))
                    nom = str(data.get('name', False))
                    origine = str(data.get('origin', False))
                    address_id = str(data.get('address_id', False) and data.get('address_id')[0])
                    partner_id = 'Non trouvé'
                    if address_id:
                        partner_data = partner_address_obj.read(cr, uid, int(address_id), ['name'], context=context)
                        if partner_data:
                            partner = str(partner_data.get('name', None))
                    res += "%s\t\t%s\t\t%s\t\t%s" % (id, nom, origine, partner)
                    res += '\n'
            else:
                res += 'AUCUN' + '\n'
            res += '----------\n'
            # les non réussis
            res += '\n'
            res += "Bons qui ont échoués : \n"
            res += '----------\n'
            if bon_non_reussis:
                res += 'ID\t\tRéf\t\tOrigine\t\tClient'
                for bon_non_reussi in sorted(bon_non_reussis):
                    data = so_obj.read(cr, uid, bon_non_reussi, ['id', 'name', 'origin', 'address_id'], context=context)
                    data_id = str(data.get('id', False))
                    nom = str(data.get('name', False))
                    origine = str(data.get('origin', False))
                    address_id = str(data.get('address_id', False) and data.get('address_id')[0])
                    partner_id = 'Non trouvé'
                    if address_id:
                        partner_data = partner_address_obj.read(cr, uid, int(address_id), ['name'], context=context)
                        if partner_data:
                            partner = str(partner_data.get('name', None))
                    res += "%s\t\t%s\t\t%s\t\t%s" % (id, nom, origine, partner_id)
                    res += '\n'
            else:
                res += 'AUCUN' + '\n'
            res += '----------\n'
        else:
            # Nous sommes dans le cas où aucun bon n'est à facturer
            res += "Aucun bon de livraison n'est à facturer."
        # On renvoie le résultat
        return res

    def _traitement_factures(self, db_name, uid, ids, clients=[], context={}):
        """
        Lance le traitement pour générer les factures puis renvoie 
        le résultat dans un fichier attaché à une requête utilisateur.
        """
        # Vérifications diverses
        if isinstance(ids, (int, long)):
            ids = [ids]
        if not clients:
            raise osv.except_osv(_('Erreur'), _("Aucun client fourni pour effectuer le traitement."))
        # Récupération d'éléments
        db, pool = pooler.get_db_and_pool(db_name)
        cr = db.cursor()
        if isinstance(clients, (int, long)):
            clients = [clients]
        ce_jour = time.strftime('%Y-%m-%d %H:%M:%S')
        chaine = ustr(self._generation_factures(cr, uid, ids, clients, context=context))
        if chaine:
            # Création d'un binaire
            export = base64.encodestring(chaine.encode("utf-8"))
            # Création d'une requête utilisateur
            requete = pool.get('res.request')
            nom = 'GÉNÉRATION factures au ' + ce_jour
            req_id = requete.create(cr, uid, {'name': nom, 'act_from': uid, 'act_to': uid, 'body': ''}, context=context)
            if req_id:
                # Préparation des éléments du fichier
                nom = 'FAC_autogen' + '_' + time.strftime('%Y-%m-%d_%H%M%S')
                extension = '.txt'
                nom_complet = nom + extension
                piece_jointe = pool.get('ir.attachment')
                vals = {
                    'name': 'Fichier GÉNÉRATION factures',
                    'datas': export,
                    'datas_fname': nom_complet,
                    'description': """
                        Description du résultat de la génération des factures pour chaque client à partir des bons de 
                        préparation et en fonction du délai de paiement
                    """,
                    'res_model': 'res.request',
                    'res_id': req_id,
                }
                piece_id = piece_jointe.create(cr, uid, vals, context=context)
                if piece_id:
                    ce_jour_fin = time.strftime('%Y-%m-%d %H:%M:%S')
                    note = "Date début traitement : %s.\nDate fin traitement : %s." % (ce_jour, ce_jour_fin)
                    requete.write(cr, uid, req_id, {'body': note}, context=context)
        print """###
            Processus de génération des factures à partir des bons d'expéditions suivant le 
            délai de paiement des clients : terminé."""
        cr.commit()
        cr.close()
        return True

    def action_make_invoices(self, cr, uid, ids, context={}):
        """
        Vérification des données et lancement d'un 'thread' pour la 
        génération des factures.
        """
        if isinstance(ids, (int, long)):
            ids = [ids]
        #+ stock_picking ayant des bons de livraisons en état terminé et à 
        #+ facturer.
        # Préparation d'éléments
        res_partner_obj = self.pool.get('res.partner')
        # On récupère tout les clients (id + mode de facturation) trié
        # par id dont le mode de facturation bl est différent de 'n'
        res = res_partner_obj.search(cr, uid, [('facturation_bl', '!=', 'n')], order='id ASC', context=context)
        if res:
            # Création d'un thread
            traitement_sous_thread = threading.Thread(target=self._traitement_factures, 
                args=(cr.dbname, uid, ids, res, context))
            # Lancement du thread
            traitement_sous_thread.start()
            # Fermeture de la fenêtre
            return {'type': 'ir.actions.act_window_close'}
        raise osv.except_osv(_('Erreur'), _('Aucun client trouvé.'))
        return False

wizard_picking_to_invoice()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
