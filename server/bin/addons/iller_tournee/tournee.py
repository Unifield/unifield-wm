# -*- encoding: utf-8 -*-
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
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import time
from osv import fields, osv

class iller_poste(osv.osv):
    _name = 'iller.poste'
    _desription = 'Poste de travail'

    _columns = {
        'name': fields.char(size=64, string='Nom', required=True),
        'type': fields.selection([('PREP', 'Préparation'), ('DECP', 'Découpe')], string='Type', required=True),
    }

    _order = 'name'

iller_poste()


class tournee_iller(osv.osv):
    _name = 'tournee.iller'
    _description = 'Tournée pour la livraison des produits'

    _columns = {
        'name': fields.char(size=64, string='Nom', required=True),
        'code_tournee': fields.integer(string='Code tournee'),
        'heure_depart': fields.integer(string='Heure depart'),
        'prep_id': fields.many2one('iller.poste', domain="[('type', '=', 'PREP')]",
            string='Poste de préparation'),
        'decoupe_id': fields.many2one('iller.poste', domain="[('type', '=', 'DECP')]",
            string='Poste de découpe'),
        'regroup_code': fields.char(size=12, string='Code de regroupement'),

        ## Les partenaires présents dans la tournée
        'partner1': fields.one2many('res.partner', 'tournee1', 'Clients principaux'),
        'partner2': fields.one2many('res.partner', 'tournee2', 'Clients secondaires'),
        'partner3': fields.one2many('res.partner', 'tournee3', 'Clients exceptionnels'),
    }

    _order = 'heure_depart, name'

tournee_iller()

class res_partner(osv.osv):
    _name = 'res.partner'
    _inherit = 'res.partner'

    _columns = {
        'tournee1': fields.many2one('tournee.iller', string='Tournee n°1'),
        'tournee2': fields.many2one('tournee.iller', string='Tournee n°2'),
        'tournee3': fields.many2one('tournee.iller', string='Tournee n°3'),
    }

res_partner()
