#!/usr/bin/env python
# -*- encoding: utf-8 -*-


import pooler
import wizard
import base64

_form_type = """<?xml version="1.0" encoding="utf-8" ?>
<form string="Choix du type">
    <field name="type" required="1" />
</form>"""

_field_type = {
    'type': {'string': 'Type', 'type': 'selection', 'selection': [('blanche', 'MEA blanche'), ('jaune', 'MEA jaune')], 'required': True},
    'name': {'string': 'Nom', 'type': 'char'},
}

_get_form = """<?xml version="1.0" encoding="utf-8" ?>
<form string="">
    <field name="file" />
</form>"""

_field_get = {
    'file': {'string': 'Fichier', 'type': 'binary'},
    'name': {'string': 'Nom', 'type': 'char'},
}

class export_tarif_mea(wizard.interface):


    def _get_file(self, cr, uid, data, args, context={}):
        mea_obj = pooler.get_pool(cr.dbname).get('product.pricelist.mea')
        b_conf_obj = pooler.get_pool(cr.dbname).get('pricelist.mea.configuration')
        b_conf_ids = b_conf_obj.search(cr, uid, [])
        mea = mea_obj.browse(cr, uid, data['ids'])[0]

        products = []

        export = "CODE;PRODUIT;PRIX" + "\r\n"
        for pp in mea.product_ids:
            p = pp.product_id
            products.append(p.id)
            p_price = 0.00
            if data['form']['type'] == 'blanche':
                p_price = pp.new_prix_blanche
            else:
                p_price = round(pp.new_prix_jaune,2)
            export += "%s;%s;%.2f" % (p.default_code, p.name, p_price)
            export += "\r\n"

        export += "\r\n"

        data['name'] = 'mea.csv'
        data['file'] = base64.encodestring(export.encode("utf-8"))

        return data


    states = {
        'init': {
            'actions': [],
            'result': {
                'type': 'form',
                'arch': _form_type,
                'fields': _field_type,
                'state': [('end', 'Annuler'), ('get', 'Obtenir le fichier')],
            },
        },
        'get': {
            'actions': [_get_file],
            'result': {
                'type': 'form',
                'arch': _get_form,
                'fields': _field_get,
                'state': [('end', 'Sortir')],
            },
        },
    }

export_tarif_mea('export.tarif.mea')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

