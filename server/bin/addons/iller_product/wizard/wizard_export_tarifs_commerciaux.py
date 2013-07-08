# -*- encoding: utf-8 -*-

import wizard
import re
import tools
import time
import base64
import cStringIO
import csv
import pooler
from osv import fields,osv
from tools.translate import _

arch = """<?xml version="1.0"?>
<form string="Exportation des tarifs commerciaux">
    <separator colspan="4" string="Exportation des tarifs commerciaux" />
    <field nolabel = "1" height="22" colspan = "4" name ="avertissement"/>
    <newline/>
    <field name="from_date"/>
    <newline/>
    <field name="achat_inclus"/>
    <newline/>
</form>
"""

fields = {
        'avertissement': {'string': u'Avertissement', 'type':'text', 'readonly':True},
        'from_date': {'string': u'Date de départ', 'type':'date', 'required':True},
        'achat_inclus': {'string': u'Inclure le prix d\'achat', 'type':'boolean'},
}

arch_end = """<?xml version="1.0"?>
<form string="Le tarif a été exporté">
    <separator string="Le tarif a été exporté"/>
    <field height="50" colspan="4" name="advice" nolabel="1"/>
    <newline/>
    <field name="name" invisible="1"/>
    <field name="data" nolabel="1" readonly="1" fieldname="name"/>
    <newline/>
</form>"""

fields_end = {
        'advice': {'string': 'Conseil', 'type':'text', 'readonly':True},        
        'data': {'string':'Fichier', 'type':'binary', 'readonly':True},
        'name': {'string':'Nom', 'type':'char', 'readonly':True},
}

def _init(self, cr, uid, data, context=None):
    ret = {}
    ret['avertissement'] = 'ATTENTION ! Ce traitement peut durer plusieurs minutes...'
    return ret

def _get_coef(cr, uid, name_bareme, bareme_obj, context=None):
    c_id = bareme_obj.search(cr, uid, [('name', '=', name_bareme)], context=context)
    if c_id:
        c = bareme_obj.browse(cr, uid, c_id[0], context=context).valeur
    else:
        c = 0.0
    return c

def act_getfile(self, cr, uid, data, context=None):
    pool = pooler.get_pool(cr.dbname)
    product_obj   = pool.get('product.product')
    categ_obj     = pool.get('product.category')
    bareme_obj    = pool.get('product.pricelist.bareme')
    rst = {}
    # Recherche de tous les barèmes à calculer:
    c01 = _get_coef(cr, uid, 'c01', bareme_obj, context=context)
    c19 = _get_coef(cr, uid, 'c19', bareme_obj, context=context)
    c17 = _get_coef(cr, uid, 'c17', bareme_obj, context=context)
    c15 = _get_coef(cr, uid, 'c15', bareme_obj, context=context)
    c13 = _get_coef(cr, uid, 'c13', bareme_obj, context=context)
    c11 = _get_coef(cr, uid, 'c11', bareme_obj, context=context)
    c09 = _get_coef(cr, uid, 'c09', bareme_obj, context=context)
    c07 = _get_coef(cr, uid, 'c07', bareme_obj, context=context)

    export = "ACHAT;ARTIC.;DESIGNATION                            ;   C01;   C19;   C17;   C15;   C13;   C11;   C09;   C07" + "\r\n"
    export += ";;; 10.00;  1.00; 2.00;  3.00;  4.00;  5.00;  6.00;  7.00  " + "\r\n"

    # Pour chaque catégorie, on imprime les prix des produits de la catégorie
    categ_ids = categ_obj.search(cr, uid, [], 0, None, 'code, name')
    for categ_id in categ_ids:
        product_ids = product_obj.search(cr, uid, [('categ_id', '=', categ_id)])
        products = product_obj.browse(cr, uid, product_ids)
        for product in products:
            # Recherche du prix selon la date saisie
            cr.execute('''SELECT nouveau_prix_achat, nouveau_prix_vente FROM product_price_history WHERE product_id=%s  AND name<=%s ORDER BY name desc LIMIT 1''',(product.id,data['form']['from_date']))
            ret = cr.fetchone()
            if ret:
                prix_achat = ret[0]
                prix_vente = ret[1]
            else:
                prix_achat = 0.0
                prix_vente = 0.0

            if data['form']['achat_inclus']:
                export += "%.2f;" %round(prix_achat,2)
            else:
                export += ";"
            export += "%s" %product.default_code + ";" + product.name + ";"
            export += "%.2f;" %round(prix_vente * c01,2)
            export += "%.2f;" %round(prix_vente * c19,2)
            export += "%.2f;" %round(prix_vente * c17,2)
            export += "%.2f;" %round(prix_vente * c15,2)
            export += "%.2f;" %round(prix_vente * c13,2)
            export += "%.2f;" %round(prix_vente * c11,2)
            export += "%.2f;" %round(prix_vente * c09,2)
            export += "%.2f;" %round(prix_vente * c07,2)
            export += "\r\n"

    export1=base64.encodestring(export.encode("utf-8"))

    rst['advice']='Pour sauvegarder le fichier, cliquer sur le petit bouton à droite du bouton Ouvrir.\n'
    rst['data'] = export1
    rst['name'] = 'Tarifs_commerciaux.csv'
    return rst

class wizard_export_tarifs_commerciaux(wizard.interface):
    states = {
            'init' : {
                    'actions' : [_init],
                    'result' : {'type' : 'form', 'arch' : arch, 'fields' : fields, 'state' : [('end', 'Annuler', 'gtk-cancel'),('export', 'Génération du fichier', 'gtk-ok') ]}
            },
            'export' : {
                    'actions' : [act_getfile],
                    'result' : {'type':'form', 'arch' : arch_end, 'fields' : fields_end, 'state' : [('end', 'Fin', 'gtk-cancel')]}
            },
    }
wizard_export_tarifs_commerciaux('wizard.export.tarifs.commerciaux')
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

