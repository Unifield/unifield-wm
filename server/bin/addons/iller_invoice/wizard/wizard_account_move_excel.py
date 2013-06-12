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

from osv import osv, fields
from datetime import datetime
from tools.translate import _
import pooler
import base64
import time
import wizard
import os

_form_type = """<?xml version="1.0" encoding="utf-8" ?>
<form string="Choix du fichier">
    <field name="date" required="1" />
</form>"""

_field_type = {
    'date': {'string': u'Heure de l\'export quotidien', 'type': 'time', 'required': True},
}

_get_form = """<?xml version="1.0" encoding="utf-8" ?>
<form string="">
    <field name="file" />
</form>"""

_field_get = {
    'file': {'string': 'Fichier', 'type': 'binary'},
    'name': {'string': 'Nom', 'type': 'char'},
}


class wizard_account_move_excel(wizard.interface):

    def _action_make_file_excel(self, cr, uid, data, context=None):

        # Définition des objets
        pool = pooler.get_pool(cr.dbname)
        obj_attachment = pool.get('ir.attachment')
        obj_invoice = pool.get('account.invoice')
        nom_fichier = 'export_comptable.csv'
        path_fichier = './'
        path = "%s%s" % (path_fichier, nom_fichier)

#TODO Rajouter un filtre sur la date pour récupérer que les factures depuis la dernière écriture -> OK sur export_file
        # On récupère toutes les factures validées et non exportées
        invoices_ids = obj_invoice.search(cr, uid, [('state', '=', 'open'), ('exported', '=', False)], context=context)

#TODO Sécuriser un peu, vérifier si aucune facture correspond : on quitte (rajout message erreur/warning ?)
        #~ if not invoices_ids:
            #~ return {'type': 'ir.action_act_window.close'} 
        invoices_records = obj_invoice.browse(cr, uid, invoices_ids, context=context)

        # On ouvre le fichier en mode ajout
        export_file = open(path, "a+")
        statinfo = os.stat(path) # In bytes
        
        if(statinfo.st_size > 1):
            # La taille est supérieure à 1 donc on n'initialise pas avec l'entête
            fichier = ''
        else:
            # Initialisation de l'entête du tableau
            fichier = u'Date;Facture;Référence partenaire;Code compte financier;Débit;Crédit\n'

        # Pour chaque facture on va chercher les écritures comptables
        for invoice in invoices_records:
            # Dictionnaire permettant d'associer une ligne à un type de compte
            type_compte_ligne = {}
            #Construction de la ligne du fichier
            for line_id in invoice.move_id.line_id:
                # Génération de la ligne
                ligne = ''
                ligne += "%s;" %(line_id.date,)
                ligne += "%s;" %(line_id.invoice.number,)
                ligne += "%s;" %(line_id.partner_id.ref,)
                ligne += "%s;" %(line_id.account_id.code,)
                ligne += "%s;" %(line_id.debit,)
                ligne += "%s;" %(line_id.credit,)

                # On vérifie le type de compte de la ligne
                if line_id.account_id.type == 'other':
                    type_compte_ligne['999other%s' % (str(line_id.id),)] = ligne
                else:
                    type_compte_ligne['000%s%s' % (line_id.account_id.type, str(line_id.id))] = ligne

            # Tri des lignes par rapport au type de compte
            for key in sorted(type_compte_ligne.iterkeys()):
#TODO Créer une fonction qui check si la ligne à écrire est déjà présente
                # On vérifie si l'écriture est déjà saisie 
                #if check_ligne(ligne, fichier):
                fichier += ''.join(type_compte_ligne[key]) + '\r\n'
            
            obj_invoice.write(cr, uid, invoice.id, {'exported':True}, context=context)
            fichier += '\r\n'
            print fichier, 'fichier'

#TODO On écrit le fichier et on l'envoie au client suivant son choix rajout des boutons adéquat
#TODO Pointer sur le fichier créé via le open ?
        # On met à jour les variables du fichier
        data['name'] = nom_fichier
        data['file'] = base64.encodestring(fichier.encode("utf-8"))
        # On crée un fichier attaché au niveau du serveur récupérable depuis la gestion des documents
        attach_id = obj_attachment.search(cr, uid, [('datas_fname', '=', nom_fichier)], context=context)
        # Si le fichier attaché existe déjà on écrit les modifications
        if attach_id:
            vals = {
                'datas': data['file'],
            }
            obj_attachment.write(cr, uid, attach_id, vals, context=context)
        # Sinon on le crée
        else:
            print data
            vals = {
                'name': 'Export comptable',
                'datas': data['file'],
                'datas_fname': nom_fichier,
                'description': u'Fichier csv avec les écritures comptables des factures',
            }
            obj_attachment.create(cr, uid, vals)
        # On écrit le fichier avec le contenu généré (en mode ajout)
        export_file.write(fichier.encode("utf-8"))
        export_file.close()
#TODO Rajout try catch + controle de taille à l'écriture ?
#TODO refactoriser 
#TODO Voir s'il y a moyen d'ajouter des lignes via ir_attachment sinon utiliser le contenu de export_file

        return data

    states = {
        'init': {
            'actions': [],
            'result': {
                'type': 'form',
                'arch': _form_type,
                'fields': _field_type,
                'state': [('end', 'Annuler'), ('get', 'Générer le fichier')],
            },
        },
        'get': {
            'actions': [_action_make_file_excel],
            'result': {
                'type': 'form',
                'arch': _get_form,
                'fields': _field_get,
                'state': [('end', 'Sortir')],
            },
        },
    }

wizard_account_move_excel('wizard.account.move.excel')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
