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

from decimal import Decimal, ROUND_UP

class product_uom(osv.osv):
    """
    Override the OpenERP product.template to add some
    Unifield specific features
    """
    _name = 'product.uom'
    _inherit = 'product.uom'

    #---  Methods to compute fields.function values
    def _get_dummy(self, cr, uid, ids, field_name, args, context=None):
        """
        Return False for all UoM given

        :param cr: Database cursor
        :param uid: ID of the user that calls the method
        :param ids: List of ID of UoM that can be computed
        :param field_name: List of fields that need to be computed
        :param args: Potential additional arguments (defined in the field
        declaration)
        :param context: Context of the call (Optional)

        :return: Dictionary with the value for each ids of the call
        :rtype: dict
        """
        if context is None:
            context = {}

        if isinstance(ids, (int, long)):
            ids = [ids]

        res = {}
        for uom_id in ids:
            res[uom_id] = True

        return res

    #--- Methods to search into a fields.function
    def _get_compatible_uom(self, cr, uid, obj, name, args, context=None):
        """
        Returns the list of products compatible with the given UoM.
        Compatible products are products that have a default UoM with a
        category that are the same category as the given UoM

        :param cr: Database cursor
        :param uid: ID of the user that calls the method
        :param obj: Object that calls the method
        :param name: Name of the field that calls the method
        :param args: List of tuples that are used to search the compatible
        products
        :param context: Context of the call (Optional)

        :return: A list of tuples to be apply has a domain to search the
        compatible products
        :rtype: list
        """
        # Objects
        product_obj = self.pool.get('product.product')

        res = []

        for arg in args:
            if arg[0] == 'compatible_product_id':
                if not arg[2]:
                    return []
                elif isinstance(arg[2], (int, long)):
                    product = product_obj.browse(cr, uid, arg[2], context=context)
                    if product:
                        return [('category_id', '=', product.uom_id.category_id.id)]

        return res

    _columns = {
        'compatible_product_id': fields.function(
            _get_dummy,
            fnct_search=_get_compatible_uom,
            method=True,
            string='Compatible UoM',
            type='boolean',
            readonly=True,
            store=False,
            help="Is the product is compatible with the given UoM ?",
        ),
    }

    _defaults = {
    }

    #--- Model methods

    #--- Controller methods
    def _compute_round_up_qty(self, cr, uid, uom_id, qty, context=None):
        """
        Round up the quantity according to the UoM

        :param cr: Database cursor
        :param uid: ID of the user that calls the method
        :param uom_id: ID of the Unit of Measure used to round quantity
        :param qty: Quantity to be rounded
        :param context: Context of the call (optionnal)

        :return: The rounded quantity according to the rounding value of
        the Unit of Measure
        """
        uom = self.browse(cr, uid, uom_id, context=context)
        rounding_value = Decimal(str(uom.rounding).rstrip('0'))

        return float(Decimal(str(qty)).quantize(rounding_value, rounding=ROUND_UP))

    def _change_round_up_qty(self, cr, uid, uom_id, qty, fields=[], result=None, context=None):
        """
        Returns the error message and the rounded value. If the rounded
        quantity is the same as the initial quantity, don't update the
        value of fields and don't display the error message.

        :param cr: Database cursor
        :param uid: ID of the user that calls the method
        :param uom_id: ID of the Unit of Measure used to round quantity
        :param qty: Quantity to be rounded
        :param fields: List of fields to be updated by the rounding value
        :param result: Dictionary with the values and the warning message
        if any
        :param context: Context of the call (Optional)

        :return: A dictionary with value for each fields and the warning
        message if needed
        :rtype: dict
        """
        if not result:
            result = {'value': {}, 'warning': {}}

        if isinstance(fields, str):
            fields = [fields]

        message = {'title': _('Bad rounding'),
                   'message': _('The quantity entered is not valid according to the rounding value of the UoM. The product quantity has been rounded to the highest good value.')}

        if uom_id and qty:
            new_qty = self._compute_round_up_qty(cr, uid, uom_id, qty, context=context)
            if qty != new_qty:
                for f in fields:
                    result.setdefault('value', {}).update({f: new_qty})
                result.setdefault('warning', {}).update(message)

        return result

    #--- Other methods

product_uom()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
