#!/usr/bin/env python
# -*- encoding: utf-8 -*-

from osv import osv
from osv import fields

class wizard_print_pricelist_cat(osv.osv_memory):
    _name = 'wizard.print.pricelist.cat'
    _description = 'Impression de la liste de prix d\'une catégorie'

    _columns = {
        'category_ids': fields.many2many('product.category', 'print_cat_rel', 'print_id', 'category_id', string='Catégorie'),
        'bareme1_id': fields.many2one('product.pricelist.bareme', string='Barème 1'),
        'bareme2_id': fields.many2one('product.pricelist.bareme', string='Barème 2'),
        'bareme3_id': fields.many2one('product.pricelist.bareme', string='Barème 3'),
        'bareme4_id': fields.many2one('product.pricelist.bareme', string='Barème 4'),
        'bareme5_id': fields.many2one('product.pricelist.bareme', string='Barème 5'),
        'bareme6_id': fields.many2one('product.pricelist.bareme', string='Barème 6'),
    }

    def _print(self, cr, uid, ids, context={}):
        datas = {'ids': context.get('active_ids', [])}
        res = self.read(cr, uid, ids, ['category_ids', 'bareme1_id', 'bareme2_id', 'bareme3_id', 'bareme4_id', 'bareme5_id', 'bareme6_id'], context=context)
        res = res and res[0] or {}
        datas['form'] = res
        return {'type': 'ir.actions.report.xml',
                'report_name': 'category.pricelist',
                'datas': datas,}

wizard_print_pricelist_cat()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

