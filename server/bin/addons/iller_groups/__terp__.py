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

##### Ce module génère beaucoup de dépendances, en cas de nouvelle base, commenter toutes les dépendances 
##### ainsi que le fichier ir.model.access.csv, sauf base, subscription, account, et sale, et lancer l'install ou -u base
##### Il faut ensuite décommenter ir.model.access.csv (les dépendances seront installées)
##### et mettre à jour le module. Si des problèmes persistent avec iller_tournee, commenter dans
##### iller_tournee tout ce qui attrait à la sécurité, lancer une mise à jour et décommenter
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
        'account',
        'crm',
        'document',
        'sale',
        'subscription',
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
