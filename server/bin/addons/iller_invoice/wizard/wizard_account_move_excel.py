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

_no_lines_form = """<?xml version="1.0" encoding="utf-8" ?>
    <form string="Rien à exporter">
    <label colspan="4" string="Aucune facture n'a de lignes à exporter !" />
    </form>
"""

_no_file_form = """<?xml version="1.0" encoding="utf-8" ?>
    <form string="Aucun fichier">
    <label colspan="4" string="Le fichier csv n'a jamais été créé ou a été déplacé !" />
    </form>
"""

nom_fichier = 'export_comptable.csv'
path_fichier = './'

class wizard_account_move_excel(wizard.interface):

    """
        Permet de vérifier qu'il y a bien des factures à exporter
    """
    def _valid_form(self, cr, uid, data, context=None):

        pool_obj = pooler.get_pool(cr.dbname)
        obj_invoice = pool_obj.get('account.invoice')
        # On regarde s'il y a des factures à exporter
        invoices_ids = obj_invoice.search(cr, uid, [('state', '=', 'open'), ('exported', '=', False)], context=context)
        # S'il n'y en a pas, on retourne un message
        if not invoices_ids:
            return 'no_lines'
        # S'il y en a, on sauvegarde les ids des factures dans data pour éviter de refaire une requête après
        data['invoices_ids'] = invoices_ids
        return 'set'

    """
        Permet de vérifier qu'il y a bien un fichier à télécharger
    """
    def _verif_file(self, cr, uid, data, context=None):

        path = "%s%s" % (path_fichier, nom_fichier)
        if not os.path.isfile(path):
            return 'no_file'
        return 'get'

    """
        Permet de générer la pièce jointe du fichier export csv
    """
    def _generate_attachment(self, cr, uid, data, nom_fichier, context=None):

        pool = pooler.get_pool(cr.dbname)
        obj_attachment = pool.get('ir.attachment')
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
            vals = {
                'name': 'Export comptable',
                'datas': data['file'],
                'datas_fname': nom_fichier,
                'description': u'Fichier csv avec les écritures comptables des factures',
            }
            obj_attachment.create(cr, uid, vals, context=context)

    """
        Permet d'écrire le contenu du fichier
    """
    def _write_file(self, cr, uid, data, export_file, nom_fichier, fichier, context=None):

        try:
            # On écrit le fichier avec le contenu généré (en mode ajout)
            export_file.write(fichier.encode("utf-8"))
            # On met à jour les variables du fichier
            data['name'] = nom_fichier
            # Replace le pointeur au début du fichier, car le write semble le positionner à la fin, 
            # du coup, lorsqu'on lit à nouveau le fichier, il ne lit rien
            export_file.seek(0)
            data['file'] = base64.encodestring(export_file.read())
        except IOError as e:
            print "I/O error({0}): {1}".format(e.errno, e.strerror)
        finally:
            export_file.close()

    """
        Permet de générer une ligne en fonction d'un browse record d'account move line
    """
    def _generate_line(self, cr, uid, data, line_id, context=None):
        # Génération de la ligne
        ligne = ''
        ligne += "%s;" %(line_id.date,)
        ligne += "%s;" %(line_id.invoice.number,)
        ligne += "%s;" %(line_id.partner_id.ref,)
        ligne += "%s;" %(line_id.account_id.code,)
        ligne += "%s;" %(line_id.debit,)
        ligne += "%s;" %(line_id.credit,)

        return ligne

    """
        Permet de récupérer les factures à exporter
    """
    def _get_invoices_records(self, cr, uid, data, context=None):

        pool = pooler.get_pool(cr.dbname)
        obj_invoice = pool.get('account.invoice')
        if 'invoices_ids' in data and data['invoices_ids']:
            invoices_ids = data['invoices_ids']
            # On met à False une fois utilisé par sécurité
            data['invoices_ids'] = False
        else:
            # On récupère toutes les factures validées et non exportées
            invoices_ids = obj_invoice.search(cr, uid, [('state', '=', 'open'), ('exported', '=', False)], context=context)

        return obj_invoice.browse(cr, uid, invoices_ids, context=context)

    """
        Permet générale permettant de générer et télécharger le fichier
    """
    def _action_make_file_excel(self, cr, uid, data, context=None):

        # Définition des objets
        pool = pooler.get_pool(cr.dbname)
        obj_invoice = pool.get('account.invoice')

        path = "%s%s" % (path_fichier, nom_fichier)

        invoices_records = self._get_invoices_records(cr, uid, data, context=context)

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

                ligne = self._generate_line(cr, uid, data, line_id, context=context)

                # On vérifie le type de compte de la ligne
                if line_id.account_id.type == 'other':
                    type_compte_ligne['999other%s' % (str(line_id.id),)] = ligne
                else:
                    type_compte_ligne['000%s%s' % (line_id.account_id.type, str(line_id.id))] = ligne

            # Tri des lignes par rapport au type de compte
            for key in sorted(type_compte_ligne.iterkeys()):
                fichier += ''.join(type_compte_ligne[key]) + '\r\n'
            
            # On notifie que les écritures comptable ont bien été écrites pour cette facture
            obj_invoice.write(cr, uid, invoice.id, {'exported':True}, context=context)
            fichier += '\r\n'

        self._write_file(cr, uid, data, export_file, nom_fichier, fichier,  context=context)

        self._generate_attachment(cr, uid, data, nom_fichier, context=context)

        return data

    def _action_schedule(self, cr, uid, data, context=None):
        #Gestion du cron
        return {}

    def _action_get_file_excel(self, cr, uid, data, context=None):
        
        path = "%s%s" % (path_fichier, nom_fichier)
        # On ouvre le fichier en mode ajout
        export_file = open(path, "r")
        try:
            data['file'] = base64.encodestring(export_file.read())
            data['name'] = nom_fichier
        except IOError as e:
            print "I/O error({0}): {1}".format(e.errno, e.strerror)
        finally:
            export_file.close()

        return data
        
    states = {
        'init': {
            'actions': [],
            'result': {
                'type': 'form',
                'arch': _form_type,
                'fields': _field_type,
                'state': [('end', 'Annuler'), ('schedule', 'Programmer'), ('choice', u'Générer maintenant'), ('ifexists', u'Télécharger')],
            },
        },
        'choice': {
            'actions': [],
            'result': {'type': 'choice',
                       'next_state': _valid_form,}
        },
        'ifexists': {
            'actions': [],
            'result': {'type': 'choice',
                       'next_state': _verif_file,}
        },
        'no_lines': {
            'actions': [],
            'result': {'type': 'form',
                       'arch': _no_lines_form,
                       'fields': {},
                       'state': [('end', 'Annuler')]},
        },
        'no_file': {
            'actions': [],
            'result': {'type': 'form',
                       'arch': _no_file_form,
                       'fields': {},
                       'state': [('end', 'Annuler')]},
        },
        'get': {
            'actions': [_action_get_file_excel],
            'result': {
                'type': 'form',
                'arch': _get_form,
                'fields': _field_get,
                'state': [('end', 'Sortir')],
            },
        },
        'set': {
            'actions': [_action_make_file_excel],
            'result': {
                'type': 'form',
                'arch': _get_form,
                'fields': _field_get,
                'state': [('end', 'Sortir')],
            },
        },
        'schedule': {
            'actions': [_action_schedule],
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
