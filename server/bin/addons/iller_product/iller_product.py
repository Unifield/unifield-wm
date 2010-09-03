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

class product_product(osv.osv):
   _inherit = 'product.product'
   _name = 'product.product'
   _columns = {
        'code_emballage'  : fields.selection([(1,'BAC'),(2,'CARTON')],'Code Emballage', size=-1),
        'type_etiq_art'   : fields.char('Type Etiquette article', size=4),
        'type_emballage'  : fields.char('Type Emballage', size=4),
        'type_condit'     : fields.selection([(0,'Piece'),(1,'Kilo'),(2,'Carton'),(3,'Colis/Barquette')],'Type de conditionnement'),
        'type_pesee'      : fields.selection([(0,'0'),(1,'1'),(2,'2'),(7,'7'),(8,'8')],'Type de pesée',size=-1),
        'nu_par_etiq_art' : fields.integer('Nu parametr. etiq. art.'),
        'code_affection'  : fields.selection([('PREP','Preparation'),('DECP','Decoupe')], 'Code Affection'),
        'localisation'    : fields.char('Zone localisation', size=3),
        'prix_achat'      : fields.float('Prix Achat', digits=(16,2)),
        'coef_depart'     : fields.float('Coef Depart',digits=(16,2)),
        'prix_depart'     : fields.float('Prix de depart',digits=(16,2)),
        'col_promo_p2'    : fields.float('Col.Promo.P2', digits=(16,2)),
        'coef_collectiv'  : fields.float('Coef.Collec', digits=(16,2)),
        'prix_depart_collectiv': fields.float('Prix de depart Collec',digits=(16,2)),
        'coef_promo_blanc': fields.float('Coef Promo blc', digits=(16,2)), 
        'liste_prep'      : fields.selection([(0,'Rien'),(1,'Congelé'),(2,'Salaison'),(3,'Volaille')], 'Liste Prep', size=-1),
        'compl_lib'       : fields.char('Complement Des.', size=12),
        'cond_vente'      : fields.selection([(0,'Pièce'),(1,'Kg'),(2,'Carton')], 'Condit.Vente', size=-1),
   }

   def onchange_coef_depart(self, cr, uid, ids, prix_achat, coef_depart):
       return {'value': {'prix_depart': prix_achat * coef_depart}}

   def onchange_coef_collectiv(self, cr, uid, ids, prix_achat, coef_collectiv):
       return {'value': {'prix_depart_collectiv': prix_achat * coef_collectiv}}


product_product()
