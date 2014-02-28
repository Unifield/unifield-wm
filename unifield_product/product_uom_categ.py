# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2014 TeMPO Consulting, MSF
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

from osv import fields
from osv import osv


class product_uom_categ(osv.osv):
    """
    Override the OpenERP product.uom.categ to add some
    Unifield specific features
    """
    _name = 'product.uom.categ'
    _inherit = 'product.uom.categ'

    #---  Methods to compute fields.function values

    #--- Methods to search into a fields.function

    _columns = {
        'active': fields.boolean(
            string='Active',
            help="If the active field is set to False, it allows to hide the nomenclature without removing it.",
        ),
    }

    _defaults = {
        'active': True,
    }

    #--- Model methods

    #--- Controller methods

    #--- Other methods

product_uom_categ()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
