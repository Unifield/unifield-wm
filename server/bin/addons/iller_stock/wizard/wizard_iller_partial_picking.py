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
import netsvc
from tools.misc import UpdateableStr, UpdateableDict
import pooler

import wizard
from osv import osv, fields
import tools
from tools.translate import _

_moves_arch_lst = UpdateableStr()
_moves_fields = UpdateableDict()

class iller_partial_picking(osv.osv_memory):
    _name = "stock.partial.picking"
    _description = "Partial Picking"
    _columns = {
        'date': fields.datetime('Date', required=True),
     }
     
    def _to_xml(self, s):
        return (s or '').replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')

    def qty_change(self, field_name, qty, context={}):
        if not field_name:
            return False
        if not qty:
            return {'value': {field_name: '3.00'}, 'context': context}
        return {'value': {field_name: qty}, 'context': context}

    def fields_view_get(self, cr, uid, view_id=None, view_type='form', context=None, toolbar=False):
        # Récupération de la fonction par défaut
        result = super(iller_partial_picking, self).fields_view_get(cr=cr, user=uid, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar)

        # Préparation de différents objets
        pick_obj = self.pool.get('stock.picking')
        picking_ids = context.get('active_ids', False)

        # Envoi du résultat si aucun traitement spécifique à faire
        if not picking_ids:
            return result

        # Création 
        _moves_arch_lst = """<form string="Faire le colisage">
                        <field name="date" invisible="1"/>"""

        # récupération des lignes de bon de livraison
        _moves_fields = result['fields']
        for sp in picking_ids:
            sp_move_lines = pick_obj.browse(cr, uid, sp, context=context).move_lines
            if sp_move_lines:
                for stock_move in sp_move_lines:
                    _moves_arch_lst += '<group col="6">'
                    _moves_arch_lst += '<field name="move%s" />' % (stock_move.id)
                    field_name = "move%s" % stock_move.id
                    _moves_fields[field_name] = {
                            'string': self._to_xml(stock_move.name),
                            'type': 'float',
                            'required': True,
                            'default': stock_move.product_qty,
                            'on_change': "qty_change(field_name=field_name, qty=stock_move.product_qty)"
                        }
                    _moves_arch_lst += '<field name="difference%s" readonly="0"/>' % (stock_move.id)
                    _moves_fields['difference%s' % stock_move.id] = {
                        'string': 'Diff.',
                        'type': 'float',
                        'required': False,
                        'default': '0.00' }

                    _moves_arch_lst += '<field name="reliquat%s" nolabel="1"/>' % (stock_move.id)
                    _moves_fields['reliquat%s' % stock_move.id] = {
                        'type': 'boolean',
                        'required': False,
                        'default': False,
                        'help': "Faire un reliquat ?" }
                    _moves_arch_lst += """</group><newline />"""

        _moves_arch_lst += """
            <group col="6" colspan="2">
                <button icon='gtk-cancel' special="cancel" string="_Annuler" />
                <button name="do_partial" string="_Valider" colspan="1" 
                    type="object" icon="gtk-go-forward" />
            </group>
        </form>"""
        # Retour du résultat final
        result['arch'] = _moves_arch_lst
        result['fields'] = _moves_fields
        print "FINAL : %s" % result
        return result

iller_partial_picking()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
