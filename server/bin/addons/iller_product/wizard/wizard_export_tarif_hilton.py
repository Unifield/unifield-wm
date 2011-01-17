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


class wizard_export_tarif_hilton(osv.osv_memory):
    def act_cancel(self, cr, uid, ids, context=None):
        #self.unlink(cr, uid, ids, context)
        return {'type':'ir.actions.act_window_close' }

    def act_export_ok(self, cr, uid, ids, context=None):
        return {'type':'ir.actions.act_window_close' }

    def act_getfile(self, cr, uid, ids, context=None):
        this = self.browse(cr, uid, ids)[0]
        this.advice = _("Pour sauvegarder le fichier, cliquer sur le petit bouton à droite du bouton Ouvrir.\n")
        this.name = 'Tarif_HILTON.csv'
        context['date']=this.from_date

        partner_obj   = pooler.get_pool(cr.dbname).get('res.partner')
        product_obj   = pooler.get_pool(cr.dbname).get('product.product')
        categ_obj     = pooler.get_pool(cr.dbname).get('product.category')
        pricelist_obj = pooler.get_pool(cr.dbname).get('product.pricelist')
        version_obj   = pooler.get_pool(cr.dbname).get('product.pricelist.version')
        item_obj      = pooler.get_pool(cr.dbname).get('product.pricelist.item')

        # Recherche du partenaire dont il faut éditer le tarif
        partner_id = partner_obj.search(cr, uid, [('name', 'ilike', 'HILTON HOTEL')])
        if len( partner_id) == 0:
            raise osv.except_osv( ('Attention'), ('Ce partenaire n\'a pas été trouvé'))
        partner = partner_obj.browse(cr,uid, partner_id[0])
        pricelist_id = partner.property_product_pricelist.id

        # Recherche de la version de la liste de prix active au moment de la date saisie
        version_id = version_obj.search(cr, uid,[('pricelist_id', '=', pricelist_id), \
                                                 ('date_start',   '<=', this.from_date), \
                                                 ('date_end',     '>=', this.from_date)])
        version = version_obj.browse(cr, uid, version_id[0])

        # Formattage des dates pour l'affichage dans le fichier d'export
        date_debut_version_tarif = version.date_start
        date_debut = date_debut_version_tarif[8:10] + "/" + date_debut_version_tarif[5:7] + "/" + date_debut_version_tarif[0:4] 
        date_fin_version_tarif = version.date_end
        date_fin = date_fin_version_tarif[8:10] + "/" + date_fin_version_tarif[5:7] + "/" + date_fin_version_tarif[0:4]

        qty = 1.0
        # La variable prix va contenir les prix de tous les produits figurant sur le tarif
        prix = {} 

        # On balaie les différents éléments de cette version
        # Si c'est un produit, on en recherche le prix
        # Si c'est une catégorie de produits, on cherche le prix de tous les produits de la catégorie
        # Sinon, on recherche tous les prix de tous les produits
        item_ids = item_obj.search(cr,uid, [('price_version_id', '=', version_id)])
        for item_id in item_ids:
            item = item_obj.browse(cr, uid, item_id)
            # Si la case "hebdo" est cochée, on ne veut que les promos de la semaine (séquence 3)
            if this.hebdo and item.sequence != 3:
               continue
            # Si la case "mensuel" est cochée, on ne veut que les prix spéciaux (séquence 1)
            if this.mensuel and item.sequence != 1:
                continue
            if item.product_id:
               # La règle s'applique sur un produit
               if not prix.get(item.product_id.id) :
                  # Ce produit ne figure pas encore sur la liste, on calcule son prix
                  price = self.pool.get('product.pricelist').price_get(cr, uid, [pricelist_id],
                                        item.product_id.id, qty , partner_id[0], {
                                        'uom': item.product_id.uom_id.id,
                                        'date': this.from_date,
                                        })[pricelist_id]
                  prix[item.product_id.id] = price 
            else:
                if item.categ_id:
                   # La règle s'applique sur une catégorie de produits. Recherche de tous les produits concernés:
                   product_ids = product_obj.search(cr, uid, [('categ_id', '=', item.categ_id.id)])
                   for product_id in product_ids:
                       if not prix.get(product_id):
                          price = self.pool.get('product.pricelist').price_get(cr, uid, [pricelist_id],
                                   product_id, qty , partner_id[0], {
                                   'uom': product_obj.browse(cr, uid, product_id).uom_id.id,
                                   'date': this.from_date,
                                   })[pricelist_id]
                          prix[product_id] = price
                else:
                   # La règle concerne tous les produits
                   product_ids = product_obj.search(cr, uid, [])
                   for product_id in product_ids: 
                       if not prix.get(product_id):
                          prod =  product_obj.browse(cr, uid, product_id)
                          uom = prod.uom_id
                          price = self.pool.get('product.pricelist').price_get(cr, uid, [pricelist_id],
                                            product_id, qty , partner_id[0], {
                                            'uom': uom.id,
                                            'date': this.from_date,
                                            })[pricelist_id]
                          prix[product_id] = price

        # A ce stade, on a récupéré la liste de tous les prix des produits figurant sur la liste.
        # Il faut encore les mettre en forme 

        export = "ACTION;SUPPLIER_SKU;ITEM_DESCRIPTION;BRAND_NAME;MFG_NAME;MFG_PART_NUMBER;LONG_DESCRIPTION;PRODUCT_ORIGIN;EXPIRATION_DATE;PRODUCT_COLOR;WEIGHT;DIMENSIONS;WILLING_CASE_BREAK;CASE_WEIGHT;ITEMS_PER_CASE;PRICE_UOM_CODE;MINIMUM_ORDER_QTY;UNIT_PRICE;CURRENCY_CODE;BREAK_QTY;BREAK_AMT;PERCENT_BREAK_MULTIPLIER;BREAK_QTY3;BREAK_AMT3;PERCENT_BREAK_MULTIPLIER3;PRICE_EFFECTIVE_DATE;PRICE_EXPIRATION_DATE;TAX_EXEMPT;LEAD_TIME;LEAD_TIME_MIN;UNSPSC;UPC;IMAGE_NAME;CATEGORY_ID;CATEGORY_DESC" + "\r\n"

        export +=  u"N;Numéro d' Article;Nom du Produit;Marque;Nom du Fabricant;ID de Produit du Frabricant;Désc. détaillée de Produit;Provenance du produit;Date d'échéance du produit;Couleur du produit;Taille du produit;Dimensions de Caisse;Consentant pour escompter la caisse;Poids moyen par caisse;Articles par Caisse;Code de Prix UDM;Quantité minimum de Commande;Prix unitaire;Code de Devise;Qté d' escompte de niveau 2;Prix niveau 2;Multiplicateur niveau 2;Qté d' escompte de niveau 3;Prix niveau 3;Multiplicateur niveau 3;Date d' entrée en vigueur de prix;Prix à la date finale;Exempt d'impôts;Délai de Livraison;Période d' Attente minimum (Jours);UNSPSC;CUP;Noms de Fichiers d' Images;ID de Catégorie;Déscription Catégories" + "\r\n"

        export += "N;STRING(102);STRING(1000);STRING(256);STRING(100);STRING(256);STRING(4000);STRING(100);DATE;STRING(200);STRING(140);STRING(256);NUMERIC(1,0);NUMERIC(38,10);NUMERIC(10,0);STRING(40);NUMERIC(38,10);NUMERIC(38,10);STRING(20);NUMERIC(38,10);NUMERIC(38,10);NUMERIC(38,10);NUMERIC(38,10);NUMERIC(38,10);NUMERIC(38,10);DATE;DATE;NUMERIC(1,0);NUMERIC(4,0);NUMERIC(4,0);STRING(180);STRING(56);STRING(510);NUMERIC(10,0);STRING(1000)" + "\r\n"

        for  product_id in prix.keys():
             product = product_obj.browse(cr, uid, product_id)

             export += "U;"
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
             export += product.uom_id.name;
             export += ";"       # Colonne Q: Quantité mini de commande?
             export += str(prix.get(product_id)) + ";"
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

        export1=base64.encodestring(export.encode("utf-8"))

        return self.write(cr, uid, ids, {'state':'get', 'data': export1, 'advice': this.advice, 'name':this.name}, context=context)


    _name = "wizard.export.tarif.hilton"
    _columns = {
            'name': fields.char('Filename', 16, readonly=True),
            'from_date': fields.date('Date de départ', required=True),
            'mensuel': fields.boolean(string='Uniquement les prix spéciaux du mois'),
            'hebdo': fields.boolean(string='Uniquement les prix de la promo blanche'),
            'avertissement': fields.text('ATTENTION', readonly=True),
            'advice': fields.text('Advice', readonly=True),
            'data': fields.binary('File', readonly=True),
            'state' : fields.selection( ( ('choose','choose'),   # choose client 
                                          ('get','get'),         # get the file
                                      ) ),
            }
    _defaults = { 'state': lambda *a: 'choose', 
                  'avertissement': lambda *a: 'ATTENTION! Ce traitement peut durer plusieurs minutes...',
                }

wizard_export_tarif_hilton()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

