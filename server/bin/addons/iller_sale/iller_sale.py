#!/usr/bin/env python
# -*- encoding: utf-8 -*-

from osv import osv
from osv import fields


class iller_sale_comment(osv.osv):
    _name = 'iller.sale.comment'
    _description = 'Commentaire par produit/client'
    _rec_name = 'product_id'

    _columns = {
        'product_id': fields.many2one('product.product', string='Produit', required=True),
        'partner_id': fields.many2one('res.partner', string='Client', required=True),
        'comment': fields.text(string='Commentaire', required=True),
    }

iller_sale_comment()


class iller_sale_line(osv.osv):
    _name = 'sale.order.line'
    _inherit = 'sale.order.line'


    def write(self, cr, uid, ids, data, context={}):
        '''
            Enregistre ou remplace le commentaire enregistré dans 
            la BDD
        '''
        comment_obj = self.pool.get('iller.sale.comment')

        if 'notes' in data:
            for line in self.browse(cr, uid, ids):
                comment_ids = comment_obj.search(cr, uid, [('product_id', '=', line.product_id.id), ('partner_id', '=', line.order_id.partner_id.id)])
                if comment_ids and len(comment_ids) > 0:
                    comment_obj.write(cr, uid, comment_ids, {'comment': data.get('notes')})
                else:
                    comment_obj.create(cr, uid, {'comment': data.get('notes'), 'partner_id': line.order_id.partner_id.id, 'product_id': line.product_id.id})

        return super(iller_sale_line, self).write(cr, uid, ids, data, context=context)


    def create(self, cr, uid, data, context={}):
        '''
            Enregistre ou remplace le commentaire enregistré dans
            la BDD
        '''
        comment_obj = self.pool.get('iller.sale.comment')
        order_obj = self.pool.get('sale.order')


        if 'notes' in data and 'product_id' in data and 'order_id' in data:
            partner_id = order_obj.browse(cr, uid, data.get('order_id')).partner_id.id
            comment_ids = comment_obj.search(cr, uid, [('product_id', '=', data.get('product_id')), ('partner_id', '=', partner_id)])
            if comment_ids and len(comment_ids) > 0:
                comment_obj.write(cr, uid, comment_ids, {'comment': data.get('notes')})
            else:
                comment_obj.create(cr, uid, {'comment': data.get('notes'), 'partner_id': partner_id, 'product_id': data.get('product_id')})

        return super(iller_sale_line, self).create(cr, uid, data, context={})


    def product_id_change(self, cr, uid, ids, pricelist, product, qty=0,
          uom=False, qty_uos=0, uos=False, name='', partner_id=False,
          lang=False, update_tax=True, date_order=False, packaging=False, fiscal_position=False, flag=False):
        '''
            Lors du changement de produit, on regarde si un commentaire existe déjà 
            pour ce produit et ce partenaire
        '''
        comment_obj = self.pool.get('iller.sale.comment')

        comment = ''
        res = super(iller_sale_line, self).product_id_change(cr, uid, ids, pricelist, product, qty, uom, qty_uos, uos, name, partner_id, \
                                                             lang, update_tax, date_order, packaging, fiscal_position, flag)

        if product and partner_id:
            comment_ids = comment_obj.search(cr, uid, [('partner_id', '=', partner_id), ('product_id', '=', product)])
            if comment_ids and len(comment_ids) > 0:
                comment = comment_obj.browse(cr, uid, comment_ids[0]).comment

        res['value'].update({'notes': comment})

        return res


iller_sale_line()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

