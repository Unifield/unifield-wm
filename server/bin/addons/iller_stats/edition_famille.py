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

class stats_edition_famille_init(osv.osv_memory):
    _name = 'stats.edition.famille.init'

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

        res = super(stats_edition_famille_init, self).default_get(cr, uid, fields, context=context)

        today = date.today()

        res['date_depart'] = date(today.year, today.month, 1).strftime('%Y-%m-%d 00:00:00')
        res['date_fin'] = today.strftime('%Y-%m-%d 00:00:00')

        return res

    def display_report(self, cr, uid, ids, context={}):
        '''
        Affiche la liste de tous les familles
        '''
        stats = self.browse(cr, uid, ids)[0]

        requete = '''
            CREATE OR REPLACE VIEW stats_edition_famille AS (
                SELECT 
                   row_number() over (ORDER BY pc.id) as id,
                   pc.id as categ_id,
                   sum(relin.product_qty) as qty_entrees, 
                   sum(relout.product_qty) as qty_sorties,
                   sum(relsto.product_qty) as qty_stock_init,
                   sum(relsto.product_qty*ph.nouveau_prix_vente) as val_st_init,
                   0.00 as qty_inv,
                   sum(relsto.product_qty)+sum(relin.product_qty)-sum(relout.product_qty) as qty_stock,
                   sum(relsto.product_qty)+sum(relin.product_qty)-sum(relout.product_qty) as qty_stock_debut,
                   sum(relin.product_qty*relin.price_unit) as val_achat,
                   sum(relout.product_qty*relout.price_unit) AS val_sorties,
                   sum(relout.product_qty*ph.nouveau_prix_achat) val_consom,
                   sum(relsto.product_qty*ph.nouveau_prix_vente)+sum(relin.product_qty*relin.price_unit)-sum(relout.product_qty*relout.price_unit) as val_stock_debut,
                   sum(relout.product_qty*relout.price_unit)-sum(relout.product_qty*ph.nouveau_prix_achat) AS val_marge,
                   0.00-(sum(relsto.product_qty)+sum(relin.product_qty)-sum(relout.product_qty)) as val_inv_sis,
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
                 GROUP BY pc.id
                 ORDER BY pc.id)
        ''' % (stats.date_depart, stats.date_fin, stats.date_depart, stats.date_fin, stats.date_depart)

        cr.execute(requete)

        return {'type': 'ir.actions.act_window',
                'res_model': 'stats.edition.famille',
                'view_mode': 'tree',
                'view_type': 'form'}

stats_edition_famille_init()

class stats_edition_famille(osv.osv):
    _name = 'stats.edition.famille'
    _auto = False

    _columns = {
        'categ_id': fields.many2one('product.category', string='Catégorie', select="1"),
#        'tva': fields.many2one('account.account.tax', string='Code TVA'),
#        'stock_mini': fields.float(string='Stock Mini'),
        'qty_entrees': fields.float(string='Qtés Entrées'),
        'qty_stock_init': fields.float(string='Qté St. Init.'),
        'qty_sorties': fields.float(string='Qtés Sorties'),
        'qty_stock': fields.float(string='Qtés Stock'),
        'qty_stock_debut': fields.float(string='Qtés S. Début'),
        'qty_inv': fields.float(string='Qtés Invent'),
        'val_achat': fields.float(string='Val. Achats'),
        'val_st_init': fields.float(string='Val. St. Init'),
        'val_sorties': fields.float(string='Val. Sorties'),
        'val_consom': fields.float(string='Val. Conso.'),
        'val_stock_debut': fields.float(string='Val. St. Début'),
        'val_marge': fields.float(string='Val. marge'),
        'val_inv_sis': fields.float(string='INV-(SIS)'),
        'taux_marge': fields.float(string='Taux marge', select="2"),
    }

    _defaults = {
        'qty_inv': lambda *a: 0.00,
    }

    _order = 'categ_id'

stats_edition_famille()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

