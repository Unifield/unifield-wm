#!/usr/bin/env python
# -*- encoding: utf-8 -*-

from osv import osv
from osv import fields


class iller_sale(osv.osv):
    _name = 'sale.order'
    _inherit = 'sale.order'

    
    def action_ship_create(self, cr, uid, ids, *args):
        '''
            Ajoute une tournée au stock.picking générés lors de
            la confirmation de la commande de vente
        '''
        pick_obj = self.pool.get('stock.picking')

        res = super(iller_sale, self).action_ship_create(cr, uid, ids, *args)

        for so in self.browse(cr, uid, ids):
            if so.tournee_id and so.tournee_id.id:
                for pick in so.picking_ids:
                    pick_obj.write(cr, uid, [pick.id], {'tournee_id': so.tournee_id.id})

        return res


    def onchange_partner_id(self, cr, uid, ids, partner_id, context={}):
        '''
            Met à jour la tournée en fonction du partenaire
        '''
        res = super(iller_sale, self).onchange_partner_id(cr, uid, ids, partner_id)

        if partner_id:
            partner = self.pool.get('res.partner').browse(cr, uid, partner_id, context=context)
            if partner.tournee1 and partner.tournee1.id :
                res['value'].update({'tournee_id': partner.tournee1.id})
            elif partner.tournee2 and partner.tournee2.id :
                res['value'].update({'tournee_id': partner.tournee2.id})
            elif partner.tournee3 and partner.tournee3.id : 
                res['value'].update({'tournee_id': partner.tournee3.id})

        return res

    def action_wait(self, cr, uid, ids, *args):
        """
        Fonction utilisée lors de la validation d'une commande.
        Permet de générer un fichier Bizerba par commande donnée et de l'attacher auxdites commandes
        """
        super(iller_sale, self).action_wait(cr, uid, ids, *args)
        export_bizerba_obj = self.pool.get('export.bizerba')
        export_bizerba_obj.get_file(cr, uid, ids)

    _columns = {
        'tournee_id': fields.many2one('tournee.iller', string='Tournée'),
    }


iller_sale()


class iller_sale_order_line(osv.osv):
    _name = 'sale.order.line'
    _inherit = 'sale.order.line'


    def product_id_change(self, cr, uid, ids, pricelist, product_id, qty=0,
            uom=False, qty_uos=0, uos=False, name='', partner_id=False,
            lang=False, update_tax=True, date_order=False, packaging=False, fiscal_position=False, tournee_id=False, flag=False):
        '''
            Lors du changement de produit, mettre à jour le poste
            de préparation associé
        '''
        product_obj = self.pool.get('product.product')
        tournee_obj = self.pool.get('tournee.iller')

        res = super(iller_sale_order_line, self).product_id_change(cr, uid, ids, pricelist, product_id, qty, uom, qty_uos, uos, name, partner_id,
                                                             lang, update_tax, date_order, packaging, fiscal_position, flag)

        if product_id and tournee_id:
            product = product_obj.browse(cr, uid, product_id)
            tournee = tournee_obj.browse(cr, uid, tournee_id)
            if product.code_affectation == 'DECP':
                res['value'].update({'poste_id': tournee.decoupe_id.id})
            else:
                res['value'].update({'poste_id': tournee.prep_id.id})

        return res


    _columns = {
        'poste_id': fields.many2one('iller.poste', string='Poste'), 
    }


iller_sale_order_line()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
