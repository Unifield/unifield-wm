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

from osv import fields, osv

class iller_poste(osv.osv):
    _name = 'iller.poste'
    _desription = 'Poste de travail'

    _columns = {
        'name': fields.char(size=64, string='Nom', required=True),
        'type': fields.selection([('PREP', u'Préparation'), ('DECP', u'Découpe')], string='Type', required=True),
        'stock_move_ids': fields.one2many('stock.move', 'poste_id', required=False),
    }

    _order = 'name'

iller_poste()


class tournee_iller(osv.osv):
    _name = 'tournee.iller'
    _description = u'Tournée pour la livraison des produits'


    def name_search(self, cr, uid, name, args=None, operator='ilike', context=None, limit=80):
        if not args:
            args=[]
        if not context:
            context={}
        res = []
        if name:
            #Vérification si ce qu'on cherche est le code
            try:
                code = int(name)
            except ValueError, e:
                pass
                return super(tournee_iller, self).name_search(cr, uid, name, args=args, operator=operator, context=context, limit=limit)
            res = self.search(cr, uid, [('code_tournee','=',name)], limit=limit, context=context)
        else:
            return super(tournee_iller, self).name_search(cr, uid, name, args=args, operator=operator, context=context, limit=limit)
        return self.name_get(cr, uid, res, context)


    _columns = {
        'name': fields.char(size=64, string=u'Nom', required=True),
        'code_tournee': fields.integer(string=u'Code tournée'),
        #'heure_depart': fields.integer(string='Heure depart'),
        'heure_depart': fields.char(size=5, string=u'Heure depart'),
        'prep_id': fields.many2one('iller.poste', domain="[('type', '=', 'PREP')]",
            string=u'Poste de préparation'),
        'decoupe_id': fields.many2one('iller.poste', domain="[('type', '=', 'DECP')]",
            string=u'Poste de découpe'),
        'regroup_code': fields.char(size=12, string=u'Code de regroupement'),
        'stock_picking_ids': fields.one2many('stock.picking', 'tournee_id', string=u'Produits à expédier'),

        ## Les partenaires présents dans la tournée
        'partner1': fields.one2many('res.partner', 'tournee1', u'Clients principaux'),
        'partner2': fields.one2many('res.partner', 'tournee2', u'Clients secondaires'),
        'partner3': fields.one2many('res.partner', 'tournee3', u'Clients exceptionnels'),
    }

    _order = 'heure_depart, name'

tournee_iller()

class res_partner(osv.osv):
    _name = 'res.partner'
    _inherit = 'res.partner'

    _columns = {
        'tournee1': fields.many2one('tournee.iller', string=u'Tournée n°1'),
        'tournee2': fields.many2one('tournee.iller', string=u'Tournée n°2'),
        'tournee3': fields.many2one('tournee.iller', string=u'Tournée n°3'),
    }

res_partner()
