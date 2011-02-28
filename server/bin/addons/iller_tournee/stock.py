#!/usr/bin/env python
# -*- encoding: utf-8 -*-

from osv import osv
from osv import fields
import netsvc

class iller_picking(osv.osv):
    _name = 'stock.picking'
    _inherit = 'stock.picking'

    _columns = {
        'tournee_id': fields.many2one('tournee.iller', string='Tournée', required=False),
    }

    def _postes_valides(self, cr, uid, ids, context={}):
        for sp in self.browse(cr, uid, ids):
            for move in sp.move_lines:
                if not move.poste_id.id:
                    raise osv.except_osv('Alerte', "Un ou plusieurs champs « Poste de préparation » n'est pas rempli. Veuillez remplir tous les champs « Poste de préparation » pour chacune des lignes de mouvement.")
        return True

    def draft_force_assign(self, cr, uid, ids, *args):
        self._postes_valides(cr, uid, ids)
        wf_service = netsvc.LocalService("workflow")
        for pick in self.browse(cr, uid, ids):
            wf_service.trg_validate(uid, 'stock.picking', pick.id,
                'button_confirm', cr)
        return True

    def draft_validate(self, cr, uid, ids, *args):
        self._postes_valides(cr, uid, ids)
        wf_service = netsvc.LocalService("workflow")
        self.draft_force_assign(cr, uid, ids)
        for pick in self.browse(cr, uid, ids):
            move_ids = [x.id for x in pick.move_lines]
            self.pool.get('stock.move').force_assign(cr, uid, move_ids)
            wf_service.trg_write(uid, 'stock.picking', pick.id, cr)

            self.action_move(cr, uid, [pick.id])
            wf_service.trg_validate(uid, 'stock.picking', pick.id, 'button_done', cr)
        return True


iller_picking()

class iller_stock_move(osv.osv):
    _name = 'stock.move'
    _inherit = 'stock.move'

    _columns = {
        'poste_id': fields.many2one('iller.poste', string="Poste Prépa.", required=False),
    }

iller_stock_move()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

