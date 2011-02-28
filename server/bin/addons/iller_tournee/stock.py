#!/usr/bin/env python
# -*- encoding: utf-8 -*-

from osv import osv
from osv import fields

class iller_picking(osv.osv):
    _name = 'stock.picking'
    _inherit = 'stock.picking'

    _columns = {
        'tournee_id': fields.many2one('tournee.iller', string='Tournée', required=False),
    }

iller_picking()

class iller_stock_move(osv.osv):
    _name = 'stock.move'
    _inherit = 'stock.move'

    _columns = {
        'poste_id': fields.many2one('iller.poste', string="Poste Prépa.", required=False),
    }

iller_stock_move()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

