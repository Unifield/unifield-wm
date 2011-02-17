#!/usr/bin/env python
# -*- encoding: utf-8 -*-

from osv import osv
from osv import fields

class iller_picking(osv.osv):
    _name = 'stock.picking'
    _inherit = 'stock.picking'

    _columns = {
        'tournee_id': fields.many2one('tournee.iller', string='Tournée', required=True),
    }

iller_picking()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

