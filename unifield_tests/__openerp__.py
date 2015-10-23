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

{
    "name" : "Unifield Unit Tests",
    "version" : "0.1",
    "description" : "This module adds unit test for Unifield modules",
    "author" : "TeMPO Consulting, MSF",
    "category" : "Tests",
    "depends" : [
        'base',
        'sync_server',
    ],
    "init_xml" : [
    ],
    "update_xml" : [
        'automatic_tests/data/test_db_mapping_data.xml',
        'automatic_tests/views/test_db_mapping_view.xml',
        'automatic_tests/views/automatic_test_template_view.xml',
        'automatic_tests/views/automatic_test_campaign_view.xml',
        'automatic_tests/views/automatic_test_view.xml',
        'automatic_tests/wizard/views/automatic_test_add_file_view.xml',
    ],
    "demo_xml" : [],
    "test": [],
    "function": [
        ('automatic.test.template', 'update_automatic_test_template'),
    ],
    "installable": True,
    "active": False
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
