#!/usr/bin/env python
# -*- encoding: utf-8 -*-

from osv import osv, fields
import tools
import base64
import csv
import netsvc
import time
from tempfile import TemporaryFile


class wizard_import_magasin(osv.osv_memory):
    _name = 'wizard.import.magasin'
    _description = 'Import des ventes du magasin'

    _columns = {
        'file': fields.binary(string='Fichier à importer', required=True),
        'error': fields.text(string='Erreur'),
    }


    def _run_import(self, cr, uid, ids, context={}):
        '''
            Traite le fichier en entrée et importe
            les différentes ventes effectuées par
            le magasin
        '''
        poso = self.pool.get('pos.order')
        posol = self.pool.get('pos.order.line')
        data_obj = self.pool.get('ir.model.data')

        imp = self.browse(cr, uid, ids[0])

        file = imp.file
        fileobj = TemporaryFile('w+')
        fileobj.write(base64.decodestring(file))
        fileobj.seek(0)
        
        reader = csv.reader(fileobj, quotechar='\'', delimiter=';')
        reader.next()

        ## On récupère le magasin créé par le fichier data
        shop_id = False
        data_ids = data_obj.search(cr, uid, [('module', '=', 'iller_pos'), ('model', '=', 'sale.shop'), ('name', '=', 'sale_shop_magasin')], context=context)
        res_id = data_obj.read(cr, uid, data_ids, ['res_id'], context=context)
        if res_id :
            shop_id = res_id[0].get('res_id', False)

        if not shop_id:
            raise osv.except_osv('Erreur', 'Aucun magasin ne correspond au magasin Iller')

        ## On récupère le tarif général
        pricelist = False
        data_ids = data_obj.search(cr, uid, [('module', '=', 'iller_product'), ('model', '=', 'product.pricelist'), ('name', '=', 'pricelist_tarif_general')], context=context)
        res_id = data_obj.read(cr, uid, data_ids, ['res_id'], context=context)
        if res_id:
            pricelist = res_id[0].get('res_id', False)

        if not pricelist:
            raise osv.except_osv('Erreur', 'Aucune liste de prix trouvée')

        ## On récupère les modalités de paiement compta
        comptant = False
        data_ids = data_obj.search(cr, uid, [('module', '=', 'iller_pos'), ('model', '=', 'account.payment.term'), ('name', '=', 'paiement_comptant')], context=context)
        res_id = data_obj.read(cr, uid, data_ids, ['res_id'], context=context)
        if res_id:
            comptant = res_id[0].get('res_id', False)

        if not comptant:
            raise osv.except_osv('Erreur', 'Aucun mode de paiement \'Comptant\' trouvé')

        po = False
        nb_line = 0
        amount_total = 0.00
        error = ''

        for line in reader:
            nb_line = nb_line+1
            ## On remet à False les données pour la nouvelle lignes
            product_id = price_unit = qty = False
            discount = 0.00
            if line[13] in ('00101', '00146', '101', '146'):
                if not po:
                    dt = time.strptime(line[2] + line[3], '%Y%m%d%H%M')
                    date_order = time.strftime('%Y-%m-%d %H:%M:00', dt)
                    po = poso.create(cr, uid, {'shop_id': shop_id,
                                               'date_validity': date_order,
                                               'pricelist_id': pricelist,
                                               'date_order': date_order,}, context=context)
                if line[13] == '00101' or line[13] == '101':
                    ## On recherche le produit
                    product_ids = self.pool.get('product.product').search(cr, uid, [('default_code', '=', line[14])], context=context)
                    if not product_ids:
                        error += 'Erreur ligne %d :; PAs de produit trouvé [default_code : %s]' %(nb_line, line[14])
                        error += '\n'
                        continue
#                        raise osv.except_osv('Erreur', 'Pas de produit trouvé pour la ligne %d [default_code : %s]' %(nb_line, line[14]))
                    product_id = product_ids[0]
                    qty = float(line[17].replace(',', '.'))/1000.00
                    price_unit = float(line[16].replace(',', '.'))/100.00

                    posol_data = {'product_id': product_id,
                                  'qty': qty,
                                  'price_unit': price_unit,
                                  'name': line[15],
                                  'order_id': po}

                    if line[18] and line[18] != '' and float(line[18].replace(',', '.')) != 0.00:
                        discount = float(line[18].replace(',', '.'))/100.00
                        posol_data.update({'discount': (qty*price_unit)/discount})

                    amount_total += (qty*price_unit)-((qty*price_unit*discount)/100)

                    posol_id = posol.create(cr, uid, posol_data, context=context)
                elif line[13] == '00146' or line[13] == '146':
                    payment_data = {'name': 'Paiement magasin',
                                    'order_id': po,
                                    'payment_date': date_order,
                                    'payment_id': comptant,
                                    'amount': amount_total}
                    self.pool.get('pos.payment').create(cr, uid, payment_data, context=context)
                    wf_service = netsvc.LocalService("workflow")
                    wf_service.trg_validate(uid, 'pos.order', po, 'paid', cr)
                    wf_service.trg_validate(uid, 'pos.order', po, 'done', cr)
                    po = False
                    amount_total = 0.00

            self.write(cr, uid, ids, {'error': error})


            ## On cherche la vue à afficher pour afficher les erreurs
            view_id = False
            data_ids = data_obj.search(cr, uid, [('module', '=', 'iller_pos'), ('model', '=', 'ir.ui.view'), ('name', '=', 'wizard_import_magasin_done')], context=context)
            res_id = data_obj.read(cr, uid, data_ids, ['res_id'])
            if res_id:
                view_id = res_id[0].get('res_id', False)

            if not view_id:
                raise osv.except_osv('Erreur', 'La vue à afficher n\'est pas disponible dans le système')
                
            context.update({'active_id': ids[0], 'active_ids': ids})

        return {'type': 'ir.actions.act_window',
                'res_model': 'wizard.import.magasin',
                'view_mode': 'form',
                'view_type': 'form',
                'view_id': view_id,
                'context': context}



wizard_import_magasin()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

