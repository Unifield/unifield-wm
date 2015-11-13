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

import types
import yaml


class NewRecord(object):
    def __init__(self, model, db, key, xml_id=False, db_id=False):
        self.model = model
        self.db = db
        self.key = key
        self.xml_id = xml_id
        self.db_id = db_id
        super(Record, self).__init__()

    def __str__(self):
        return \
            '!record {model: %s, db: %s, key: %s, xml_id: %s, db_id: %s}:' % (
                self.model, self.db, self.key, self.xml_id, self.db_id
            )


def record_constructor(loader, node):
    kwargs = loader.construct_mapping(node)
    return Record(**kwargs)


class YamlInterpreter(object):

    def __init__(self, filename):
        self.filename = filename

    def process(self, yaml_string):
        """
        Processes a Yaml string. Custom tags are interpreted by 'process_'
        instance methods.
        """
        yaml.add_constructor(u"!record", record_constructor)

        is_preceded_by_comment = False
        for node in yaml.load(yaml_string):
            # Is a comment ?
            if isinstance(node, types.StringTypes):
                continue
            else:
                print node

def yaml_import(yamlfile):
    yaml_string = yamlfile.read()
    yaml_interpreter = YamlInterpreter(filename=yamlfile.name)
    yaml_interpreter.process(yaml_string)


if __name__ == '__main__':
    f = file('/home/qt/fo_test.yml')
    yaml_import(f)


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
