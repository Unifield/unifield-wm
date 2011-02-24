#!/usr/bin/env python
# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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

from osv import fields, osv
from tools.translate import _
import time
import wizard

class stock_partial_picking(osv.osv_memory):
    _name = "stock.partial.picking"
    _description = "Partial Picking"
    _columns = {
        'date': fields.datetime('Date', required=True),
        'product_moves_out' : fields.one2many('stock.partial.move', 'wizard_id', 'Moves'),
#        'product_moves_in' : fields.one2many('stock.move.memory.in', 'wizard_id', 'Moves'),
     }
    
    def get_picking_type(self, cr, uid, picking, context=None):
        """
        Retourne le type de livraison ('in' ou 'out').
        """
        picking_type = picking.type
        for move in picking.move_lines:
            if picking.type == 'in' and move.product_id.cost_method == 'average':
                picking_type = 'in'
                break
            else:
                picking_type = 'out'
        return picking_type

    def get_moves(self, cr, uid, ids, context={}):
        """
        Permet de récupérer les lignes de mouvements courantes
        """
        print "get_moves - contenu: %s" % self.read(cr, uid, ids, ['product_moves_out'], context=context)
        return False
    
    def default_get(self, cr, uid, fields, context=None):
        """ To get default values for the object.
         @param self: The object pointer.
         @param cr: A database cursor
         @param uid: ID of the user currently logged in
         @param fields: List of fields for which we want default values
         @param context: A standard dictionary
         @return: A dictionary which of fields with values.
        """
        if context is None:
            context = {}
            
        pick_obj = self.pool.get('stock.picking')
        res = super(stock_partial_picking, self).default_get(cr, uid, fields, context=context)
        print "default_get - res AVANT modif : %s" % res
        picking_ids = context.get('active_ids', [])
        if not picking_ids:
            return res

        print "default_get - CHAMPS: %s" % fields
        result = []
        for pick in pick_obj.browse(cr, uid, picking_ids, context=context):
            pick_type = self.get_picking_type(cr, uid, pick, context=context)
            for m in pick.move_lines:
                if m.state in ('done', 'cancel'):
                    continue
                result.append(self.__create_partial_picking_memory(m, pick_type))
        
        if 'product_moves_in' in fields:
            res.update({'product_moves_in': result})
        if 'product_moves_out' in fields:
            res.update({'product_moves_out': result})
            print "default_get - nous sommes entrés dans le OUT !"
        if 'date' in fields:
            res.update({'date': time.strftime('%Y-%m-%d %H:%M:%S')})
        
        print "default_get - RES: %s" % res
        
        return res

    def fields_view_get(self, cr, uid, view_id=None, view_type='form', context=None, toolbar=False):
        """
        Affiche le wizard de validation des livraisons avec la quantité livrée.
        Wizard repris de la version 6 d'OpenERP.
        """
        result = super(stock_partial_picking, self).fields_view_get(cr, uid, view_id, view_type, context, toolbar)
       
        pick_obj = self.pool.get('stock.picking')
        picking_ids = context.get('active_ids', False)

        if not picking_ids:
            # not called through an action (e.g. buildbot), return the default.
            return result

        for pick in pick_obj.browse(cr, uid, picking_ids, context=context):
            picking_type = self.get_picking_type(cr, uid, pick, context=context)
        
        _moves_arch_lst = """<form string="%s">
                        <separator string="Faire le colisage                                                                         " />
                        <field name="date" invisible="1"/>
                        <field name="%s" colspan="4" nolabel="1" mode="tree,form" width="550" height="200" ></field>
                        """ % (_('Faire le colisage'), "product_moves_" + picking_type)
        _moves_fields = result['fields']

        # add field related to picking type only
        _moves_fields.update({
                            'product_moves_' + picking_type: {'relation': 'stock.partial.move', 'type' : 'one2many', 'string' : 'Lignes produit'}, 
                            })

        _moves_arch_lst += """
                <separator string="" colspan="4" />
                <label string="" colspan="2"/>
                <group col="2" colspan="2">
                <button icon='gtk-cancel' special="cancel"
                    string="_Annuler" />
                <button name="do_partial" string="_Confirmer"
                    colspan="1" type="object" icon="gtk-go-forward" />
            </group>
        </form>"""
        result['arch'] = _moves_arch_lst
        result['fields'] = _moves_fields
        return result
        
    def create(self, cr, uid, data, context={}):
        print 'create context %s' %context
        return super(stock_partial_picking, self).create(cr, uid, data, context=context)

    def write(self, cr, uid, ids, data, context={}):
        print data
        return super(stock_partial_picking, self).write(cr, uid, ids, data, context=context)

    def __create_partial_picking_memory(self, picking, pick_type):
        move_memory = {
            'product_id' : picking.product_id.id, 
            'quantity' : picking.product_qty, 
            'product_uom' : picking.product_uom.id, 
#            'prodlot_id' : picking.prodlot_id.id, 
            'move_id' : picking.id, 
            'reliquat' : False,
        }
    
        if pick_type == 'in':
            move_memory.update({
                'cost' : picking.product_id.standard_price, 
                'currency' : picking.product_id.company_id and picking.product_id.company_id.currency_id and picking.product_id.company_id.currency_id.id or False, 
            })
        return move_memory

    def do_partial(self, cr, uid, ids, context={}):
        """ Makes partial moves and pickings done.
        @param self: The object pointer.
        @param cr: A database cursor
        @param uid: ID of the user currently logged in
        @param fields: List of fields for which we want default values
        @param context: A standard dictionary
        @return: A dictionary which of fields with values.
        """
        print "do_partial - entré !"
        print "do_partial - nom : %s" % self._name
        print "do_partial - context : %s" % context
        pick_obj = self.pool.get('stock.picking')
        
        picking_ids = context.get('active_ids', False)
        partial = self.browse(cr, uid, ids[0], context=context)
        partial_datas = {
            'delivery_date' : partial.date
        }
        print "PARTIAL: %s" % self.browse(cr, uid, ids)[0]._data
        print "PARTIAL DATAS: %s" % partial._data
        print "PICK IDS: %s" % picking_ids
        print "do_partial - moves_list: %s" % self.pool.get('stock.partial.move').browse(cr, uid, [], context=context) #.get_moves(cr, uid, ids, context=context)

        for pick in pick_obj.browse(cr, uid, picking_ids, context=context):
            picking_type = self.get_picking_type(cr, uid, pick, context=context)
            print "do_partial - picking_type: %s" % picking_type
#            moves_list = picking_type == 'in' and partial.product_moves_in or partial.product_moves_out

            print "AVANT: %s" % picking_type
            print "MOVE LIST: %s" % partial.product_moves_out

            for move in partial.product_moves_out:
                partial_datas['move%s' % (move.move_id.id)] = {
                    'product_id': move.id, 
                    'product_qty': move.quantity, 
                    'product_uom': move.product_uom.id, 
#                    'prodlot_id': move.prodlot_id.id, 
                    'reliquat' : move.reliquat,
                }
                if (picking_type == 'in') and (move.product_id.cost_method == 'average'):
                    partial_datas['move%s' % (move.move_id.id)].update({
                                                    'product_price' : move.cost, 
                                                    'product_currency': move.currency.id, 
                                                    })
            print "APRES"
        print "APRES les données partielles %s" % partial_datas
        pick_obj.do_partial(cr, uid, picking_ids, partial_datas, context=context)
        return {}

stock_partial_picking()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
