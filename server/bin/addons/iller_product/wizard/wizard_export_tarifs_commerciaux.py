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


class wizard_export_tarifs_commerciaux(osv.osv_memory):
    def act_cancel(self, cr, uid, ids, context=None):
        #self.unlink(cr, uid, ids, context)
        return {'type':'ir.actions.act_window_close' }

    def act_export_ok(self, cr, uid, ids, context=None):
        return {'type':'ir.actions.act_window_close' }

    def act_getfile(self, cr, uid, ids, context=None):
        this = self.browse(cr, uid, ids)[0]
        this.name = 'Tarifs_commerciaux.csv'
        this.advice = _("Pour sauvegarder le fichier, cliquer sur le petit bouton à droite du bouton Ouvrir.\n")

        product_obj   = pooler.get_pool(cr.dbname).get('product.product')
        categ_obj     = pooler.get_pool(cr.dbname).get('product.category')
        bareme_obj    = pooler.get_pool(cr.dbname).get('product.pricelist.bareme')

        # Recherche de tous les barèmes à calculer:
        c01_id = bareme_obj.search(cr, uid, [('name', '=', 'c01')])
        if c01_id:
           c01 = bareme_obj.browse(cr, uid, c01_id[0]).valeur
        else:
           c01 = 0.0

        c19_id = bareme_obj.search(cr, uid, [('name', '=', 'c19')])
        if c19_id:
           c19 = bareme_obj.browse(cr, uid, c19_id[0]).valeur
        else:
           c19 = 0.0

        c17_id = bareme_obj.search(cr, uid, [('name', '=', 'c17')])
        if c17_id:
           c17 = bareme_obj.browse(cr, uid, c17_id[0]).valeur
        else:
           c17 = 0.0

        c15_id = bareme_obj.search(cr, uid, [('name', '=', 'c15')])
        if c15_id:
           c15 = bareme_obj.browse(cr, uid, c15_id[0]).valeur
        else:
           c15 = 0.0

        c13_id = bareme_obj.search(cr, uid, [('name', '=', 'c13')])
        if c13_id:
           c13 = bareme_obj.browse(cr, uid, c13_id[0]).valeur
        else:
           c13 = 0.0

        c11_id = bareme_obj.search(cr, uid, [('name', '=', 'c11')])
        if c11_id:
           c11 = bareme_obj.browse(cr, uid, c11_id[0]).valeur
        else:
           c11 = 0.0

        c09_id = bareme_obj.search(cr, uid, [('name', '=', 'c09')])
        if c09_id:
           c09 = bareme_obj.browse(cr, uid, c09_id[0]).valeur
        else:
           c09 = 0.0

        c07_id = bareme_obj.search(cr, uid, [('name', '=', 'c07')])
        if c07_id:
           c07 = bareme_obj.browse(cr, uid, c07_id[0]).valeur
        else:
           c07 = 0.0

        export = "ACHAT;ARTIC.;DESIGNATION                            ; C. 01;   C19;  C17;   C15;   C13;   C11;   C09;   C07" + "\r\n"
        export += ";;; 10.00;  1.00; 2.00;  3.00;  4.00;  5.00;  6.00;  7.00  " + "\r\n"              

        # Pour chaque catégorie, on imprime les prix des produits de la catégorie
        categ_ids = categ_obj.search (cr, uid, [])
        for categ_id in categ_ids:
            product_ids = product_obj.search(cr, uid, [('categ_id', '=', categ_id)])
            for product_id in product_ids:
                product = product_obj.browse(cr, uid, product_id)
                # Recherche du prix selon la date saisie
                cr.execute('''SELECT nouveau_prix_achat, nouveau_prix_vente FROM product_price_history WHERE product_id=%s  AND name<=%s ORDER BY name desc LIMIT 1''',(product.id,this.from_date))
                ret = cr.fetchone()
                if ret:
                   prix_achat = ret[0]
                   prix_vente = ret[1]
                else:
                   prix_achat = 0.0
                   prix_vente = 0.0

                if this.achat_inclus:
                    export += str(round(prix_achat,2)) + ";"
                else:
                    export += ";"
                export += product.default_code + ";" + product.name + ";"
                export += str(round(prix_vente * c01,2)) + ";"
                export += str(round(prix_vente * c19,2)) + ";"
                export += str(round(prix_vente * c17,2)) + ";"
                export += str(round(prix_vente * c15,2)) + ";"
                export += str(round(prix_vente * c13,2)) + ";"
                export += str(round(prix_vente * c11,2)) + ";"
                export += str(round(prix_vente * c09,2)) + ";"
                export += str(round(prix_vente * c07,2)) + ";"
                export += "\r\n"

        export1=base64.encodestring(export.encode("utf-8"))

        return self.write(cr, uid, ids, {'state':'get', 'data': export1, 'advice': this.advice, 'name':this.name}, context=context)


    _name = "wizard.export.tarifs.commerciaux"
    _columns = {
            'name': fields.char('Filename', 16, readonly=True),
            'avertissement': fields.text('ATTENTION', readonly=True),
            'from_date': fields.date('Date de départ', required=True),
            'achat_inclus': fields.boolean('Inclure le prix d\'achat', required=True),
            'advice': fields.text('Advice', readonly=True),
            'data': fields.binary('File', readonly=True),
            'state' : fields.selection( ( ('choose','choose'),   # choose client 
                                          ('get','get'),         # get the file
                                      ) ),
            }
    _defaults = { 'state': lambda *a: 'choose', 
                  'avertissement': lambda *a: 'ATTENTION! Ce traitement peut durer plusieurs minutes...',
                }

wizard_export_tarifs_commerciaux()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

