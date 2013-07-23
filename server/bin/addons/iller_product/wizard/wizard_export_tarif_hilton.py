# -*- encoding: utf-8 -*-

import base64
import pooler
import wizard
import time
import threading
from osv import fields,osv
from tools.translate import _


arch = """<?xml version="1.0"?>
<form string="Exportation du tarif HILTON">
    <separator colspan="4" string="Exportation du tarif HILTON" />
    <field nolabel = "1" height="22" colspan = "4" name ="avertissement"/>
    <newline/>
    <field name="from_date"/>
    <newline/>
    <field name="mensuel"/>
    <newline/>
    <field name="hebdo"/>
    <newline/>
</form>
"""

fields = {
        'avertissement': {'string': u'Avertissement', 'type':'text', 'readonly':True},
        'from_date': {'string': u'Date de départ', 'type':'date', 'required':True},
        'mensuel': {'string': u'Uniquement les prix spéciaux du mois', 'type':'boolean'},
        'hebdo': {'string': u'Uniquement les prix de la promo blanche', 'type':'boolean'},
}

arch_end = """<?xml version="1.0"?>
<form string="Le tarif a été exporté">
    <separator string="Le tarif a été exporté"/>
    <field height="75" colspan="4" name="advice" nolabel="1"/>
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


def build_product_line(cr, uid, product, date_debut, date_fin, prix):
    export = "U;"
    export += "#" + product.default_code + " ;"
    export += product.name + ";"
    export += ";"       # Colonne D: Marque?
    export += ";"       # Colonne E: Nom du fabriquant?
    export += "#;"      # Colonne F: Id de produit du fabriquant?
    if product.description:
        export += product.description + ";"
    else:
        export += ";"
    export += ";"       # Colonne H: Origine du produit?
    export += ";"       # Colonne I: Date d'échéance?
    export += ";"       # Colonne J: Couleur du produit?
    if product.weight_net != 0:
        export += str(product.weight_net) + ";"
    else:
        export += ";" 
    export += ";"       # Colonne L: Dimension caisse?
    export += "0;"      # Colonne M: Consentant pour escompter la caisse
    export += ";"       # Colonne N: Poids moyen par caisse?
    export += ";"       # Colonne O: Nb articles par caisse?
    export += product.uom_id.name + ";"
    export += ";"       # Colonne Q: Quantité mini de commande?
    export += str(prix) + ";"
    export += "EUR;"
    export += ";;;;;;"  # Colonnes T à Y : champs de type BREAK...?
    export += date_debut + ";"
    export += date_fin + ";"
    export += ";"       # Colonne AA: Prix à la date finale?
    export += ";"       # Colonne AB: Exempt d'impôt?
    export += "1;"      # Colonne AC: Délai de livraison?
    export += "1;"      # Colonne AD: Période d'attente minimum?
    export += ";"       # Colonne AE: UNSPC?
    export += "#;"      # Colonne AF: CUP?
    export += ";"       # Colonne AG: Fichier image?
    export += str(product.categ_id.name) + ";"
    export += ";"       # Colonne AI: Nom de la catégorie?
    export += "\r\n"

    return export

def _init(self, cr, uid, data, context=None):
    ret = {}
    ret['avertissement'] = 'Attention ! La génération du fichier peut prendre plusieurs minutes ...'
    return ret


def _check_if_continue(data, item):

    goon = False
    if (data['form']['hebdo'] and data['form']['mensuel']) and (item.sequence == 3 or item.sequence == 1):
        goon = True
    # Si la case "hebdo" est cochée, on ne veut que les promos de la semaine (séquence 3)
    if data['form']['hebdo'] and item.sequence != 3:
        goon = True
    # Si la case "mensuel" est cochée, on ne veut que les prix spéciaux (séquence 1)
    if data['form']['mensuel'] and item.sequence != 1:
        goon = True
    return goon


def _get_line(cr, uid, pricelist_id, qty, partner_id, data, product_id, date_debut, date_fin, pricelist_obj):
    
    price = pricelist_obj.price_get(cr, uid, [pricelist_id],
                        product_id.id, qty, partner_id[0], {
                        'uom': product_id.uom_id.id,
                        'date': data['form']['from_date'],
                        })[pricelist_id]
    line = build_product_line(cr, uid, product_id, date_debut, date_fin, price)
    return line


def _get_version_base(cr, uid, pricelist_id, data, context=None):

    pool = pooler.get_pool(cr.dbname)
    version_obj   = pool.get('product.pricelist.version')
    version_id = version_obj.search(cr, uid,[('pricelist_id', '=', pricelist_id), \
                                             ('date_start',   '<=', data['form']['from_date']), \
                                             ('date_end',     '>=', data['form']['from_date'])], context=context)
    if not version_id:
        version_id = version_obj.search(cr, uid, [('pricelist_id', '=', pricelist_id), \
                                                  ('date_start', '=', False)], context=context)
    if version_id:
        version = version_obj.browse(cr, uid, version_id[0], context=context)
    else:
        raise osv.except_osv(('Erreur'), ('Aucune liste de prix trouvée pour le client HILTON.'))

    # Formatage des dates pour l'affichage dans le fichier d'export
    date_debut_version_tarif = version.date_start
    if not date_debut_version_tarif:
        date_debut = ''
    else:
        date_debut = date_debut_version_tarif[8:10] + "/" + date_debut_version_tarif[5:7] + "/" + date_debut_version_tarif[0:4] 
    date_fin_version_tarif = version.date_end
    if not date_fin_version_tarif:
        date_fin = ''
    else:
        date_fin = date_fin_version_tarif[8:10] + "/" + date_fin_version_tarif[5:7] + "/" + date_fin_version_tarif[0:4]

    return version, date_debut, date_fin


def act_getfile(self, cr, uid, data, context=None):
    print 'debut', time.strftime('%H:%M:%S')
    context['date'] = data['form']['from_date']
    ret = {}

    pool = pooler.get_pool(cr.dbname)
    partner_obj   = pool.get('res.partner')
    product_obj   = pool.get('product.product')
    item_obj      = pool.get('product.pricelist.item')
    pricelist_obj = pool.get('product.pricelist')

    # Recherche du partenaire dont il faut éditer le tarif
    partner_id = partner_obj.search(cr, uid, [('name', 'ilike', 'HILTON')], context=context)
    if len(partner_id) == 0:
        raise osv.except_osv( ('Attention'), ('Le partenaire HILTON n\'a pas été trouvé'))
    partner = partner_obj.browse(cr,uid, partner_id[0])
    pricelist_id = partner.property_product_pricelist.id

    # Recherche de la version de la liste de prix active au moment de la date saisie
    version, date_debut, date_fin = _get_version_base(cr, uid, pricelist_id, data, context=context)

    qty = 1.0
    # La variable prix va contenir les prix de tous les produits figurant sur le tarif
    prix = {} 

    export = "ACTION;SUPPLIER_SKU;ITEM_DESCRIPTION;BRAND_NAME;MFG_NAME;MFG_PART_NUMBER;LONG_DESCRIPTION;PRODUCT_ORIGIN;EXPIRATION_DATE;PRODUCT_COLOR;WEIGHT;DIMENSIONS;WILLING_CASE_BREAK;CASE_WEIGHT;ITEMS_PER_CASE;PRICE_UOM_CODE;MINIMUM_ORDER_QTY;UNIT_PRICE;CURRENCY_CODE;BREAK_QTY;BREAK_AMT;PERCENT_BREAK_MULTIPLIER;BREAK_QTY3;BREAK_AMT3;PERCENT_BREAK_MULTIPLIER3;PRICE_EFFECTIVE_DATE;PRICE_EXPIRATION_DATE;TAX_EXEMPT;LEAD_TIME;LEAD_TIME_MIN;UNSPSC;UPC;IMAGE_NAME;CATEGORY_ID;CATEGORY_DESC" + "\r\n"

    export +=  u"N;Numéro d'article;Nom du produit;Marque;Nom du fabricant;ID du produit du fabricant;Desc. détaillée du produit;Provenance du produit;Date d'échéance du produit;Couleur du produit;Taille du produit;Dimensions de caisse;Consentant pour escompter la caisse;Poids moyen par caisse;Articles par caisse;Code de prix UDM;Quantité minimum de commande;Prix unitaire;Code de devise;Qté d'escompte de niveau 2;Prix niveau 2;Multiplicateur niveau 2;Qté d'escompte de niveau 3;Prix niveau 3;Multiplicateur niveau 3;Date d'entrée en vigueur de prix;Prix à la date finale;Exempt d'impôts;Délai de livraison;Période d'attente minimum (Jours);UNSPSC;CUP;Noms de fichiers d'images;ID de catégorie;Description catégories" + "\r\n"
    #~ export +=  u"N;Num\xe9ro d'article;Nom du produit;Marque;Nom du fabricant;ID du produit du fabricant;Desc. d\xe9taill\xe9e du produit;Provenance du produit;Date d'\xe9ch\xe9ance du produit;Couleur du produit;Taille du produit;Dimensions de caisse;Consentant pour escompter la caisse;Poids moyen par caisse;Articles par caisse;Code de prix UDM;Quantit\xe9 minimum de commande;Prix unitaire;Code de devise;Qt\xe9 d'escompte de niveau 2;Prix niveau 2;Multiplicateur niveau 2;Qt\xe9 d'escompte de niveau 3;Prix niveau 3;Multiplicateur niveau 3;Date d'entr\xe9e en vigueur de prix;Prix \xe0 la date finale;Exempt d'imp\xf4ts;D\xe9lai de livraison;P\xe9riode d'attente minimum (Jours);UNSPSC;CUP;Noms de fichiers d'images;ID de cat\xe9gorie;Description cat\xe9gories\r\n"

    export += "N;STRING(102);STRING(1000);STRING(256);STRING(100);STRING(256);STRING(4000);STRING(100);DATE;STRING(200);STRING(140);STRING(256);NUMERIC(1,0);NUMERIC(38,10);NUMERIC(10,0);STRING(40);NUMERIC(38,10);NUMERIC(38,10);STRING(20);NUMERIC(38,10);NUMERIC(38,10);NUMERIC(38,10);NUMERIC(38,10);NUMERIC(38,10);NUMERIC(38,10);DATE;DATE;NUMERIC(1,0);NUMERIC(4,0);NUMERIC(4,0);STRING(180);STRING(56);STRING(510);NUMERIC(10,0);STRING(1000)" + "\r\n"

    fichier_tmp = ''
    # On balaie les différents éléments de cette version
    # Si c'est un produit, on en recherche le prix
    # Si c'est une catégorie de produits, on cherche le prix de tous les produits de la catégorie
    # Sinon, on recherche tous les prix de tous les produits
    item_ids = item_obj.search(cr,uid, [('price_version_id', '=', version.id)], context=context)
    items = item_obj.browse(cr, uid, item_ids, context=context)
    for item in items:
        # On check si une case est cochée (ou les deux) et si le produit correspond au choix correspondant
        # On regarde aussi si la règle possède une référence à une autre liste de prix (Tous les produits)
        if _check_if_continue(data, item) and not item.base_pricelist_id:
            continue

        if item.product_id and item.product_id.id not in prix.keys():
                # La règle s'applique sur un produit
                # Ce produit ne figure pas encore sur la liste, on calcule son prix
                prix[item.product_id.id] = _get_line(cr, uid, pricelist_id, qty, partner_id,
                                            data, item.product_id, date_debut, date_fin, pricelist_obj)
                fichier_tmp += prix[item.product_id.id]
        elif item.categ_id:
                # La règle s'applique sur une catégorie de produits. Recherche de tous les produits concernés:
                product_ids = product_obj.search(cr, uid, [('categ_id', '=', item.categ_id.id)])
                products = product_obj.browse(cr, uid, product_ids, context=context)
                for product in products:
                    if product.id not in prix.keys():
                        prix[product.id] = _get_line(cr, uid, pricelist_id, qty, partner_id,
                                                    data, product, date_debut, date_fin, pricelist_obj)
                        fichier_tmp += prix[product.id]
        else:
            # Si la règle a une autre liste de prix en référence, on va regarder dans cette autre liste de prix s'il n'y a
            # pas de règles de produits qui pourraient être stockées (cas liste promo mea)
            if item.base_pricelist_id:
                # On récupère de la version de base et les dates de début/fin 
                version, date_debut, date_fin = _get_version_base(cr, uid, item.base_pricelist_id.id, data, context=context)
                # On récupère les règles correspondant à la version
                items_other = item_obj.search(cr,uid, [('price_version_id', '=', version.id)], context=context)
                items_other_records = item_obj.browse(cr, uid, items_other, context=context)
                # Pour chaque règle
                for item_other_record in  items_other_records:
                    # Si la règle a un produit, et que le produit n'a pas encore été stocké
                    if _check_if_continue(data, item_other_record):
                        continue
                    if item_other_record.product_id and item_other_record.product_id.id not in prix.keys():
                        # On récupère le prix correspondant à cette 'autre liste de prix' pour garantir l'ordre
                        # dans les tarifs (ex : liste promo mea blanche, on regarde d'abord les règles mea
                        # puis on passe dans la liste promo blanche pour voir les promos )
                        prix[item_other_record.product_id.id] = _get_line(cr, uid, pricelist_id, qty, partner_id,
                                                    data, item_other_record.product_id, date_debut, date_fin, pricelist_obj)
                        fichier_tmp += prix[item_other_record.product_id.id]

            # On recheck à nouveau pour ne pas reparcourir la règle 'Tous les produits'
            if _check_if_continue(data, item):
                continue
            # La règle concerne tous les produits
            product_ids = product_obj.search(cr, uid, [])
            products = product_obj.browse(cr, uid, product_ids, context=context)
            for product in products: 
                if product.id not in prix.keys():
                    prix[product.id] = _get_line(cr, uid, pricelist_id, qty, partner_id,
                                                data, product, date_debut, date_fin, pricelist_obj)
                    fichier_tmp += prix[product.id]

    export += fichier_tmp

    export1=base64.encodestring(export.encode("utf-8"))
    print 'fin', time.strftime('%H:%M:%S')
    ret['advice']='Pour sauvegarder le tarif qui vient d\'être généré, cliquer sur le petit bouton à droite du bouton Ouvrir.\r\n'
    ret['advice']+='Pour ouvrir le fichier sous excel, créer un nouveau fichier, aller dans le menu \"Data/Importer des données externes/Importer\" et sélectionner le jeu de caractères \"Unicode - UTF-8\"'
    ret['data'] = export1
    ret['name'] = 'Tarif_HILTON.csv'
    return ret

class wizard_export_tarif_hilton(wizard.interface):
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
wizard_export_tarif_hilton('wizard.export.tarif.hilton')
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

