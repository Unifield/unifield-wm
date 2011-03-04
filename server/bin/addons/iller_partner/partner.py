#!/usr/bin/env python
# -*- coding: UTF8 -*-

from osv import osv
from osv import fields
from datetime import date


class iller_partner(osv.osv):
    _name = 'res.partner'
    _inherit = 'res.partner'

    def name_search(self, cr, uid, name, args=None, operator='ilike', context=None, limit=80):
        if not args:
            args=[]
        if not context:
            context={}
        if name:
            ids = self.search(cr, uid, [('ref', operator, name)] + args, limit=limit, context=context)
            if not ids:
                ids = self.search(cr, uid, [('name', operator, name)] + args, limit=limit, context=context)
        else:
            ids = self.search(cr, uid, args, limit=limit, context=context)
        return self.name_get(cr, uid, ids, context)

    def create(self, cr, uid, vals, context={}):
        if 'reglement' in vals and vals['reglement'] == 'traite':
            raise osv.except_osv('Erreur', 'La traite a été choisi comme \
mode de règlement, vous devez donc enregistrer un RIB pour ce client')

        return super(iller_partner, self).create(cr, uid, vals, context=context)


    def write(self, cr, uid, ids, vals, context={}):
        if 'reglement' in vals and vals['reglement'] == 'traite':
            if not self._verif_rib(cr, uid, ids):
                raise osv.except_osv('Erreur', 'La traite a été choisi comme \
mode de règlement, vous devez donc enregistrer un RIB pour ce client')

        return super(iller_partner, self).write(cr, uid, ids, vals, context=context)


    def _get_total_ristourne(self, cr, uid, ids, field_name, args, context={}):
        inv_obj = self.pool.get('account.invoice')
        res = {}

        for partner in self.browse(cr, uid, ids):
            res[partner.id] = 0.00
            ## On détermine les dates de départ et de fin pour le calcul du la ristourne
            date_depart = date.today()
            date_fin = date.today()
            today = date.today()
            first_day = 1

            ## On détermine le dernier jour
            if today.month in (1,3,5,7,8,10,12):
                last_day = 31
            elif today.month in (4,6,9,11):
                last_day = 30
            elif today.year/4 == int(today.year/4):
                last_day = 29
            else:
                last_day = 28

            if partner.type_ristourne == 'd':
                if today.day <= 10:
                    last_day = 10
                elif today.day > 10 and today.day <= 20:
                    first_day = 11
                    last_day = 20

                date_depart = date(today.year, today.month, first_day)
                date_fin = date(today.year, today.month, last_day)
            elif partner.type_ristourne == 'm':
                date_depart = date(today.year, today.month, 1)
                date_fin = date(today.year, today.month, last_day)
            else:
                date_depart = date(today.year, 1, 1)
                date_fin = date(today.year, 12, 31)

            inv_ids = inv_obj.search(cr, uid, [('partner_id', '=', partner.id),
                                               ('state', '=', 'paid'),
                                               ('date_invoice', '>', date_depart),
                                               ('date_invoice', '<', date_fin)])
            for invoice in inv_obj.browse(cr, uid, inv_ids):
                res[partner.id] += invoice.amount_untaxed
            res[partner.id] = (res[partner.id]*partner.taux_ristourne)/100

        return res


    _columns = {
        ## Informations comptables
        'siret': fields.char(size=64, string='N° de siret'),
        'saisib': fields.text(string='Commentaire saisib', help='Repris sur \
                le bon de préparation'),
        'reglement': fields.selection([('traite', 'Traite'),
                                       ('espece', 'Espèce'),
                                       ('cheque', 'Chèque'),
                                       ('virement', 'Virement')],
                                       string='Règlement'),
        'nb_ex_factures': fields.integer(string='Nb ex. factures'),
        'releve': fields.selection([('N', 'Facture traditionnelle'), 
                                    ('O', 'Relevé détaillé par décade'),
                                    ('R', 'Relevé + Traite')],
                                    string='Relevés'),
        'facturation_bl': fields.selection([('m', 'Mois'),
                                            ('s', 'Semaine'),
                                            ('d', 'Décade'),
                                            ('n', 'Non')],
                                            string='Mode de règlement BL'),

        ## Informations ristourne
        'remise_fac': fields.float(digits=(16,2), string='Remise factures'),
        'taux_ristourne': fields.float(digits=(16,2), string='Taux ristourne'),
        'type_ristourne': fields.selection([('d', 'Décade'),
                                            ('m', 'Mensuelle'),
                                            ('a', 'Annuelle')],
                                            string='Type ristourne'),
        'total_ristourne': fields.function(_get_total_ristourne, type='float', 
                                    readonly=True, method=True,
                                    string='Total ristourne'),
        'appeler_ok': fields.boolean(string='Client à appeler', help='Cochez \
                la case si le client a besoin d\'être appelé.'),
        'tele_user_id': fields.many2one('res.users', string='Télé-vendeuse'),

        ## Autres champs
        'commentaire_prep': fields.text(string='Commentaire Préparation'),
        'commentaire_livraison': fields.text(string='Commentaire Livraison'),
        'depose_ok': fields.boolean(string='Dépose possible ?'),

        ## Client bloqué
        'bloque': fields.boolean(string='Bloqué ?', help='Si la case est cochée, le partenaire \
                                n\'apparaitra plus dans les recherches sur les bon de commande'),
    }

    _defaults = {
        'type_ristourne': lambda *a: 'a',
        'bloque': lambda *a: False,
        'reglement': lambda *a: 'virement',
        'facturation_bl': lambda *a: 'm',
    }


    def _verif_rib(self, cr, uid, ids, context={}):
        '''
            On vérifie qu'un RIB existe pour le partenaire
        '''
        for partner in self.browse(cr, uid, ids):
            for bank in partner.bank_ids:
                if bank.state == 'rib':
                    return True
        
        return False


    def reglement_onchange(self, cr, uid, ids, reglement, context={}):
        '''
            Traitement lors de la modification du champ reglement
            Si le reglèment est indiqué comme une traite, on vérifie si
            un RIB exitse pour le partenaire
        '''
        if reglement == 'traite' and not self._verif_rib(cr, uid, ids):
            return {'value': {}, 'warning': {'title': 'Pas de RIB pour le client', 'message':
                'Si vous choisissez la traite comme mode de règlement, vous devez \
 ajouter un RIB à ce client'}}

            return {'value': {}}

iller_partner()


class res_partner_address(osv.osv):
    _name = 'res.partner.address'
    _inherit = 'res.partner.address'

    _columns = {
        'pref_contact': fields.selection([('mail', 'E-mail'), ('fax', 'Fax'), 
                                          ('courrier', 'Courrier')],
                                          string='Préf. Envoi'),
    }

res_partner_address()


class res_users(osv.osv):
    _name = 'res.users'
    _inherit = 'res.users'

    _columns = {
        'code_saler': fields.integer(string='Code Vendeur'),
    }

res_users()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

