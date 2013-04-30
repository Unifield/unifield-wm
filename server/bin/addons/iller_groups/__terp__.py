# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2013 Tempo Consulting.
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
    'name': 'Gestion des droits pour ILLER',
    'version': '1.0',
    'category': 'Generic Modules/Projects & Services',
    'description': """
        Ce module contient les développements spécifiques
        concernant la gestion des droits pour Iller
""",
    'author': 'TeMPO Consulting',
    'website': 'http://www.tempo-consulting.com',
    'depends': [
        'base', 
        'product', 
        'hr', 
        'mrp', 
        'crm', 
        'stock',
        'purchase',
        'sale',
        'account',
        'document',
    ],
    'init_xml': [],
    'demo_xml': [],
    'update_xml': [
            'security/iller_security.xml',
            'security/ir.model.access.csv',
    ],
    'installable': True,
    'active': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
