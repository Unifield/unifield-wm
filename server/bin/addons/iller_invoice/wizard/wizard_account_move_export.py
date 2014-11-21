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
from datetime import datetime, timedelta
from tools.translate import _
import pooler
import base64
import time
import wizard
import os
import mx
import csv

_form_init = """<?xml version="1.0" encoding="utf-8" ?>
<form string="Choix de l'action">
    <label string="Choisissez l'action à exécuter : 'Programmer' permet de planifier l'export csv grâce à des paramètres. 'Générer maintenant' permet de lancer l'export immédiatement et donne la possibilité de récupérer le fichier. 'Télécharger' permet de récupérer directement le fichier en l'état, sans faire de modification." colspan="4" />
</form>"""

_form_type = """<?xml version="1.0" encoding="utf-8" ?>
<form string="Choix du fichier">
    <field name="nextcall" />
    <field name="interval_number" required="1" />
    <field name="interval_type" required="1" />
    <field name="doall" required="1" />
</form>"""

_field_type = {
    'nextcall': {'string': u'Date de l\'export', 'type': 'datetime', 'default':time.strftime('%Y-%m-%d %H:%M:%S')},
    'interval_number': {'string': u'Intervalle entre les appels', 'type': 'integer', 'required': True, 'default':1},
    'interval_type': {'string': u'Type de répétition', 'type': 'selection',
        'selection': [('work_days', 'Jours de travail'), ('days', 'Jours'), ('weeks', 'Semaines'),
                    ('months', 'Mois'), ('hours', 'Heures'), ('minutes', 'Minutes')],
        'required': True, 'default':'work_days'},
    'doall': {'string': u'Recommencer les manqués', 'type': 'boolean',
        'required': True, 'default':True},
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

_missing_input_form = """<?xml version="1.0" encoding="utf-8" ?>
    <form string="Erreur de saisie">
    <label colspan="4" string="Des champs obligatoires sont vides." />
    </form>
"""

_error_input_form = """<?xml version="1.0" encoding="utf-8" ?>
    <form string="Erreur de saisie">
    <label colspan="4" string="L'intervalle doit être supérieure à 1." />
    </form>
"""

nom_fichier = 'export_comptable.csv'
path_fichier = './'


class iller_export_cron(osv.osv):
    _name = 'iller.export.cron'

    """
        Permet de récupérer les factures à exporter
    """
    def _get_invoices_records(self, cr, uid, ids, data, context=None):

        obj_invoice = self.pool.get('account.invoice')
        if 'invoices_ids' in data and data['invoices_ids']:
            invoices_ids = data['invoices_ids']
            # On met à False une fois utilisé par sécurité
            data['invoices_ids'] = False
        else:
            # On récupère toutes les factures validées et non exportées
            invoices_ids = obj_invoice.search(cr, uid, [('state', '=', 'open'), ('exported', '=', False)], context=context)

        return obj_invoice.browse(cr, uid, invoices_ids, context=context)

    """
        Permet de générer la pièce jointe du fichier export csv
    """
    def _generate_attachment(self, cr, uid, ids, data, nom_fichier, context=None):

        obj_attachment = self.pool.get('ir.attachment')
        nom_fichier_joint = cr.dbname + '_' + nom_fichier
        # On crée un fichier attaché au niveau du serveur récupérable depuis la gestion des documents
        attach_id = obj_attachment.search(cr, uid, [('datas_fname', '=', nom_fichier_joint)], context=context)
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
                'datas_fname': nom_fichier_joint,
                'description': u'Fichier csv avec les écritures comptables des factures',
            }
            obj_attachment.create(cr, uid, vals, context=context)

    """
        Permet d'écrire le contenu du fichier
    """
    def _write_file(self, cr, uid, ids, data, writer_csv, export_file, lignes, context=None):

        try:

            # On écrit le fichier avec la liste de lignes à écrire, selon
            # le formattage définit dans le constructeur
            writer_csv.writerows(lignes)
            # On met à jour les variables du fichier
            data['name'] = nom_fichier
            # Replace le curseur au début du fichier, car le write le positionne à la fin
            export_file.seek(0)
            data['file'] = base64.encodestring(export_file.read())
        except IOError:
            print "Erreur de lecture/écriture de fichier"
        finally:
            export_file.close()

    """
        Permet de générer une ligne en fonction d'un browse record d'account move line
    """
    def _generate_line(self, cr, uid, ids, data, line_id, context=None):

        ligne = []
        date_object = mx.DateTime.Parser.DateTimeFromString(line_id.date)
        # Génération de la ligne
        ligne.append('%s/%s/%s' %(date_object.day, date_object.month, date_object.year))
        ligne.append('%s' %(line_id.invoice.number,))
        ligne.append('%s' %(line_id.partner_id.ref,))
        ligne.append('%s' %(line_id.account_id.code,))
        str_debit = '%s' %(line_id.debit,)
        str_credit ='%s' %(line_id.credit,)
        ligne.append(str_debit.replace('.', ','))
        ligne.append(str_credit.replace('.', ','))

        return ligne

    """
        Fonction générale permettant de générer et télécharger le fichier
    """
    def schedule(self, cr, uid, data, context=None):

        # Définition des objets
        obj_invoice = self.pool.get('account.invoice')
        obj_move_line = self.pool.get('account.move.line')
        
        ids = []
        path = "%s%s_%s" % (path_fichier, cr.dbname, nom_fichier)

        invoices_records = self._get_invoices_records(cr, uid, ids, data, context )

        # On ouvre le fichier en mode ajout
        export_file = open(path, "a+")
        statinfo = os.stat(path) # In bytes

        writer_csv = csv.writer(export_file, delimiter=';')
        if(statinfo.st_size > 1):
            # La taille est supérieure à 1 donc on n'initialise pas avec l'entête
            lignes = []
        else:
            # Initialisation de l'entête du tableau
            lignes = [['Date', 'Facture', 'Référence partenaire', 'Code compte financier', 'Débit', 'Crédit']]
        
        # Pour chaque facture on va chercher les écritures comptables
        for invoice in invoices_records:
            # Initialisation d'une variable stockant les lignes dont le compte est de type 'other'
            lignes_other = []
            if invoice.move_id.line_id:
                # Pour chaque account move line correspondant à la facture en cours
                for line_id in invoice.move_id.line_id:
                    # Si la ligne n'a pas encore été exportée
                    if not line_id.exported_csv:
                        # Si le compte est de type other, alors on stocke dans une variable temporaire pour
                        # permettre de les écrire plus tard
                        if line_id.account_id.type == 'other':
                            lignes_other.append(self._generate_line(cr, uid, ids, data, line_id, context=context))
                        # Sinon on ajoute directement au fichier la ligne reçue
                        else:
                            lignes.append(self._generate_line(cr, uid, ids, data, line_id, context=context))

                        # Pour chaque ligne on indique que la ligne a été exportée 
                        obj_move_line.write(cr, uid, [line_id.id], {'exported_csv':True}, context=context)

            # Après la boucle on ajoute les lignes dont le type est 'other'
            lignes += lignes_other
            # On notifie que les écritures comptable ont bien été écrites pour cette facture
            # Permet lors de l'appel suivant de récupérer uniquement les factures dont les
            # lignes n'ont pas été exportées
            obj_invoice.write(cr, uid, invoice.id, {'exported':True}, context=context)

            # Décommenter pour avoir une séparation entre les factures
            # lignes += ['\r\n']

        self._write_file(cr, uid, ids, data, writer_csv, export_file,  lignes, context=context)

        self._generate_attachment(cr, uid, ids, data, nom_fichier, context=context)

        return data

iller_export_cron()

class wizard_account_move_export(wizard.interface):
    
    """
        Permet de vérifier que les données sont correctement saisies
    """
    def _valid_input(self, cr, uid, data, context=None):

        # Si la date n'a pas été saisie on met la date du jour
        if 'nextcall' not in data['form'] or not data['form']['nextcall']:
            data['form']['nextcall'] = time.strftime('%Y-%m-%d %H:%M:%S')

        # Vérification que les champs ne sont pas vides
        if ('interval_number' not in data['form'] and not data['form']['interval_number']) \
            or ('interval_type' not in data['form'] and not data['form']['interval_type']) \
            or ('doall' not in data['form'] and not data['form']['doall']):
            return 'missing_input'
        # Vérification de la saisie de l'intervalle
        if data['form']['interval_number'] < 1:
            return 'error_input'

        return 'schedule_factory'


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

        path = "%s%s_%s" % (path_fichier, cr.dbname, nom_fichier)
        if not os.path.isfile(path):
            return 'no_file'
        return 'get'


    """
        Fonction générale permettant de générer et télécharger le fichier
    """
    def _action_make_file_export(self, cr, uid, data, context=None):
        pool = pooler.get_pool(cr.dbname)
        obj_iller_invoice_cron = pool.get('iller.export.cron')
        data = obj_iller_invoice_cron.schedule(cr, uid, data, context=context)
        return data

    """
        Fonction permettant de programmer le cron pour exécuter la routine
    """
    def _action_schedule(self, cr, uid, data, context=None):
        # Définition des objets
        pool = pooler.get_pool(cr.dbname)
        obj_cron = pool.get('ir.cron')

        # Récupération du cron pour l'export csv comptable
        cron_ids = obj_cron.search(cr, uid, [('name', '=', 'Export csv comptable')], context=context)

        # Construction des valeurs de vals à écrire ou créer
        vals = {
            'nextcall': data['form']['nextcall'] or time.strftime('%Y-%m-%d %H:%M:%S'),
            'interval_number': data['form']['interval_number'] or 1,
            'interval_type': data['form']['interval_type'] or 'work_days',
            'function': 'schedule',
            'doall': data['form']['doall'] or False,
            'numbercall': -1,
            'active': True,
            'model': 'iller.export.cron',
            'args': (data, context),
        }
        # Si le cron existe déjà on écrit 
        if cron_ids:
            obj_cron.write(cr, uid, cron_ids[0], vals, context=context)
        # Sinon on le crée
        else:
            vals['name'] = 'Export csv comptable'
            obj_cron.create(cr, uid, vals, context=context)

        return {}
        
    """
        Fonction permettant de récupérer le fichier écrit sur le serveur
    """
    def _action_get_file_export(self, cr, uid, data, context=None):
        
        path = "%s%s_%s" % (path_fichier, cr.dbname, nom_fichier)
        # On ouvre le fichier en mode ajout
        export_file = open(path, "r+")
        try:
            data['file'] = base64.encodestring(export_file.read())
            data['name'] = nom_fichier
        except IOError:
            print "Erreur de lecture/écriture de fichier"
        finally:
            export_file.close()

        return data


    states = {
        # Initialisation
        'init': {
            'actions': [],
            'result': {
                'type': 'form',
                'arch': _form_init,
                'fields': {},
                'state': [('end', 'Annuler'), ('input_schedule', 'Programmer'), ('choice', u'Générer maintenant'), ('ifexists', u'Télécharger')],
            },
        },
        # Formulaires de saisie
        'input_schedule': {
            'actions': [],
            'result': {
                    'type': 'form',
                    'arch': _form_type,
                    'fields': _field_type,
                    'state': [('end', 'Annuler'), ('validinput', 'Valider')],
            },
        },
        # Contrôles
        'validinput': {
            'actions': [],
            'result': {'type': 'choice',
                       'next_state': _valid_input,}
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
        # Formulaires d'erreur
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
        'error_input': {
            'actions': [],
            'result': {'type': 'form',
                       'arch': _error_input_form,
                       'fields': {},
                       'state': [('end', 'Annuler')]},
        },
        'missing_input': {
            'actions': [],
            'result': {'type': 'form',
                       'arch': _missing_input_form,
                       'fields': {},
                       'state': [('end', 'Annuler')]},
        },
        # Formulaires d'action
        'get': {
            'actions': [_action_get_file_export],
            'result': {
                'type': 'form',
                'arch': _get_form,
                'fields': _field_get,
                'state': [('end', 'Sortir')],
            },
        },
        'set': {
            'actions': [_action_make_file_export],
            'result': {
                'type': 'form',
                'arch': _get_form,
                'fields': _field_get,
                'state': [('end', 'Sortir')],
            },
        },
        'schedule_factory': {
            'actions': [_action_schedule, _action_get_file_export],
            'result': {
                'type': 'form',
                'arch': _get_form,
                'fields': _field_get,
                'state': [('end', 'Sortir')],
            },
        },
    }

wizard_account_move_export('wizard.account.move.export')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
