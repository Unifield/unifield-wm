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
from tools import ustr


class wizard_account_move_excel(osv.osv_memory):
    _name = 'wizard.account.move.excel'

    #~ _columns = {
        #~ 'data': fields.binary('File', readonly=True),
        #~ 'name': fields.char('Filename', 16, readonly=True),
        #~ 'state': fields.selection( ( ('choose','choose'),   # choose date
             #~ ('get','get'),         # get the file
           #~ ) ),
    #~ }

    #~ def attachment_tree_view(self, cr, uid, ids, context):
        #~ domain = [
            #~ ('res_model', '=', 'project.task'), ('res_id', 'in', ids)
        #~ ]
        #~ res_id = ids and ids[0] or False
        #~ return {
            #~ 'name': _('Attachments'),
            #~ 'domain': domain,
            #~ 'res_model': 'ir.attachment',
            #~ 'type': 'ir.actions.act_window',
            #~ 'view_id': False,
            #~ 'view_mode': 'tree,form',
            #~ 'view_type': 'form',
            #~ 'limit': 80,
            #~ 'context': "{'default_res_model': '%s','default_res_id': %d}" % (self._name, res_id)
        #~ }
    def get_file(self, cr, uid, ids, context={}):
        """
        Génère un binaire 'hote.txt' contenant des informations sur les découpes à faire pour une commande donnée.
        Ceci afin de l'exporter vers Bizerba qui affiche lesdites informations.
        """
        # Préparation de variables
        nom_fichier = 'hote.txt'
        attachement_obj = self.pool.get('ir.attachment')
        sale_order_obj = self.pool.get('sale.order')
        sol_obj = self.pool.get('sale.order.line')
        total = 0
        # Parcours de chaque commande
        for sale_order in sale_order_obj.browse(cr, uid, ids):
            chaine = ''
            lines = sale_order_obj.read(cr, uid, sale_order.id, ['order_line']).get('order_line', False)
            # Parcours de chaque ligne
            num_ligne = 1
            for sol_id in lines:
                # Vérification si découpe, si oui, alors on génère une chaîne de caractère
                if sol_obj.browse(cr, uid, sol_id, context=context).product_id.code_affectation == 'DECP':
                    # Génération de la chaine de la ligne de commande
                    chaine_ligne = self.gen_bizerba_string(cr, uid, sol_id, num_ligne, context=context)
                    # Ajout au fichier de commande
                    chaine += chaine_ligne
                    chaine += "\n"
                    num_ligne += 1
                    total += 1
            
            # Écriture de la chaine créée et association avec la commande si jamais on a plus d'une ligne
            if total > 0:
                data = base64.encodestring(chaine.encode("utf-8"))
                vals = {
                    'name': 'Fichier bizerba',
                    'datas': data,
                    'datas_fname': nom_fichier,
                    'description': 'Fichier prévu pour le PC Bizerba',
                    'res_model': 'sale.order',
                    'res_id': sale_order.id,
                }
                # Création de l'élément "fichier joint" dans OpenERP
                attachement_obj.create(cr, uid, vals)
        return True
        
    def action_make_file_excel(self, cr, uid, ids, context=None):
        # Pour le fichier : utiliser le wizard 
        
        # On récupère toutes les factures validées
        invoices_ids = self.pool.get('account.invoice').search(cr, uid, [('state', '=', 'open')], context=context)
        invoices_records = self.pool.get('account.invoice').browse(cr, uid, invoices_ids, context=context)

        # Création ou lecture du fichier
        fichier = u'Date;Référence partenaire;Code compte financier;Débit;Crédit\n'

        # Pour chaque facture on va chercher les écritures comptables
        for invoice in invoices_records:
            type_compte_ligne = {}
            #Construction de la ligne du fichier
            for line_id in invoice.move_id.line_id:

                # Génération de la ligne
                ligne = ''
                ligne += ''.join(line_id.date) + ';'
                ligne += ''.join(line_id.invoice) + ';'
                ligne += ''.join(line_id.partner_id.ref) + ';'
                ligne += ''.join(str(line_id.account_id.code)) + ';'
                ligne += ''.join(str(line_id.debit)) + ';'
                ligne += ''.join(str(line_id.credit)) + ';'
                print ligne, 'ligne', line_id.account_id.type
                
                # On vérifie le type de compte de la ligne
                if line_id.account_id.type == 'other':
                    type_compte_ligne['999other%s' % (str(line_id.id),)] = ligne
                else:
                    type_compte_ligne['000%s%s' % (line_id.account_id.type, str(line_id.id))] = ligne

            # Tri des lignes par rapport au type de compte
            for key in sorted(type_compte_ligne.iterkeys()):
                # On vérifie si l'écriture est déjà saisie 
                #~ if check_ligne(ligne, fichier):
                fichier += ''.join(type_compte_ligne[key]) + '\r\n'

            fichier += '\r\n'
            print fichier, 'fichier'
            # On génère le fichier csv séparé par des point virgules
        return False

wizard_account_move_excel()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
