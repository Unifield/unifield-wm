# -*- coding: utf-8 -*-
##############################################################################
#    
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2011 MSF, TeMPO Consulting
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
from tools.translate import _

class stock_move_select_asset(osv.osv_memory):
    _name = 'stock.move.select.asset'

    _columns = {
        'move_processor_id': fields.reference(
            string='Move',
            selection=[
                ('create.picking.move.processor', 'Move'),
                ('stock.move.in.processor', 'Move'),
                ('internal.move.processor', 'Move'),
                ('outgoing.delivery.move.processor', 'Move'),
                ('stock.move.processor', 'Move'),
                ('ppl.move.processor', 'Move'),
                ('return.ppl.move.processor', 'Move'),
            ],
            size=256,
        ),
        'asset_ids': fields.many2many(
            'product.asset',
            'wizard_id',
            'asset_id',
            'select_asset_wizard_rel',
            string='Asset',
        ),
        'product_id': fields.many2one(
            'product.product',
            string='Product',
            readonly=True,
        ),
    }

    def put_in_processor(self, cr, uid, ids, context=None):
        '''
        Create one stock.move.processor (or other model according to 
        value in move_processor_id) per asset selected.
        Check if the number of selected asset is <= original quantity
        '''
        if context is None:
            context = {}

        if isinstance(ids, (int, long)):
            ids = [ids]

        for wiz in self.browse(cr, uid, ids, context=context):
            import pdb
            pdb.set_trace()
            if len(wiz.asset_ids) > wiz.move_processor_id.ordered_quantity:
                raise osv.except_osv(
                    _('Error'),
                    _('You cannot choose a higher number of assets (%d) than the initial quantity (%d).') %
                    (len(wiz.asset_ids), wiz.move_processor_id.ordered_quantity),
                )

        return self.close_window(cr, uid, ids, context=context)

    def close_window(self, cr, uid, ids, context=None):
        '''
        Close the window and return to the picking processing wizard
        '''
        if context is None:
            context = {}

        if isinstance(ids, (int, long)):
            ids = [ids]

        wiz = self.browse(cr, uid, ids[0], context=context)

        return {
            'type': 'ir.actions.act_window',
            'res_model': wiz.move_processor_id,
            'view_type': 'form',
            'view_mode': 'form',
            'res_id': wiz.move_processor_id,
            'target': 'new',
            'context': context,
        }

stock_move_select_asset()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

