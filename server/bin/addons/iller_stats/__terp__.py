# -*- coding: utf-8 -*-
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
{
    "name" : "Statistiques Iller",
    "version" : "1.0",
    "author" : "TeMPO Consulting, MSF",
    "category": "Statistiques",
    "description": """
    Statistiques pour Iller Distribution
    """,
    "website": "http://unifield.msf.org",
    "depends" : [
        'iller_product', 'iller_sale', 'iller_tournee', 'iller_stock',
        'iller_partner', 'iller_pos', 'iller_invoice',
    ],
    "init_xml": [
    ],
    "update_xml": [
        'entree_article_view.xml',
        'ca_client_view.xml',
        'iller_stats_report.xml',
        'stats_view.xml',
        'stats_wizard.xml',
        'sale_view.xml',
    ],
    "demo_xml": [
    ],
    "test": [
            ],
    "installable": True,
    "active": False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
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



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

