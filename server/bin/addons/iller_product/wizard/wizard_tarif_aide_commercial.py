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

import wizard
import pooler
import time

def _get_tarif(self, cr, uid, data, context):      
    date = data['form']['date']
    res=[]
    res.append([111,222])
    data['form']['liste'] = res
    return  data['form']

class wizard_tarif_aide_commercial(wizard.interface):
    form1 = '''<?xml version="1.0"?>
    <form string="Grille de Tarif">
        <field name="date"/>
    </form>'''
    form1_fields = {
    	     'date': {
	     	'string': 'Date',
		'type': 'date',
		'required':True
        },
    }

    states = {
      'init': {
            'actions': [],
            'result': {'type': 'form', 'arch':form1, 'fields':form1_fields, 'state': [('end', 'Annulation','gtk-cancel'),('report', 'Grille de Tarif','gtk-ok')]}
        },
    'report': {
            'actions': [_get_tarif],
            'result': {'type': 'print', 'report': 'tarif.aide.commercial', 'state': 'end'}
        }
    }
wizard_tarif_aide_commercial('tarif.aide.commercial')
