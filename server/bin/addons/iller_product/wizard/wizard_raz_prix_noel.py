#!/usr/bin/env python
# -*- encoding: utf-8 -*-

from osv import osv
from osv import fields

class wizard_raz_prix_noel(osv.osv_memory):
    _name = 'wizard.raz.prix.noel'
    _description = 'Remise à zéro des prix de Noël'

    _columns = {
    }

    def _raz(self, cr, uid, ids, context={}):
        product_obj = self.pool.get('product.product')
        product_ids = product_obj.search(cr, uid, [('prix_decembre', '!=', 0.00)])
        product_obj.write(cr, uid, product_ids, {'prix_decembre': 0.00})

        return {'name': 'Remise à zéro des prix de Noël',
                'type': 'ir.actions.act_window',
                'res_model': 'wizard.raz.prix.noel.close',
                'target': 'new',
                'view_mode': 'form',
                'view_type': 'form',
        }

wizard_raz_prix_noel()

class wizard_raz_prix_noel_close(osv.osv_memory):
    _name = 'wizard.raz.prix.noel.close'
    _description = 'Close wizard'

    _columns = {
    }

    def _close(self, cr, uid, ids, context={}):
        return {'type': 'ir.actions.act_window_close'}

wizard_raz_prix_noel_close()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

