# -*- coding: utf-8 -*-
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
import pooler

class stock_partial_move_memory_out(osv.osv_memory):
    _name = "stock.move.memory.out"
    _rec_name = 'product_id'

    _columns = {
        'product_id' : fields.many2one('product.product', string="Produit", required=True),
        'quantity' : fields.float("Quantité", required=True),
        'product_uom': fields.many2one('product.uom', 'Unité de mesure', required=True),
#        'prodlot_id' : fields.many2one('stock.production.lot', 'Lot de production'),
        'move_id' : fields.many2one('stock.move', "Mouvement de stock"),
        'wizard_id' : fields.many2one('stock.partial.move', string="Assistant"),
        'cost' : fields.float("Coût", help="Coût unitaire pour cette ligne de produit"),
        'currency' : fields.many2one('res.currency', string="Monnaie", help="Monnaie dans laquelle le coût unitaire est affiché."),
        'difference': fields.float("Diff."),
        'reliquat': fields.boolean("Reliquat ?", help="Faire un reliquat ?"),
    }

    def qty_change(self, cr, uid, ids, move_id=None, qty=None):
        """
        Retourne la différence entre la quantité commandée et la quantité 
        réellement livrée.
        Si jamais la différence est supérieure à zéro, alors on affiche la 
        coche permettant de faire un reliquat.
        """
        if not move_id and not qty:
            return False
        diff = 0.00
        sm_obj = pooler.get_pool(cr.dbname).get('stock.move')
        for sm in sm_obj.browse(cr, uid, [move_id]):
            diff = sm.product_qty - qty
        res = {'value': {'difference': diff}}
        # Deux prochaines lignes à décommenter pour cocher automatiquement le
        #+ reliquat si la différence entre quantité commandée et quantitée 
        #+ livrée est supérieure à 0
#        if diff > 0:
#            res = {'value': {'difference': diff, 'reliquat': True}}
        return res

stock_partial_move_memory_out()

class stock_partial_move_memory_in(osv.osv_memory):
    _name = "stock.move.memory.in"

    _columns = {
        'product_id' : fields.many2one('product.product', string="Produit", required=True),
        'quantity' : fields.float("Quantité", required=True),
        'product_uom': fields.many2one('product.uom', 'Unité de mesure', required=True),
#        'prodlot_id' : fields.many2one('stock.production.lot', 'Lot de production'),
        'move_id' : fields.many2one('stock.move', "Mouvement de stock"),
        'wizard_id' : fields.many2one('stock.partial.move', string="Assistant"),
        'cost' : fields.float("Coût", help="Coût unitaire pour cette ligne de produit"),
        'currency' : fields.many2one('res.currency', string="Monnaie", help="Monnaie dans laquelle le coût unitaire est affiché."),
    }

stock_partial_move_memory_in()

class stock_partial_move(osv.osv_memory):
    _name = "stock.partial.move"
    _description = "Partial Move"
    _rec_name = "wizard_id"

    _columns = {
#        'date': fields.datetime('Date', required=True),
#        'type': fields.char("Type", size=3),
#        'product_moves_out' : fields.one2many('stock.move.memory.out', 'wizard_id', 'Moves'),
#        'product_moves_in' : fields.one2many('stock.move.memory.in', 'wizard_id', 'Moves'),
        'product_id' : fields.many2one('product.product', string="Produit", required=True),
        'quantity' : fields.float("Quantité", required=True),
        'product_uom': fields.many2one('product.uom', 'Unité de mesure', required=True),
#        'prodlot_id' : fields.many2one('stock.production.lot', 'Lot de production'),
        'move_id' : fields.many2one('stock.move', "Mouvement de stock"),
        'wizard_id' : fields.many2one('stock.partial.picking', string="Assistant"),
        'cost' : fields.float("Coût", help="Coût unitaire pour cette ligne de produit"),
        'currency' : fields.many2one('res.currency', string="Monnaie", help="Monnaie dans laquelle le coût unitaire est affiché."),
        'difference': fields.float("Diff."),
        'reliquat': fields.boolean("Reliquat ?", help="Faire un reliquat ?"),
     }

    def __is_in(self,cr, uid, move_ids):
        """
            @return: True if one of the moves has as picking type 'in'
        """
        if not move_ids:
            return False
       
        move_obj = self.pool.get('stock.move')
        move_ids = move_obj.search(cr, uid, [('id','in',move_ids)])
       
        for move in move_obj.browse(cr, uid, move_ids):
            if move.picking_id.type == 'in' and move.product_id.cost_method == 'average':
                return True
        return False

    def __get_picking_type(self, cr, uid, move_ids):
        if self.__is_in(cr, uid, move_ids):
            return "product_moves_in"
        else:
            return "product_moves_out"

    def qty_change(self, cr, uid, ids, move_id=None, qty=None):
        """
        Retourne la différence entre la quantité commandée et la quantité 
        réellement livrée.
        Si jamais la différence est supérieure à zéro, alors on affiche la 
        coche permettant de faire un reliquat.
        """
        if not move_id and not qty:
            return False
        diff = 0.00
        sm_obj = pooler.get_pool(cr.dbname).get('stock.move')
        for sm in sm_obj.browse(cr, uid, [move_id]):
            diff = sm.product_qty - qty
        res = {'value': {'difference': diff}}
        # Deux prochaines lignes à décommenter pour cocher automatiquement le
        #+ reliquat si la différence entre quantité commandée et quantitée 
        #+ livrée est supérieure à 0
#        if diff > 0:
#            res = {'value': {'difference': diff, 'reliquat': True}}
        return res

    def view_init(self, cr, uid, fields_list, context=None):
        res = super(stock_partial_move, self).view_init(cr, uid, fields_list, context=context)
        move_obj = self.pool.get('stock.move')
    
        if context is None:
            context = {}
        for move in move_obj.browse(cr, uid, context.get('active_ids', []), context=context):
            if move.state in ('done', 'cancel'):
                raise osv.except_osv(_('Action invalide !'), _("Impossible de livrer des produits qui l'ont déjà été !"))
            
        return res

    def __create_partial_move_memory(self, move):
        move_memory = {
            'product_id' : move.product_id.id,
            'quantity' : move.product_qty,
            'product_uom' : move.product_uom.id,
#            'prodlot_id' : move.prodlot_id.id,
            'move_id' : move.id,
        }
        
        if move.picking_id.type == 'in':
            move_memory.update({
                'cost' : move.product_id.standard_price,
                'currency' : move.product_id.company_id and move.product_id.company_id.currency_id and move.product_id.company_id.currency_id.id or False,
            })
        return move_memory

    def __get_active_stock_moves(self, cr, uid, context=None):
        move_obj = self.pool.get('stock.move')
        if context is None:
            context = {}
               
        res = []
        for move in move_obj.browse(cr, uid, context.get('active_ids', []), context=context):
            if move.state in ('done', 'cancel'):
                continue           
            res.append(self.__create_partial_move_memory(move))
        
        return res
    
    _defaults = {
#        'product_moves_in' : __get_active_stock_moves,
        'product_moves_out' : __get_active_stock_moves,
#        'date' : lambda *a : time.strftime('%Y-%m-%d %H:%M:%S'),
    }

## FONCTION fields_view_get rendue inutile
#    def fields_view_get(self, cr, uid, view_id=None, view_type='form', context=None, toolbar=False):
#        if not context:
#            context = {}
#        
#        message = {
#                'title' : _('Deliver Products'),
#                'info' : _('Delivery Information'),
#                'button' : _('Deliver'),
#                }
#        if context:
#            if context.get('product_receive', False):
#                message = {
#                    'title' : _('Receive Products'),
#                    'info' : _('Receive Information'),
#                    'button' : _('Receive'),
#                }
#        
#        move_ids = context.get('active_ids', False)    
#        message['picking_type'] = self.__get_picking_type(cr, uid, move_ids)
#        result = super(stock_partial_move, self).fields_view_get(cr, uid, view_id, view_type, context, toolbar)
#        _moves_fields = result['fields']
#        _moves_fields.update({
##                            'product_moves_in' : {'relation': 'stock.move.memory.in', 'type' : 'one2many', 'string' : 'Lignes produit'},
#                            'product_moves_out' : {'relation': 'stock.move.memory.out', 'type' : 'one2many', 'string' : 'Lignes produit'}
#                            })
#        
#        _moves_arch_lst = """
#                <form string="%(title)s">
#                    <separator colspan="4" string="%(info)s"/>
#                    <field name="date" colspan="2"/>
#                    <separator colspan="4" string="Move Detail"/>
#                    <field name="%(picking_type)s" colspan="4" nolabel="1" mode="tree,form" width="550" height="200" ></field>      
#                    <separator string="" colspan="4" />
#                    <label string="" colspan="2"/>
#                    <group col="2" colspan="2">
#                        <button icon='gtk-cancel' special="cancel" string="_Cancel" />
#                        <button name="do_partial" string="%(button)s"
#                            colspan="1" type="object" icon="gtk-apply" />
#                    </group>
#                </form> """ % message
#        
#        result['arch'] = _moves_arch_lst
#        result['fields'] = _moves_fields
#        return result

    def do_partial(self, cr, uid, ids, context=None):
        """ Makes partial moves and pickings done.
        @param self: The object pointer.
        @param cr: A database cursor
        @param uid: ID of the user currently logged in
        @param fields: List of fields for which we want default values
        @param context: A standard dictionary
        @return: A dictionary which of fields with values.
        """
        
        if context is None:
            context = {}
        move_obj = self.pool.get('stock.move')
        
        move_ids = context.get('active_ids', False)
        partial = self.browse(cr, uid, ids[0], context=context)
        partial_datas = {
            'delivery_date' : partial.date
        }
        
        p_moves = {}
        picking_type = self.__get_picking_type(cr, uid, move_ids)
        
        moves_list = picking_type == 'product_moves_in' and partial.product_moves_in  or partial.product_moves_out
        for product_move in moves_list:
            p_moves[product_move.move_id.id] = product_move
        
        moves_ids_final = []
        for move in move_obj.browse(cr, uid, move_ids, context=context):
            if move.state in ('done', 'cancel'):
                continue
            if not p_moves.get(move.id):
                continue
            partial_datas['move%s' % (move.id)] = {
                'product_id' : p_moves[move.id].id,
                'product_qty' : p_moves[move.id].quantity,
                'product_uom' :p_moves[move.id].product_uom.id,
                'prodlot_id' : p_moves[move.id].prodlot_id.id,
            }
            
            moves_ids_final.append(move.id)
            if (move.picking_id.type == 'in') and (move.product_id.cost_method == 'average'):
                partial_datas['move%s' % (move.id)].update({
                    'product_price' : p_moves[move.id].cost,
                    'product_currency': p_moves[move.id].currency.id,
                })
        
        move_obj.do_partial(cr, uid, moves_ids_final, partial_datas, context=context)
        return {'type': 'ir.actions.act_window_close'}

stock_partial_move()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

