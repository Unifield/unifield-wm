#!/usr/bin/env python
# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2011 TeMPO Consulting, MSF. All Rights Reserved
#    Developer: Olivier DOSSMANN
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

import yaml

import pooler
#from tools import safe_eval

from tools.yaml_import import YamlInterpreter


class UnifieldYamlInterpreterException(Exception):
    pass

class UnifieldYamlInterpreter(YamlInterpreter):
    _INCLUDE_HQ2 = False

    def __init__(self, cr, module, id_map, mode, filename, noupdate=False):
        """
        Add cursors to the different databases
        """
        super(UnifieldYamlInterpreter, self).\
            __init__(cr, module, id_map, mode, filename, noupdate=noupdate)

        # Create cursors to other databases
        db_map_obj = self.pool.get('test.db.mapping')
        self.cursors = {}
        db_map_ids = db_map_obj.search(self.cr, self.uid, [
            ('db_to_use', '!=', ''),
#            ('keyword', '!=', 'sync'),
            ('keyword', 'not in', ['sync',
                'hq1c2', 'hq1c2p1', 'hq1c2p2',  # Comment this line to get HQ1C2
            ]),
        ], context=self.context)
        for db_map in db_map_obj.browse(self.cr, self.uid, db_map_ids, context=self.context):
            if not self._INCLUDE_HQ2 and db_map.keyword.startswith('hq2'):
                continue  # skip HQ2 tree
            new_cr = pooler.get_db(db_map.db_to_use)
            self.cursors[db_map.keyword] = new_cr

        for curs in self.cursors.values():
            cursor = curs.cursor()

            try:
                mod_obj = pooler.get_pool(cursor.dbname).get('ir.module.module')
                up_obj = pooler.get_pool(cursor.dbname).get('base.module.upgrade')
                mod_ids = mod_obj.search(cursor, 1, [
                    ('name', '=', 'unifield_tests_data'),
                    ('state', '!=', 'installed'),
                ], context=self.context)
                mod_obj.button_install(cursor, 1, mod_ids, context=self.context)
                up_id = up_obj.upgrade_module(cursor, 1, [], context=self.context)
                cursor.commit()
            except Exception as e:
                cursor.rollback()
            finally:
                cursor.close()

    def process(self, yaml_string):
        """
        Commit and close all cursors
        """
        for key, cr in self.cursors.iteritems():
            self.cursors[key] = pooler.get_db(cr.dbname).cursor()

        try:
            # Remove old test data
            #for cursor in self.cursors.itervalues():
                #tmd_obj = pooler.get_pool(cursor.dbname).get('test.model.data')
                #tmd_ids = tmd_obj.search(cursor, self.uid, [], context=self.context)
                #tmd_obj.unlink(cursor, self.uid, tmd_ids, context=self.context)
            res = super(UnifieldYamlInterpreter, self).process(yaml_string)
            for cursor in self.cursors.values():
                cursor.commit()
        except:
            for cr in self.cursors.values():
                cr.rollback()
        finally:
            for cr in self.cursors.values():
                cr.close()

    def process_record(self, node):
        """
        Use the good cursor to have the record created in the good DB
        """
        record, fields = node.items()[0]

        # Use the good cursor to have the record created in the good DB
        if record.db:
            self.module = 'unifield_tests_data'
            old_cr = self.cr
            new_cr = self.cursors[record.db]
            self.cr = new_cr
            data_obj = pooler.get_pool(self.cr.dbname).get('test.model.data')
            data_exist = False
            if record.xml_id:
                module = self.module
                data_ref = record.xml_id
                if '.' in record.xml_id:
                    module, data_ref = record.xml_id.split('.')

                try:
                    data_ids = data_obj.get_object_reference(self.cr, self.uid,
                        module, data_ref)
                except Exception as e:
                    data_ids = []
                if data_ids:
                    data_exist = True
                    if record.xml_id != record.id:
                        data_obj.copy(self.cr, self.uid, data_ids[0], {
                            'module': self.module,
                            'name': record.id,
                        }, context=self.context)

            # In case of non-existing data in ir_module_data, create a new record
            if not data_exist:
                try:
                    super(UnifieldYamlInterpreter, self).process_record(node)
                    if record.id in self.id_map:
                        data_obj.create(self.cr, self.uid, {
                            'name': record.id,
                            'module': self.module,
                            'res_id': self.id_map[record.id],
                            'model': record.model,
                        }, context=self.context)
                except Exception as e:
                    pass

            self.cr = old_cr
        else:
            return super(UnifieldYamlInterpreter, self).process_record(node)

    def _eval_field(self, model, field_name, expression):
        column = False
        if field_name in model._columns:
            column = model._columns[field_name]
        elif field_name in model._inherit_fields:
            column = model._inherit_fields[field_name][2]

        if column:
            if column._type == "many2one":
                if expression[0] == '@':
                    return self._eval_field_custom_expression(expression[1:])
            elif column._type == "many2many":
                ids = []
                if isinstance(expression, (list, tuple)):
                    for e in expression:
                        if e[0] == '@':
                            id = self._eval_field_custom_expression(e[1:])
                        else:
                            id = self.get_id(e)
                        ids.append(id)
                else:
                    ids = self._eval_field_custom_expression(expression[1:],
                        is_ids=True)
                return [(6, 0, ids)]

        # default
        return super(UnifieldYamlInterpreter, self)._eval_field(model,
            field_name, expression)

    def _eval_field_custom_expression(self, expression, is_ids=False):
        args = map(lambda e: e.strip(), expression.split(';'))
        if not args or len(args) < 2:
            raise UnifieldYamlInterpreterException('invalid expression')
        method = args[0]
        model = args[1]
        args = len(args) > 2 and args[2:] or []

        if method == 'search':
            return self._eval_field_custom_expression_search(model, args,
                is_ids=is_ids)
        return False

    def _eval_field_custom_expression_search(self, model_name, args,
            is_ids=False):
        # parse domain str
        if not args or len(args) != 1:
            raise UnifieldYamlInterpreterException(
                '@search;model;domain expected')
        domain = args[0]
        if not domain[0] == '[':
            domain = '[' + domain
        if not domain[-1] == ']':
            domain += ']'
        # TODO use save_eval: issue with save_eval (list of chars obtained)
        #domain = safe_eval.save_eval(domain)
        domain = eval(domain)

        # proceed search
        ids =  pooler.get_pool(self.cr.dbname).get(model_name).search(
            self.cr, self.uid, domain)
        if is_ids:
            return ids and ids or False
        return ids and ids[0] or False

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
