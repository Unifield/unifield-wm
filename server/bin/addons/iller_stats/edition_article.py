#!/usr/bin/env python
# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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

from osv import osv, fields
import tools

from datetime import date, datetime, timedelta

class stats_edition_article_init(osv.osv_memory):
    _name = 'stats.edition.article.init'

    _columns = {
        'date_depart': fields.date(string='Date de départ', required=True),
        'date_fin': fields.date(string='Date de fin', required=True),
    }

    def default_get(self, cr, uid, fields, context={}):
        '''
        Initialise les valeurs avec les dates du mois en cours
        '''
        if not context:
            context={}

        res = super(stats_edition_article_init, self).default_get(cr, uid, fields, context=context)

        today = date.today()

        res['date_depart'] = date(today.year, today.month, 1).strftime('%Y-%m-%d 00:00:00')
        res['date_fin'] = today.strftime('%Y-%m-%d 00:00:00')

        return res

    def display_report(self, cr, uid, ids, context={}):
        '''
        Affiche la liste de tous les produits
        '''
        stats = self.browse(cr, uid, ids)[0]

        requete = '''
            CREATE OR REPLACE VIEW stats_edition_article AS (
                SELECT 
                   row_number() over (ORDER BY p.id) as id,
                   p.id as product_id,
                   pc.id as categ_id,
                   ph.nouveau_prix_achat as prix_achat,
                   ph.nouveau_prix_vente as prix_depart,
                   sum(relin.product_qty) as qty_entrees, 
                   sum(relout.product_qty) as qty_sorties,
                   sum(relsto.product_qty) as qty_stock_init,
                   sum(relsto.product_qty)*ph.nouveau_prix_vente as val_st_init,
                   sum(relsto.product_qty)+sum(relin.product_qty)-sum(relout.product_qty) as qty_stock,
                   sum(relin.product_qty*relin.price_unit) as val_achat,
                   sum(relout.product_qty*relout.price_unit) AS val_sorties,
                   sum(relout.product_qty*ph.nouveau_prix_achat) val_consom,
                   sum(relout.product_qty*relout.price_unit)-sum(relout.product_qty*ph.nouveau_prix_achat) AS val_marge,
                   (sum(relout.product_qty*relout.price_unit)-sum(relout.product_qty*ph.nouveau_prix_achat))/sum(relout.product_qty*relout.price_unit)*100 AS taux_marge
                FROM 
                   product_product p 
                  LEFT JOIN product_template pt
                   ON p.product_tmpl_id = pt.id
                  LEFT JOIN product_category pc
                   ON pt.categ_id = pc.id
                  LEFT JOIN product_price_history ph
                   ON ph.product_id = p.id
                  LEFT JOIN 
                   (SELECT pol.price_unit, sm.product_qty, sp.type, sm.product_id FROM stock_move sm LEFT JOIN stock_picking sp ON sm.picking_id = sp.id LEFT JOIN purchase_order_line pol ON sm.purchase_line_id = pol.id WHERE sp.type = 'in' AND sm.date_planned >= '%s' AND sm.date_planned <= '%s') relin 
                   ON relin.product_id = p.id 
                  LEFT JOIN 
                   (SELECT sol.price_unit, sm.product_qty, sp.type, sm.product_id FROM stock_move sm LEFT JOIN stock_picking sp ON sm.picking_id = sp.id LEFT JOIN sale_order_line sol ON sm.sale_line_id = sol.id WHERE sp.type = 'out' AND sm.date_planned >= '%s' AND sm.date_planned <= '%s') relout 
                   ON relout.product_id = p.id 
                  LEFT JOIN
                   (SELECT sm.product_qty, sm.product_id FROM stock_move sm LEFT JOIN stock_picking sp ON sm.picking_id = sp.id WHERE sm.date_planned < '%s' AND sp.type in ('in', 'out')) relsto
                   ON relsto.product_id = p.id
                 GROUP BY p.id, pc.id, pt.name, ph.nouveau_prix_achat, ph.nouveau_prix_vente);
        ''' % (stats.date_depart, stats.date_fin, stats.date_depart, stats.date_fin, stats.date_depart)

        cr.execute(requete)

        return {'type': 'ir.actions.act_window',
                'res_model': 'stats.edition.article',
                'view_mode': 'tree',
                'view_type': 'form'}

stats_edition_article_init()

class stats_edition_article(osv.osv):
    _name = 'stats.edition.article'
    _auto = False

    _columns = {
        'product_id': fields.many2one('product.product', string='Article', select="1"),
        'categ_id': fields.many2one('product.category', string='Catégorie', select="1"),
#        'tva': fields.many2one('account.account.tax', string='Code TVA'),
#        'stock_mini': fields.float(string='Stock Mini'),
        'prix_achat': fields.float(string='PX. Achat'),
        'prix_depart': fields.float(string='PX. Dep/Rung'),
        'qty_entrees': fields.float(string='Qtés Entrées'),
        'qty_stock_init': fields.float(string='Qté St. Init.'),
        'qty_sorties': fields.float(string='Qtés Sorties'),
        'qty_stock': fields.float(string='Qtés Stock'),
        'val_achat': fields.float(string='Val. Achats'),
        'val_st_init': fields.float(string='Val. St. Init'),
        'val_sorties': fields.float(string='Val. Sorties'),
        'val_consom': fields.float(string='Val. Conso.'),
        'val_marge': fields.float(string='Val. marge'),
        'taux_marge': fields.float(string='Taux marge', select="2"),
    }
    _order = 'categ_id, product_id'

stats_edition_article()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

