#!/usr/bin/env python
# -*- coding: UTF8 -*-

import wizard
import pooler


_configure_form = """<?xml version="1.0" encoding="utf-8" ?>
<form string="Configurer une promo" width=900 height=650>
    <separator colspan="4" string="Informations Generales" />
    <field name="start_date" required="1" />
    <field name="end_date" required="1" />
    <separator colspan="4" string="Produits" />
    <field name="product_ids" nolabel="1" colspan="4" />
</form>"""


_configure_fields = {
        'start_date': {'type': 'date', 'required': True, 'string': 'Date de debut'},
        'end_date': {'type': 'date', 'required': True, 'string': 'Date de fin'},
        'product_ids': {'type': 'many2many', 'relation': 'product.product', 'string': 'Produits'},
    }


class wizard_configure_promo(wizard.interface):

    states = {
        'init': {
            'actions': [],
            'result': {'type': 'form',
                       'arch': _configure_form,
                       'fields': _configure_fields,
                       'state': [('end', 'Annule')]},
        }
    }

wizard_configure_promo('pricelist.configure.promo')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

