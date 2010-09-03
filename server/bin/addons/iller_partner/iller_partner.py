#!/usr/bin/env python
# -*- coding: UTF8 -*-

from osv import osv
from osv import fields


class iller_partner(osv.osv):
    _name = 'res.partner'
    _inherit = 'res.partner'

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

        ## Informations ristourne
        'remise_fac': fields.float(digits=(16,2), string='Remise factures'),
        'taux_ristourne': fields.float(digits=(16,2), string='Taux ristourne'),
        'type_ristourne': fields.selection([('d', 'Décade'),
                                            ('m', 'Mensuelle'),
                                            ('a', 'Annuelle')],
                                            string='Type ristourne'),
        'appeler_ok': fields.boolean(string='Client à appeler', help='Cochez \
                la case si le client a besoin d\'être appelé.'),
        'tele_user_id': fields.many2one('res.users', string='Télé-vendeuse'),
    }


    def _verif_rib(self, cr, uid, ids, context={}):
        '''
            On vérifie qu'un RIB existe pour le partenaire
        '''


    def reglement_onchange(self, cr, uid, ids, reglement, context={}):
        '''
            Traitement lors de la modification du champ reglement
            Si le reglèment est indiqué comme une traite, on vérifie si
            un RIB exitse pour le partenaire
        '''
        if reglement == 'traite':
            self._verif_rib(cr, uid, ids)

        return

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

