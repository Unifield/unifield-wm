# -*- coding: utf-8 -*-
import time

import wizard
import netsvc
import pooler
import osv
import base64
import csv


arch = """<?xml version="1.0"?>
<form string="Exportation du Tarif SNCF">
        <field name="advice"/>
        <newline/>
        <field name="from_date" colspan="1"/>
        <newline/>
        <field name="file" />
        <separator colspan="4" />
</form>
"""

fields = {
        'advice': {'string': 'Avertissement', 'type':'text', 'readonly':True},
        'from_date': {'string': 'Date de départ', 'type':'date', 'required':True},
        'file': {'string':'Fichier CSV de la SNCF', 'type':'binary', 'required':True},
}

arch_end = """<?xml version="1.0"?>
<form string="Le tarif a été exporté">
        <field name="advice"/>
        <newline/>
        <field name="tarif_SNCF.csv" />
        <newline/>
        <field name="nb" colspan="4" />
</form>"""
fields_end = {
        'advice': {'string': 'Attention', 'type':'text', 'readonly':True},        
        'tarif_SNCF.csv': {'string':'Taille du fichier tarif', 'type':'binary', 'required':True},
        'nb': {'string':'Nombre de prix mis à jour', 'type':'integer', 'readonly':True},

}
def _init(self, cr, uid, data, context):
    ret = {}
    ret['advice'] = 'Le fichier EXCEL reçu de la SNCF doit avoir été converti au format CSV.\r\nLe séparateur de champ est \';\'.\r\nLe séparateur de texte est vide (il n\'y en a pas).'
    return ret


def _export(self, cr, uid, data, context):

#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# ATTENTION: QUAND ON SAUVEGARDE LE FICHIER .CSV:
# LE SEPARATEUR DE CHAMP DOIT ETRE ";"
# LE SEPARATEUR DE TEXTE EST VIDE (IL N'Y EN A PAS)
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!


    product_obj   = pooler.get_pool(cr.dbname).get('product.product')
    partner_obj   = pooler.get_pool(cr.dbname).get('res.partner')
    categ_obj     = pooler.get_pool(cr.dbname).get('product.category')
    pricelist_obj = pooler.get_pool(cr.dbname).get('product.pricelist')
    version_obj   = pooler.get_pool(cr.dbname).get('product.pricelist.version')
    item_obj      = pooler.get_pool(cr.dbname).get('product.pricelist.item')

    # Recherche du client SNCF
    partner_id = partner_obj.search(cr, uid, [('name', 'ilike', 'SNCF STRASBOURG')])
    if len( partner_id) == 0:
        raise osv.except_osv( ('Attention'), ('Ce partenaire n\'a pas été trouvé'))
    partner = partner_obj.browse(cr,uid, partner_id[0])
    pricelist_id = partner.property_product_pricelist.id

    # Recherche de la version de la liste de prix active au moment de la date saisie
    version_id = version_obj.search(cr, uid,[('pricelist_id', '=', pricelist_id), \
                                             ('date_start',   '<=', data['form']['from_date'] ), \
                                             ('date_end',     '>=', data['form']['from_date'])])
    version = version_obj.browse(cr, uid, version_id[0])

    # Lecture du fichier CSV et rechercher des prix des produits Iller
    buf=base64.decodestring(data['form']['file']).split('\n')
    reader = csv.reader(buf,delimiter="\t")
    ret = {}
    nb = 0
    qty = 1.0
    export = ''
    for row in reader:
        if row:
           cols = row[0].split(';')
           # cols[0] contient le code du produit (à quelques 0 près)
           # on cherche le produit correspond et son prix qui sera mis dans cols[3]
           if cols[0]:
              long = len(cols[0])
              if (long == 3) or (long == 4):
                 code = int(cols[0]) * 100 
              product_ids = product_obj.search(cr, uid, [('default_code', 'ilike', str(code))])
              if not product_ids:
                 print "********** PAS DE PRODUIT DE CODE %s" %code
              else:
                 prod = product_obj.browse(cr, uid, product_ids[0])
                 uom = prod.uom_id
                 prix = pricelist_obj.price_get(cr, uid, [pricelist_id],
                                        product_ids[0], qty , partner_id[0], {
                                        'uom': uom.id,
                                        'date': data['form']['from_date'],
                                        })[pricelist_id]
                 cols[3] =  str(round(prix,2))
                 nb += 1
                     
           for col in cols:
               export += unicode(col,'utf-8') + ";"

        export += "\r\n"

    export1=base64.encodestring(export.encode("utf-8"))

    ret['advice']='Pour sauvegarder le tarif qui vient d\'être généré, cliquer sur le petit bouton à droite du bouton Ouvrir.'
    ret['nb'] = nb
    ret['tarif_SNCF.csv'] = export1
    return ret

class export_tarif_sncf(wizard.interface):
    states = {
            'init' : {
                    'actions' : [_init],
                    'result' : {'type' : 'form', 'arch' : arch, 'fields' : fields, 'state' : [('end', 'Cancel', 'gtk-cancel'),('export', 'Génération du tarif', 'gtk-ok') ]}
            },
            'export' : {
                    'actions' : [_export],
                    'result' : {'type':'form', 'arch' : arch_end, 'fields' : fields_end, 'state' : [('end', 'Fin', 'gtk-cancel')]}
            },
    }
export_tarif_sncf('export.tarif.sncf')
