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
    'type': {'string': 'Type', 'type': 'selection', 'selection': [('blanche', 'Promo blanche'), ('jaune', 'Promo jaune')], 'required': True},
}

_get_form = """<?xml version="1.0" encoding="utf-8" ?>
<form string="">
    <field name="file" />
</form>"""

_field_get = {
    'file': {'string': 'Fichier', 'type': 'binary'},
}

class export_tarif_promo(wizard.interface):


    def _get_file(self, cr, uid, data, args, context={}):
        promo_obj = pooler.get_pool(cr.dbname).get('product.pricelist.promo')
        product_obj = pooler.get_pool(cr.dbname).get('product.product')
        promo = promo_obj.browse(cr, uid, data['ids'])[0]

        export = "PRODUIT;PRIX" + "\r\n"
        for p in promo.product_ids:
            p_price = 0.00
            if data['form']['type'] == 'blanche':
                p_price = p.prix_blanche
            else:
                p_price = round(p.prix_jaune,2)
            export += "%s;%s" % (p.name, p_price)
            export += "\r\n"

        export += "PAGE2;   " + "\r\n"
        for p2 in promo.product2_ids:
            p_price = 0.00
            if data['form']['type'] == 'blanche':
                p_price = p2.prix_blanche
            else:
                p_price = round(p2.prix_jaune,2)
            export += "%s;%s" % (p2.name, p_price)
            export += "\r\n"

        export1=base64.encodestring(export.encode("utf-8"))

        data['file'] = export1

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

export_tarif_promo('export.tarif.promo')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

