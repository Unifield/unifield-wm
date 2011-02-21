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
        b_conf_obj = pooler.get_pool(cr.dbname).get('pricelist.promo.configuration')
        b_conf_ids = b_conf_obj.search(cr, uid, [])
        promo = promo_obj.browse(cr, uid, data['ids'])[0]

        products = []

        export = "CODE;PRODUIT;PRIX" + "\r\n"
        for pp in promo.product_ids:
            p = pp.product_id
            products.append(p.id)
            p_price = 0.00
            if data['form']['type'] == 'blanche':
                p_price = p.prix_blanche
            else:
                p_price = round(pp.prix_jaune,2)
            export += "%s;%s;%.2f" % (p.default_code, p.name, p_price)
            export += "\r\n"

        export += "\r\n"
        export += "PAGE2" + "\r\n"
        export += "CODE;PRODUIT;PRIX" + "\r\n"
        for pp2 in promo.product2_ids:
            p2 = pp2.product_id
            p_price = 0.00
            if p2.id in products:
                if data['form']['type'] == 'blanche':
                    p_price = p2.prix_blanche
                else:
                    p_price = round(pp2.prix_jaune,2)
            else:
                p_price = round(p2.list_price*b_conf_obj.browse(cr, uid, b_conf_ids[0]).bareme_page2.valeur,2)
            export += "%s;%s;%.2f" % (p2.default_code,p2.name, p_price)
            export += "\r\n"

        data['file'] = base64.encodestring(export.encode("utf-8"))
        data['name'] = 'PROMO.CSV'

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

