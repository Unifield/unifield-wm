# -*- encoding: utf-8 -*-
# EN CAS D'UPGRADE, VOIR LES REMARQUES DE TYPE "!!! ATTENTION MISE A JOUR !!!
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY ir FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from osv import fields
from osv import osv
from tools import config
from datetime import datetime
import time
import decimal


class product_category(osv.osv):
    _name = 'product.category'
    _inherit = 'product.category'

    _columns = {
        'code': fields.char(size=12, string='Code'),
    }

    _order = 'code, name, id'

    def name_get(self, cr, uid, ids, context={}):
        '''
        Affichage du code en plus du nom lors de 
        l'affichage d'une catégorie
        '''
        res = []
        for i in self.browse(cr, uid, ids, context=context):
            res.append((i.id, '[%s] %s' %(i.code or '', i.name)))
        return res

product_category()


class product_price_history(osv.osv):
    _name = 'product.price.history'
    _description = 'Historique Prix Achat'
    _order = 'name desc'

    _columns = {
        'name': fields.date('Valable à partir du',required=True,select=1),
        'nouveau_prix_achat': fields.float('Prix d\'achat',required=True, digits=(16,2)),
        'nouveau_prix_vente': fields.float('Prix de vente', required=True, digits=(16,2)),
        'nouveau_prix_blanche': fields.float('Prix blanche', required=True, digits=(16,2)),
        'product_id': fields.many2one('product.product','Product',ondelete='cascade', select=1),
        'fin' : fields.char(size=1, string=' '),
        'comment': fields.char(size=128, string='Commentaire'),
    }
    _defaults = {
        'name': lambda *a: time.strftime('%Y-%m-%d'),
    }

    def update_price(self, cr, uid):
        product_ids = self.search(cr, uid, [])

        for prd in self.browse(cr, uid, product_ids):
            cr.execute('''SELECT id FROM product_price_history WHERE product_id=%s  AND name<=%s ORDER BY name desc LIMIT 1''',(prd.id, time.strftime('%Y-%m-%d')))
            ret = cr.fetchone()
            prix_vente = decimal.Decimal(prd.prix_achat*prd.coeff_depart).quantize(decimal.Decimal('.01'), rounding=decimal.ROUND_DOWN)
            cr.execute('UPDATE product_price_history SET nouveau_prix_vente = %s WHERE id = %s') % (prix_vente, ret)

product_price_history()


class product_uom(osv.osv):
    _inherit = 'product.uom'
    _name = 'product.uom'

    _columns = {
        'code_uom' : fields.char(size=2, string='Code'),
    }


    def name_search(self, cr, uid, name, args=None, operator='ilike', context=None, limit=80):
        if not args:
            args=[]
        if not context:
            context={}
        if name:
            #Vérification si ce qu'on cherche est le code
            try:
                code = int(name)
            except ValueError, e:
                pass
                res = self.search(cr, uid, [('name','ilike',name)], limit=limit, context=context)
                return self.name_get(cr, uid, res, context)
            res = self.search(cr, uid, [('code_uom','ilike',name)], limit=limit, context=context)
        return self.name_get(cr, uid, res, context)

product_uom()

class product_product(osv.osv):
    _inherit = 'product.product'
    _name = 'product.product'

    def update_prix_vente(self, cr, uid, context={}):
        '''
            Met a jour le prix de vente du produit si celui-ci n'est pas arrondi
            correctement.
        '''
        product_ids = self.search(cr, uid, [], context=context)
        for product in self.browse(cr, uid, product_ids, context=context):
            prix_vente = decimal.Decimal(str(product.prix_achat*product.coeff_depart)).quantize(decimal.Decimal('.01'), rounding=decimal.ROUND_DOWN)
            # Mise a jour de list_price
            if product.list_price != float(prix_vente):
                self.write(cr, uid, [product.id], {'list_price': prix_vente}, context=context)
            cr.execute('''SELECT name FROM product_price_history WHERE product_id=%s  AND name<=%s ORDER BY name desc LIMIT 1''',(product.id,time.strftime('%Y-%m-%d')))
            ret = cr.fetchone()
            if ret:
                hist_name = ret[0]
                cr.execute('''SELECT id, nouveau_prix_vente FROM product_price_history WHERE product_id=%s  AND name=%s ORDER BY name desc''',(product.id,hist_name))
                res = cr.fetchall()
                for r in res:
                    history_id = r[0]
                    hist_vente = r[1]
                    if hist_vente != float(prix_vente):
                        cr.execute('''UPDATE product_price_history SET nouveau_prix_vente = %s WHERE id = %s''', (prix_vente, history_id))

        #pricelist_ids = self.pool.get('product.pricelist').search(cr, uid, [('tarif_special_choice', '=', 'oui')])
        #le = len(pricelist_ids)
        #i = 0
        #for pricelist in self.pool.get('product.pricelist').browse(cr,uid, pricelist_ids):
        #    i += 1
        #    print 'Traitement %s/%s -- %s' % (i, le, pricelist.name)
        #    pricelist_id = pricelist.id
        #    #partner_ids = self.pool.get('res.partner').search(cr, uid, [('property_product_pricelist', '=', pricelist_id)])
        #    cr.execute("""SELECT res_id FROM ir_property WHERE value = 'product.pricelist,%s'""" % pricelist_id)
        #    p_res = cr.fetchall()
        #    partner_ids = []
        #    for pr in p_res:
        #        partner_ids.append(int(pr[0].split(',')[1]))
        #    
        #    if not partner_ids:
        #        if not self.pool.get('sale.order').search(cr, uid, [('pricelist_id', '=', pricelist_id)]):
        #            self.pool.get('product.pricelist').unlink(cr, uid, pricelist_id)
        #    else:
        #        for partner in self.pool.get('res.partner').browse(cr, uid, partner_ids):
        #            tarif_general_choice = self.pool.get('res.partner').getSelectionValue(cr, uid, 'res.partner', 'tarif_general_choice', partner.tarif_general_choice)
        #            base_ids = self.pool.get('product.pricelist').search(cr, uid, [
        #                ('mea_choice', '=', partner.mea_choice or 'non'),
        #                ('promo_choice', '=', partner.promo_choice or 'non'),
        #                ('tarif_choice', '=', partner.tarif_choice or 'blanche'),
        #                ('name', 'ilike', tarif_general_choice)], context=context)
        #            if not base_ids:
        #                base_ids = self.pool.get('product.pricelist').search(cr, uid, [
        #                    ('mea_choice', '=', partner.mea_choice or 'non'),
        #                    ('promo_choice', '=', partner.promo_choice or 'non'),
        #                    ('tarif_choice', '=', False),
        #                    ('name', 'ilike', tarif_general_choice)], context=context)
        #                if not base_ids:
        #                    print 'Pas de base trouvee pour partner %s (%s, %s, %s, %s)' % (partner.ref, partner.mea_choice or 'non', partner.promo_choice or 'non', partner.tarif_choice or 'blanche', tarif_general_choice)
        #            else:
        #                print 'Update %s -- %s' % (partner.name, pricelist.name)
        #                version_ids = self.pool.get('product.pricelist.version').search(cr, uid, [('pricelist_id', '=', pricelist_id)])
        #                if len(version_ids) == 1:
        #                    cr.execute('''UPDATE product_pricelist_item SET base_pricelist_id = %s WHERE price_version_id = %s AND name = 'Tous les produits';''', (base_ids[0], version_ids[0]))
        #                else:
        #                    cr.execute('''UPDATE product_pricelist_item SET base_pricelist_id = %s WHERE price_version_id IN %s AND name = 'Tous les produits';''', (base_ids[0], tuple(version_ids)))
#            cr.commit()

        return True

    def write(self, cr, uid, ids, vals, context={}):
        '''
            Calcul des tarifs en fonction des prix d'achat
        '''
        history_obj = self.pool.get('product.price.history')
        for prd in self.browse(cr, uid, ids):
            history_id = history_obj.search(cr, uid, [('name', '=', datetime.now()), ('product_id', '=', prd.id)])
            list_price = vals.get('prix_achat', prd.prix_achat)*vals.get('coeff_depart', prd.coeff_depart)
            prix_vente = decimal.Decimal(str(list_price)).quantize(decimal.Decimal('.01'), rounding=decimal.ROUND_DOWN)
            vals['list_price'] = prix_vente
            vals['prix_blanche'] = vals.get('prix_achat', prd.prix_achat)*vals.get('coeff_blanche', prd.coeff_blanche)

            if 'prix_achat' in vals:
                data_history = {'name': datetime.now(),
                                'nouveau_prix_achat': vals.get('prix_achat'),
                                'nouveau_prix_vente': prix_vente,
                                'nouveau_prix_blanche': vals.get('prix_achat')*vals.get('coeff_blanche', prd.coeff_blanche),
                                'product_id': prd.id,
                                'comment': ''}
                if not 'wizard' in context:
                    data_history.update({'comment': 'Prix modifié depuis la fiche du produit'})
                if history_id and len(history_id) > 0:
                    self.pool.get('product.price.history').write(cr, uid, history_id, data_history)
                else:
                    self.pool.get('product.price.history').create(cr, uid, data_history)

            if ('coeff_depart' in vals or 'coeff_blanche' in vals) and not 'prix_achat' in vals:
                data_history = {'name': datetime.now(),
                                'nouveau_prix_achat': prd.prix_achat,
                                'nouveau_prix_vente': prix_vente,
                                'nouveau_prix_blanche': prd.prix_achat*vals.get('coeff_blanche', prd.coeff_blanche),
                                'product_id': prd.id,
                                'comment': ''}
                if not 'wizard' in context:
                    data_history.update({'comment': 'Prix modifié depuis la fiche du produit'})
                if history_id and len(history_id) > 0:
                    self.pool.get('product.price.history').write(cr, uid, history_id, data_history)
                else:
                    self.pool.get('product.price.history').create(cr, uid, data_history)
                                                                        

        return super(product_product, self).write(cr, uid, ids, vals, context=context)


    def price_get(self, cr, uid, ids, ptype='list_price', context={}):
        res = {}
        if not context:
            context = {}
        product_uom_obj = self.pool.get('product.uom')
        for product in self.browse(cr, uid, ids, context=context):
            res[product.id] = product[ptype] or 0.0
            if ptype == 'list_price':
                res[product.id] = (res[product.id] * (product.price_margin or 1.0)) + \
                        product.price_extra
            if ptype in ('list_price') and context.get('datestandard'):
                cr.execute('''SELECT nouveau_prix_vente FROM product_price_history WHERE product_id=%s  AND name<=%s ORDER BY name desc LIMIT 1''',(product.id,context['datestandard']))
                ret = cr.fetchone()
                if ret:
                    res[product.id] = ret[0]
            if ptype in ('prix_achat') and context.get('datestandard'):
                cr.execute('''SELECT nouveau_prix_achat FROM product_price_history WHERE product_id=%s AND name<=%s ORDER BY name desc LIMIT 1''',(product.id,context['datestandard']))
                ret = cr.fetchone()
                if ret:
                    res[product.id] = ret[0]
            if ptype in ('prix_blanche') and context.get('datestandard'):
                cr.execute('''SELECT nouveau_prix_achat FROM product_price_history WHERE product_id=%s AND name<=%s ORDER BY name desc LIMIT 1''',(product.id,context['datestandard']))
                ret = cr.fetchone()
                if ret:
                    res[product.id] = ret[0] * product.coeff_blanche

            if 'uom' in context:
                uom = product.uos_id or product.uom_id
                res[product.id] = product_uom_obj._compute_price(cr, uid,
                        uom.id, res[product.id], context['uom'])
        return res


    def _get_prix_achat(self, cr, uid, ids, field_name, arg, context={}):
        '''
            Retourne le prix d'achat du produit en fonction de l'historique
            des prix d'achat
        '''
        history_obj = self.pool.get('product.price.history')
        res = {}

        for product in self.browse(cr, uid, ids):
            history_ids = history_obj.search(cr, uid, [('name', '<=', datetime.now()),('product_id', '=', product.id)], offset=0, limit=1, order="name desc", context=context)
            if history_ids and len(history_ids) > 0:
                res[product.id] = {'prix_achat': history_obj.browse(cr, uid, history_ids[0]).nouveau_prix_achat,
                                   'prix_blanche': history_obj.browse(cr, uid, history_ids[0]).nouveau_prix_blanche,
                                   'list_price': history_obj.browse(cr, uid, history_ids[0]).nouveau_prix_vente}
            else:
                res[product.id] = {'prix_achat': 0.00, 'prix_blanche': 0.00, 'list_price': 0.00}

        return res


    def name_search(self, cr, uid, name, args=None, operator='ilike', context=None, limit=80):
        if not args:
            args=[]
        if not context:
            context={}
        if name:
            #Vérification si ce qu'on cherche est le code
            try:
                code = int(name)
            except ValueError, e:
                pass
                return super(product_product, self).name_search(cr, uid, name, args=args, operator=operator, context=context, limit=limit)

            #Si un code a été entré, on regarde la taille
            if len(name.strip()) == 3:
                #Si taille = 3 alors 1 zéro à gauche et 2 à droite
                #Exemple : 108 => 010800
                name = name.ljust(5, '0')
                name = name.rjust(6, '0')

            elif len(name.strip()) == 4:
                #Sinon si taille = 4 alors 2 zéros à droite
                #Exemple : 1502 => 150200
                name = name.ljust(6, '0')

            elif len(name.strip()) == 5:
                #Sinon si taille = 5 alors 1 zéro à gauche
                #Exemple : 69220 => 069220
                name = name.rjust(6, '0')

        return super(product_product, self).name_search(cr, uid, name, args, operator=operator, context=context, limit=limit)

    _columns = {
        'prix_achat': fields.function(_get_prix_achat, method=True, string='Prix d\'achat', digits=(16, int(config['price_accuracy'])), store=False, multi='prix'),
        'coeff_depart': fields.float(digits=(16,2), string='Coeff. départ'),
        'type_cond': fields.selection([('0000', 'PIECE'), ('0001', 'KILO'), ('0002', 'CARTON'), ('0003', 'BARQUETTE')], 
                                                                                            string='Type conditionnement'),
        'type_preselec': fields.selection([('0', 'Facturation pièce/carton'), ('1', 'Facturation Kilo')], string='Type préselection'),
        'coeff_blanche': fields.float(digits=(16,6), string='Coeff. blanche'),
        'coeff_jaune': fields.many2one('product.pricelist.bareme', string='Barème promo jaune'),
        'prix_blanche': fields.function(_get_prix_achat, method=True, string='Prix blanche', digits=(16, int(config['price_accuracy'])), store=True, multi='prix'),
        'list_price': fields.function(_get_prix_achat, method=True, string='Prix de vente', digits=(16, int(config['price_accuracy'])), store=False, multi='prix'),
        'prix_decembre': fields.float(digits=(16, int(config['price_accuracy'])), string='Prix décembre'),

        'type_pesee': fields.selection([('0', 'Poids variable'), ('1', 'Prix fixe'), ('2', 'Poids fixe'),
                                        ('7', 'Négoce pièce'), ('8', 'Négoce poids')], string='Type de pesée'),
        'code_affectation': fields.selection([('DECP', 'Découpe'), ('PREP', 'Préparation')], string='Code Affectation'),
        'liste_prepa': fields.selection([('0', 'Rien'), ('1', 'Congelé'), ('2', 'Salaison'), ('3', 'Volaille')],
                                                string='Liste préparation', required=True),
        'price_history': fields.one2many('product.price.history', 'product_id', 'Historique des Prix'),
        'default_code' : fields.char('Code', size=64, required=True),
    }

    _defaults = {
        'cost_method': lambda *a: 'average',
        'type_cond': lambda *a: '0001',
        'type_preselec': lambda *a: '1',
        'coeff_blanche': lambda *a: 1.00,
    }


    def coeff_price_change(self, cr, uid, ids, prix_achat, coeff_depart, coeff_blanche, context={}):
        return {'value': {'list_price': prix_achat*coeff_depart, 'prix_blanche': prix_achat*coeff_blanche}}


    def promo_blanche_change(self, cr, uid, ids, coeff_blanche, prix_achat, context={}):
        return {'value': {'prix_blanche': coeff_blanche*prix_achat}}


    def preselec_onchange(self, cr, uid, ids, type_cond, type_preselec, context={}):
        if type_preselec == '1':
            return {'value': {'type_cond': '0001', 'type_preselec': '1'}}
        elif type_preselec == '0' and type_cond == '0001':
            return {'value': {}, 'warning': {'title': 'Impossible', 'message':
                'Le type de préselection à la pièce ou au carton est incompatible avec le conditionnement KILO'}}

        return {'value': {}}


    def cond_onchange(self, cr, uid, ids, type_cond, type_preselec, context={}):
        if type_cond == '0001':
            return {'value': {'type_cond': '0001', 'type_preselec': '1'}}
        elif type_preselec == '0' and type_cond == '0001':
            return {'value': {}, 'warning': {'title': 'Impossible', 'message':
                'Le type de conditionnement KILO est incompatible avec le type de préselection à la pièce/carton'}}

        return {'value': {}}


product_product()
