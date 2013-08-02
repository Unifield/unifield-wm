# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) Copyright (C) 2011 MSF, TeMPO Consulting.
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

from osv import osv
from osv import fields


class kit_import_from_version(osv.osv_memory):
    '''
    Wizard to choose a version to fill lines on a theretical kit composition
    '''
    _name = 'kit.import.from.version'

    _columns = {
        'kit_id': fields.many2one('composition.kit', string='Current kit', readonly=True, required=True),
        'product_id': fields.related('kit_id', 'composition_product_id', string='Product', readonly=True),
        'import_version_id': fields.many2one('composition.kit', string='Version'),
    }

    def import_from_version(self, cr, uid, ids, context=None):
        '''
        Call the import from version method from composition.kit
        '''
        item_obj = self.pool.get('composition.item')

        if isinstance(ids, (int, long)):
            ids = [ids]

        for kit_wizard in self.browse(cr, uid, ids, context=context):
            # Cannot import the current version
            if kit_wizard.import_version_id.id == kit_wizard.kit_id.id:
                raise osv.except_osv(_('Error'), _('You cannot import the current version'))

            # Cannot import the version of another product
            if kit_wizard.import_version_id.composition_product_id.id != kit_wizard.kit_id.composition_product_id.id:
                raise osv.except_osv(_('Error'), _('You cannot import the version of a Theoretical Kit Composition with another product than [%s] %s') % (kit_wizard.kit_id.composition_product_id.default_code, kit_wizard.kit_id.composition_product_id.name))

            lines_to_remove = []
            for line_to_remove in kit_wizard.kit_id.composition_item_ids:
                lines_to_remove.append(line_to_remove.id)

            item_obj.unlink(cr, uid, lines_to_remove, context=context)

            for line in kit_wizard.import_version_id.composition_item_ids:
                item_obj.copy(cr, uid, line.id, {'item_kit_id': kit_wizard.kit_id.id}, context=context)

        return {'type': 'ir.actions.act_window_close'}

kit_import_from_version()
