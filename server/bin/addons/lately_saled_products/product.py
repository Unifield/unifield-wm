# -*- encoding: utf-8 -*-

import osv
import field

class product_product(osv.osv):
    _name = "product.product"
    _inherit = "product.product"
    
    _get_last_date():
        res = ''
        return res
    
    _get_last_quantity():
        res = ''
        return res
    
    _columns = {
        'last_date': fields.function(_get_last_date, method=True, string='Dernière date', store=False),
        'last_quantity': fields.function(_get_last_quantity, method=True, string='Dernière quantité', store=False),
    }
