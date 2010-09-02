# -*- encoding: utf-8 -*-
# EN CAS D'UPGRADE, VOIR LES REMARQUES DE TYPE "!!! ATTENTION MISE A JOUR !!!
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY ir FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from osv import fields
from osv import osv
from tools import config
from product import _common
from datetime import date
import pooler
import time

class res_partner(osv.osv):
   _inherit = 'res.partner'
   _name = 'res.partner'
   _columns = {
        'siret': fields.char('Siret', size=128),
        'commentaire': fields.text('Commentaire'),
        'nb_ex_fact': fields.integer('Nb Ex Factures'),
        'releves': fields.selection([('O','oui'), ('N','non'),('R','Traite')],'Relevés'),
        'type_releve': fields.char('Type Relv Ndm', size=1),
        'type_facture': fields.selection([('I', 'I'), ('Q', 'Q'),('M','M')], 'Type Facture'),
        'soumis_tva':  fields.selection([(0,'soumis'), (1,'exonere'),(2,'??')], 'Soumis TVA', size=-1),
   }
res_partner()

class res_partner_address(osv.osv):
   _inherit = 'res.partner.address'
   _name = 'res.partner.address'
   _columns = {
        'enseigne': fields.char('Enseigne', size=128),
   }

res_partner_address()

class res_users(osv.osv):
    _name = 'res.users'
    _inherit = 'res.users'

    _columns = {
        'code_saler': fields.integer(string='Code Vendeur'),
    }

res_users()
