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

    def _contient_ligne_decoupe(self, cr, uid, ids, field_name, arg, context={}):
        """
        Retourne 'D' si une ligne de découpe figure dans la commande de vente, sinon retourne une chaîne vide.
        NB: Une ligne de découpe est visible par sale.order.line, product_id puis code_affectation dont la valeur est 'DECP'.
        """
        res = {}
        if isinstance(ids, (int, long)):
            ids = [ids]
        for so in self.browse(cr, uid, ids, context=context):
            total = 0
            res[so.id] = ''
            for sol in so.order_line:
                if sol.product_id and sol.product_id.code_affectation == 'DECP':
                    total += 1
            if total > 0:
                res[so.id] = 'd'
        return res

    def _contient_ligne_decoupe_search(self, cr, uid, obj, name, args, context={}):
        """
        Renvoie la liste des commandes de ventes suivant les cas suivants :
        - commandes ayant une ligne de commande contenant un produit allant à la découpe (product_id.code_affectation == 'DECP')
        - commandes inverses
        """
        if not len(args):
            return []
        res = []
        sql_decoupe = """
            SELECT so.id 
            FROM sale_order so, sale_order_line sol, product_product p
            WHERE sol.order_id = so.id
            AND sol.product_id = p.id
            AND p.code_affectation = 'DECP' 
            GROUP BY so.id ORDER BY so.id
        """
        for arg in args:
            if arg[1] not in ('='):
                raise osv.except_osv(_('Attention'), _("La recherche ne prend pas en charge d'autre opérateur que '='"))
            if arg[2] == 'd':
                sql = sql_decoupe
            cr.execute(sql)
            res = cr.fetchall()
        return [('id', 'in', [x[0] for x in res])]

    _columns = {
        'tournee_id': fields.many2one('tournee.iller', string='Tournée'),
        'contient_decoupe': fields.function(_contient_ligne_decoupe, fnct_search=_contient_ligne_decoupe_search, type='selection', 
            selection= [('d', 'D')], method=True, string="Découpe", store=False, required=False, readonly=True),
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

        res = super(iller_sale_order_line, self).product_id_change(cr, uid, ids, pricelist, product_id, qty, uom, qty_uos, uos, name, 
            partner_id, lang, update_tax, date_order, packaging, fiscal_position, flag)

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
