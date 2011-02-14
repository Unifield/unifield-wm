#!/usr/bin/env python
# -*- encoding: utf-8 -*-

from osv import osv
from osv import fields


class wizard_choose_category(osv.osv_memory):
    _name = 'wizard.choose.category'

    _columns = {
        'category_id': fields.many2one('product.category', string='Catégorie', required=True),
        'type': fields.selection([('depart', 'Coeff. départ'), ('blanche', 'Coeff. Promo')], string='Coefficient', required=True),
    }

    def _choose(self, cr, uid, ids, context={}):
        coeff_obj = self.pool.get('wizard.modif.coeff')
        product_obj = self.pool.get('product.product')

        ## On supprime tous les coeffs en mémoire
        coeff_ids = coeff_obj.search(cr, uid, [])
        coeff_obj.unlink(cr, uid, coeff_ids)

        coeffs = []

        for cat in self.browse(cr, uid, ids):
            context.update({'category_id': cat.category_id.id, 'wizard': 1, 'type': cat.type})
            if cat.type and cat.type == 'depart':
                product_ids = product_obj.search(cr, uid, [('categ_id', '=', cat.category_id.id), ('coeff_depart', 'not in', coeffs)], offset=0, limit=1)
                while product_ids:
                    for p in product_obj.browse(cr, uid, product_ids):
                        coeffs.append(p.coeff_depart)
                    product_ids = product_obj.search(cr, uid, [('categ_id', '=', cat.category_id.id), ('coeff_depart', 'not in', coeffs)], offset=0, limit=1)

            elif cat.type and cat.type == 'blanche':
                product_ids = product_obj.search(cr, uid, [('categ_id', '=', cat.category_id.id), ('coeff_blanche', 'not in', coeffs)], offset=0, limit=1)
                while product_ids:
                    for p in product_obj.browse(cr, uid, product_ids):
                        coeffs.append(p.coeff_blanche)
                    product_ids = product_obj.search(cr, uid, [('categ_id', '=', cat.category_id.id), ('coeff_blanche', 'not in', coeffs)], offset=0, limit=1)

            coeffs.sort()
            for c in coeffs:
                coeff_obj.create(cr, uid, {'name': c, 'coeff_new': c, 'category_id': cat.category_id.id, 'type': cat.type}, context=context)

        return {'type': 'ir.actions.act_window',
                'res_model': 'wizard.modif.coeff',
                'view_type': 'form',
                'view_mode': 'tree',
                'name': 'Modification des coefficients',
                'context': context}


wizard_choose_category()


class wizard_modif_coeff(osv.osv_memory):
    _name = 'wizard.modif.coeff'
    _description = 'Modification des coefficients'

    _columns = {
        'name': fields.float(digits=(16,2), string='Coeff. Initial', readonly=True),
        'coeff_new': fields.float(digits=(16,2), string='Nouveau Coeff.', required=True),
        'category_id': fields.many2one('product.category', string='Catégrorie'),
        'type': fields.selection([('depart', 'Coeff. départ'), ('blanche', 'Coeff. Promo')], string='Coefficient', required=True),
    }

    _order = "name, coeff_new"


    def write(self, cr, uid, ids, data, context={}):
        product_obj = self.pool.get('product.product')

        if 'coeff_new' in data and 'type' in context:
            for coeff in self.browse(cr, uid, ids):
                if context.get('type', False) == 'depart':
                    product_ids = product_obj.search(cr, uid, [('categ_id', '=', coeff.category_id.id), ('coeff_depart', '=', coeff.name)])
                    product_obj.write(cr, uid, product_ids, {'coeff_depart': data.get('coeff_new', coeff.name)}, context=context)
                elif context.get('type', False) == 'blanche':
                    product_ids = product_obj.search(cr, uid, [('categ_id', '=', coeff.category_id.id), ('coeff_blanche', '=', coeff.name)])
                    product_obj.write(cr, uid, product_ids, {'coeff_blanche': data.get('coeff_new', coeff.name)}, context=context)

        return super(wizard_modif_coeff, self).write(cr, uid, ids, data, context=context)


    def default_get(self, cr, uid, fields, context={}):
        res = super(wizard_modif_coeff, self).default_get(cr, uid, fields, context=context)

        coeff_ids = self.search(cr, uid, [])
        self.unlink(cr, uid, coeff_ids)

        return res

wizard_modif_coeff()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

