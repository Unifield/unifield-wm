#!/usr/bin/env python
#-*- encoding:utf-8 -*-

import os
import base64
from osv import osv, fields
import datetime
from tools.translate import _

class export_journal_ventes(osv.osv_memory):
    _name = "wizard.export.journal.ventes"
    _inherit = ''

    _columns = {
        'date_debut': fields.date(string="Date de début", required=True, help="Choisir la date à partir de laquelle la recherche de l'ensemble des \
            factures non générées va s'opérer."),
        'date_fin': fields.date(string="Date de fin", required=True),
        'state': fields.selection( [('open', 'Open'), ('done', 'Done')], string="State"),
        'fichier': fields.binary('Fichier', readonly=True),
    }

    _defaults = {
        'date_fin': lambda *a: datetime.datetime.now().strftime('%Y-%m-%d'),
        'state': lambda *a: 'open',
    }

    def gen_journal_vente_string(self, cr, uid, move_ids=[], context={}):
        """
        Génère et retourne une chaîne de caractère compatible avec GESCOM Compta à partir des mouvements donnés.
        NB : Ce code a été généré suivant le fichier original de GESCOM (en cobol) utilisé par Distribution Iller.
        
        """
        # Préparation des variables
        res = ''
        inv_obj = self.pool.get('account.invoice')
        move_obj = self.pool.get('account.move')
        ml_obj = self.pool.get('account.move.line')
        if not len(move_ids):
            return False

        # pour éviter les erreurs
        if isinstance(move_ids, (int, long)):
            move_ids = [move_ids]

        res = ''
        
        for am in move_obj.browse(cr, uid, move_ids, context=context):
            i = 1
            # On traite chaque ligne des mouvements
            for ml in am.line_id:
                # Préparation de certaines données
                ligne = []
                # code facture
                code = ml.invoice.number
                # date facture (pour afficher : date.strftime('%Y%m%d')
                date = datetime.datetime.strptime(ml.invoice.date_invoice, '%Y-%m-%d')
                # id du compte comptable de la facture
                account_id = ml.invoice.account_id.id
                # Type de la facture et code
                type_fac = ml.invoice.type
                code_type_fac = 1
                if type_fac == 'out_refund':
                    code_type_fac = 2
                # Origine
                ligne.append('91')
                #Société
                ligne.append('01')
                #Établissement
                ligne.append('01')
                #Journal (ici vente)
                ligne.append('01')
                #Numéro de la pièce
                num_piece = str(code.replace('/', ''))
                ligne.append(num_piece[:7].ljust(7, ' '))
                #Numéro de ligne
                ligne.append(str(i)[:4].rjust(4, "0"))
                #Facture ou avoir
                ligne.append(str(code_type_fac)[:1])
                #Code comptable
                ligne.append(ml.account_id.code[:8].ljust(8, '0'))
                #Code Tiers
                ligne.append(ml.partner_id.ref[:9].ljust(9, '0'))
                #Code Factor (autre personne qui paie la facture)
                ligne.append(" ".ljust(9, " "))
                #Code facture
                ligne.append(num_piece[:7].ljust(10, ' '))
                #Date facture
                date_fac = date.strftime('%Y%m%d')
                ligne.append(date_fac[:8].rjust(8, ' '))
                #Nature analytique
                ligne.append("N".ljust(8, " "))
                #Destination analytique
                ligne.append("D".ljust(8, " "))
                #Projet
                ligne.append(" ".ljust(15, " "))
                #Date comptable
                ligne.append(date_fac[:8].rjust(8, ' '))
                #Date exigibilité
                nouv_date = date + datetime.timedelta(20)
                nouv_date_fac = nouv_date.strftime('%Y%m%d')
                ligne.append(nouv_date_fac[:8].rjust(8, ' '))
                #Date événement
                ligne.append(date_fac[:8].rjust(8, ' '))
                #Date échéance
                ligne.append(nouv_date_fac[:8].rjust(8, ' '))
                #Référence lettrage
                ligne.append(num_piece[:7].ljust(7, ' '))
                #Sens de la ligne
                sens = 1
                montant = ml.debit
                if ml.balance < 0:
                    sens = 2
                    montant = ml.credit
                ligne.append(str(sens))
                #Montant en monnaie de la tenue de la comptabilité
                montant = str(montant).split(".")
                montant_gauche = montant[0].rjust(11, '0')
                montant_droite = montant[1].ljust(4, '0')
                montant_droite += " "
                # Si la facture est une facture de type AVOIR
                if code_type_fac == 2:
                    montant_droite += "-"
                ligne.append(montant_gauche[:11].rjust(11, '0'))
                ligne.append(",")
                ligne.append(montant_droite[:4].ljust(4, '0'))
                ligne.append(" ")
                #Montant en devise
                ligne.append("00000000000,0000 ")
                #Type devise
                ligne.append(" ")
                #Code devise
                ligne.append(" ".ljust(3, " "))
                #Taux devise
                ligne.append("00001,000000 ")
                #Diviseur devise
                ligne.append("0".ljust(5,"0"))
                #Quantité
                ligne.append("00000000000,000000 ")
                #Libellé écriture
                # TODO : faire A V O I R, F A C T U R E ou TRANSFERT JNL VENTES
                if ml.account_id.id == account_id:
                    if code_type_fac == 1:
                        ligne.append("F A C T U R E".ljust(30, " "))
                    else:
                        ligne.append("A V O I R".ljust(30, " "))
                else:
                    ligne.append("TRANSFERT JNL VENTES".ljust(30, " "))
                #Code taxe
                ligne.append("001")
                #Code taxe 2
                ligne.append("000")
                #Code taxe 3
                ligne.append("000")
                #Code régime TVA
                ligne.append("1")
                #Code DAS
                ligne.append(" ".ljust(3, " "))
                #Mode de paiement
                # FIXME TODO
                ligne.append("1".rjust(3, "0"))
                #Code Bon à payer
                ligne.append("1")
                #Code banque
                ligne.append(" ".ljust(2, " "))
                #Titre de paiement
                ligne.append(" ".ljust(10, " "))
                #Codes statistiques
                ligne.append(" ".ljust(15, " "))
                #Numéro d'article
                ligne.append(" ".ljust(20, " "))
                #Numéro de commande
                ligne.append(" ".ljust(10, " "))
                #Ligne de commande
                ligne.append("0".ljust(3, "0"))
                #Numéro de réception
                ligne.append("0".ljust(10, "0"))
                #Numéro BL Fournisseur
                ligne.append(" ".ljust(15, " "))
                #Zone utilisateur 1
                ligne.append(" ".ljust(15, " "))
                #Zone utilisateur 2
                ligne.append(" ".ljust(15, " "))
                #Zone utilisateur 3
                ligne.append(" ".ljust(15, " "))
                #Zone utilisateur 4
                ligne.append(" ".ljust(15, " "))
                #Zone utilisateur 5
                ligne.append(" ".ljust(15, " "))
                #Zone utilisateur 6
                ligne.append(" ".ljust(15, " "))
                #Zone utilisateur 7
                ligne.append(" ".ljust(15, " "))
                #Zone utilisateur 8
                ligne.append(" ".ljust(15, " "))
                #Zone utilisateur 9
                ligne.append(" ".ljust(15, " "))
                #Zone utilisateur 10
                ligne.append(" ".ljust(15, " "))
                #Flag enregistrement traité
                ligne.append("0")
                #Type de TVA
                ligne.append(" ")
                #Code escompte
                ligne.append("0".ljust(3, "0"))
                #Filler réserve PRODSTAR (espace vide prévu pour autre chose)
                ligne.append(" ".ljust(95, " "))
                #Filler réserve utilisateur (espace vide prévu pour autre chose)
                ligne.append(" ".ljust(46, " "))
                
                # On ajoute la chaîne de caractère à ce qu'on va renvoyer
                ligne.append("\n")
                res += ''.join(ligne)
                # On incrémente le numéro de ligne
                i+=1

        # On retourne le résultat sous forme d'une seule chaîne
        return res

    def action_valider(self, cr, uid, ids, context={}):
        """
        Valide le wizard et génère le fichier pour le journal des ventes
        """
        if isinstance(ids, (int, long)):
            ids = [ids]
        wizard = self.browse(cr, uid, ids[0], context=context)
        date_deb = wizard.date_debut
        date_fin = wizard.date_fin
        if date_fin < date_deb:
            raise osv.except_osv(_('Attention'), _('La date de fin doit être supérieure à celle de début.'))
        if date_deb and date_fin:
            # Vérification sur l'existence d'un journal de vente
            journal_ids = self.pool.get('account.journal').search(cr, uid, [('type', '=', 'sale')], context=context)
            if not journal_ids:
                raise osv.except_osv(_('Erreur'), _('Aucun journal de ventes trouvé !'))
            # Préparation du chemin du fichier
            nom = 'VT' + date_deb.replace('-', '') + '-' + date_fin.replace('-', '')
            extension = '.txt'
            nom_complet = nom + extension
            chemin = os.path.join(os.path.expanduser('~'),'tmp', nom_complet)
            # Vérification de l'existence du fichier
            if os.path.exists(chemin):
                raise osv.except_osv(_('Attention'), _('Le traitement a déjà été effectué sur la période donnée !'))
            # TODO : recherche sur le champ "exporté" des account_move_line
            am_ids = self.pool.get('account.move').search(cr, uid, [('state', '=', 'posted'), ('journal_id', 'in', journal_ids), 
                ('date', '>=', date_deb), ('date', '<=', date_fin)])
            aml_ids = self.pool.get('account.move.line').search(cr, uid, [('move_id.state', '=', 'posted'), ('journal_id', 'in', journal_ids), 
                ('date', '>=', date_deb), ('date', '<=', date_fin)])
            chaine = self.gen_journal_vente_string(cr, uid, am_ids, context=context)
            if chaine:
                export = base64.encodestring(chaine.encode("utf-8"))
                # On enregistre dans un fichier la période
                file(chemin, 'wb+').write(chaine)
                # On teste la présence du fichier
                if os.path.exists(chemin):
                    print "#######################"
                    print "TODO: marquer les lignes comme exportées"
                    print "#######################"
                    # On marque les lignes comme "exportées"
#                    aml_obj = self.pool.get('account.move.line')
#                    for am in self.browse(cr, uid, am_ids, context=context):
#                        for aml in am.line_id:
#                            aml_obj.write(cr, uid, aml.id, {'exporte_vers_gescom': True}, context=context)
                    # TODO marquer les lignes (modifier account_move_line)
                # TODO: Faire une res_request
                return self.write(cr, uid, ids, {'state':'done', 'fichier': export}, context=context)
            raise osv.except_osv(_('Information'), _('Aucune facture trouvée.'))
        return False

    def action_recup_fichier(self, cr, uid, ids, context={}):
        """
        Permet de charger un fichier
        """
        chaine = "test d'envoi de chaine"
        export1 = base64.encodestring(chaine.encode("utf-8"))
        return self.write(cr, uid, ids, {'state':'done', 'fichier': export1}, context=context)

    def action_retour(self, cr, uid, ids, context={}):
        """
        Remet les objets donnés au stade "open"
        """
        if isinstance(ids, (int, long)):
            ids = [ids]
        return self.write(cr, uid, ids, {'state': 'open', 'fichier': None}, context=context)

export_journal_ventes()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
