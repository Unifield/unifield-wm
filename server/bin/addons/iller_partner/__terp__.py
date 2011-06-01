# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution	
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################


{
    "name" : "Iller Partner",
    "version" : "1.0",
    "author" : "TeMPO Consulting",
    "website": "http://www.tempo-consulting.fr",
    "category" : "Enterprise Specific Modules/Iller",
    "depends" : ["base", "account", "stock", "iller_tournee", "account_payment"],
    "init_xml" : [],
    "demo_xml" : [],
    "description": """
        Ajoute des informations sur la fiche partenaire 
        pour Distribution Iller.
    """,
    'update_xml': [
        'partner_view.xml',
        'security/iller_partner_security.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'active': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
