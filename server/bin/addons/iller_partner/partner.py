#!/usr/bin/env python
# -*- coding: UTF8 -*-

from osv import osv
from osv import fields
from datetime import date
from tools.translate import _

class iller_partner(osv.osv):
    _name = 'res.partner'
    _inherit = 'res.partner'

    _order = 'ref, name, id'

    # Fonction générique permettant de récupérer le champ name d'un field.selection
    # en lui passant le nom de l'objet contenant le field.selection, le nom du champ en question
    # et la valeur étant la clé du field.selection pour laquelle on veut récupérer le nom
    # Ex : getSelectionValue(cr, uid, 'product.product', 'type_cond', product_browse.type_cond)
    def getSelectionValue(self, cr, uid, model,fieldName,field_val):
        return dict(self.pool.get(model).fields_get(cr, uid)[fieldName]['selection'])[field_val]


    def create(self, cr, uid, vals, context=None):
        '''
            Ecriture de la liste de prix correspondante
        '''
        # Récupération des valeurs dans vals, et attribution par défaut sinon
        if 'tarif_choice' in vals:
            tarif_choice = vals['tarif_choice']
        else:
            tarif_choice = 'blanche'
        if 'promo_choice' in vals:
            promo_choice = vals['promo_choice']
        else:
            promo_choice = 'oui'
        if 'mea_choice' in vals:
            mea_choice = vals['mea_choice']
        else:
            mea_choice = 'oui'
        if 'tarif_general_choice' in vals:
            tarif_general_choice = vals['tarif_general_choice']
        else:
            tarif_general_choice = 'nu01'

        tarif_general_choice = self.getSelectionValue(cr, uid, 'res.partner', 'tarif_general_choice', tarif_general_choice)

        # On récupère l'id de la liste de prix correspondant aux paramètres entrés dans le formulaire partner
        pricelist_ids = self.pool.get('product.pricelist').search(
                cr, uid, [
                            ('tarif_choice', '=', tarif_choice or 'blanche'),
                            ('promo_choice', '=', promo_choice or 'non'),
                            ('mea_choice', '=', mea_choice or 'non'),
                            ('name', 'ilike', tarif_general_choice)
                        ], context=context)
        
        # Si aucune liste de prix, on prend la liste de base par défaut
        if not pricelist_ids:
            pricelist_ids = self.pool.get('product.pricelist').search(cr, uid, [('name', 'ilike', tarif_general_choice)], context=context)
        pricelist_record = self.pool.get('product.pricelist').browse(cr, uid, pricelist_ids[0],context=context)
        
        vals.update({'property_product_pricelist':pricelist_record.id})

        return super(iller_partner, self).create(cr, uid, vals, context=context)


    def write(self, cr, uid, ids, vals, context=None):
        '''
            Ecriture de la liste de prix correspondante
        '''
        if isinstance(ids, (int, long)):
            ids = [ids]
        
        version_obj = self.pool.get('product.pricelist.version')
        pricelist_obj = self.pool.get('product.pricelist')
        # Si une écriture est effectuée sur 'property_product_pricelist', alors on effectue le comportement par défaut
        # car on est dans le cas où le tarif spécial écrit une nouvelle liste de prix
        # Si is_tarif_speciaux == True alors on fait le write par défaut car on est dans le cas d'un tarif spécial

        if 'property_product_pricelist' in vals and context and ('is_tarif_speciaux' in context and context['is_tarif_speciaux'] == True):
            return super(iller_partner, self).write(cr, uid, ids, vals, context=context)
            
        for partner_record in self.browse(cr, uid, ids, context=context):
        
            # Récupération des valeurs dans vals si existantes, sinon on prend celles du partner
            tarif_choice = vals.get('tarif_choice', partner_record.tarif_choice)
            promo_choice = vals.get('promo_choice', partner_record.promo_choice)
            mea_choice = vals.get('mea_choice', partner_record.mea_choice)
            tarif_general_choice = vals.get('tarif_general_choice', partner_record.tarif_general_choice)
            tarif_special_choice = vals.get('tarif_special_choice', partner_record.tarif_special_choice)

            base_ids = []
            pricelist_ids = []
            not_same_pricelist = False

            # Récupération de la valeur associée à la clé du field.selection et récupération de la liste correspondante
            tarif_general_choice = self.getSelectionValue(cr, uid, 'res.partner', 'tarif_general_choice', tarif_general_choice)
            # On cherche la pricelist de base correspondant à la sélection (NU01, NU02....)
            pl_id = pricelist_obj.search(cr, uid, [('name', '=', tarif_general_choice)], context=context)
            if pl_id:
                # On cherche la version de base de la pricelist du partner
                base_ids = version_obj.search(cr, uid, [('pricelist_id', '=', pl_id[0]), ('base_ok', '=', True)])

## Cas d'erreur :Aucune version de base n'est trouvée à ce moment là : problème de pricelist

            # Si aucune version de base n'est trouvée, on récupère celle que le partenaire a déjà par défaut
            if not base_ids:
                base_ids = version_obj.search(cr, uid, [('pricelist_id', '=', partner_record.property_product_pricelist.id)])
                # Si toujours aucune version de base n'est trouvée, on prend la base de NU01
                if not base_ids:
                    # Si on a pas de base, il y a une erreur dans la pricelist (cas où 
                    # des partner existants pointent sur une ancienne liste de prix)
                    pl_id = pricelist_obj.search(cr, uid, [('name', '=', 'NU01')], context=context)
                    base_ids = version_obj.search(cr, uid, [('pricelist_id', '=', pl_id)], context=context)
                    if not base_ids:
                        # Permet d'éviter de prendre NU01 erroné
                        pl_id = pricelist_obj.search(cr, uid, [('name', '=', 'NU01'), ('id', '<>', 1)], context=context)
                        base_ids = version_obj.search(cr, uid, [('pricelist_id', '=', pl_id)], context=context)
                        # Indique à l'utilisateur que la liste de prix pointée n'a pas de version de base
                        raise osv.except_osv(_('La liste de prix %s ne possède pas de version de base !\nVérifiez que vous utilisez des listes de prix correctes') % (partner_record.property_product_pricelist.id))
            base_version = base_ids[0]
            base = version_obj.browse(cr, uid, base_version, context=context)

## Cas où on a un tarif spécial sur le client

            # Si le tarif spécial est à oui, on regarde s'il existe une liste de prix associée à ce partenaire
            #    -> Cas où l'utilisateur modifie le tarif spécial de 'non' à 'oui' quand le partenaire est déjà
            #    lié à un tarif
            # OU BIEN si le tarif general de base est modifié, ET que le tarif spécial est à 'oui' 
            #    -> Cas où l'utilisateur change le tarif général de base (ex : NU01 à NU03), sans changer
            #    le tarif spécial et que celui-ci est à 'oui'
            if ('tarif_special_choice' in vals and vals['tarif_special_choice'] == 'oui') or \
                ('tarif_general_choice' in vals and partner_record.tarif_special_choice == 'oui' ):
                # On récupère la liste de prix CSP si elle existe pour ce partenaire et ces paramètres
                pricelist_ids = pricelist_obj.search(
                        cr, uid, [
                                    ('tarif_special_choice', '=', tarif_special_choice or 'non'),
                                    ('tarif_choice', '=', tarif_choice or 'blanche'),
                                    ('promo_choice', '=', promo_choice or 'non'),
                                    ('mea_choice', '=', mea_choice or 'non'),
                                    ('name', 'ilike', ('CSP %s %s' % (partner_record.ref, partner_record.name)) or base.name[-4:] or 'NU01')
                                ], context=context)
                # Si aucune pricelist spéciale n'existe, on prend la liste spéciale du partenaire
                # Cas où on crée une liste spéciale à partir du tarif général de base (NU01...NU04)
                if not pricelist_ids:
                    pricelist_ids = pricelist_obj.search(
                            cr, uid, [
                                        ('tarif_special_choice', '=', tarif_special_choice or 'non'),
                                        ('promo_choice', '=', promo_choice or 'non'),
                                        ('mea_choice', '=', mea_choice or 'non'),
                                        ('name', 'ilike', ('CSP %s %s' % (partner_record.ref, partner_record.name)) or base.name[-4:] or 'NU01')
                                    ], context=context)
                if not pricelist_ids:
                    pricelist_ids = pricelist_obj.search(
                            cr, uid, [
                                        ('tarif_special_choice', '=', tarif_special_choice or 'non'),

                                        ('name', 'ilike', ('CSP %s %s' % (partner_record.ref, partner_record.name)) or base.name[-4:] or 'NU01')
                                    ], context=context)
                                    
                # On récupère la version de base de la liste de prix spéciale
                base_special_ids = version_obj.search(cr, uid, [('pricelist_id', 'in', pricelist_ids), ('base_ok', '=', True)])
                if base_special_ids:
                    base_special = version_obj.browse(cr, uid, base_special_ids[0], context=context)
                    # Si cette base n'a pas le même nom que la sélection du formulaire, on indique qu'il faudra rechercher
                    # de nouveau une liste de prix puisque celle trouvée pour les tarifs spéciaux ne pointe pas 
                    # sur la bonne liste de prix : il faut donc recréer un tarif spécial sur cette liste
                    if base_special.name[-4:] != tarif_general_choice:
                        not_same_pricelist = True

## Cas standard (modification des paramètres du partenaire)

            # On récupère la liste de prix correspondant aux paramètres du partenaire 
            # si aucune liste de prix spéciale n'existe OU si la liste spéciale trouvée 
            # ne correspond plus à la liste choisie dans le formulaire
            if not pricelist_ids or not_same_pricelist:
                pricelist_ids = pricelist_obj.search(
                        cr, uid, [
                                    ('tarif_choice', '=', tarif_choice or 'blanche'),
                                    ('promo_choice', '=', promo_choice or 'non'),
                                    ('mea_choice', '=', mea_choice or 'non'),
                                    ('name', 'ilike', base.name[-4:] or tarif_general_choice or 'NU01')
                                ], context=context)
## Cas par défaut

            # Si on a toujours pas de liste de prix, on applique par défaut celle du tarif de base choisi
            if not pricelist_ids:
                pricelist_ids = pricelist_obj.search(cr, uid, [('name', 'ilike', tarif_general_choice)], context=context)
            
            pricelist_record = pricelist_obj.browse(cr, uid, pricelist_ids[0],context=context)
            
            # Rajout d'un context qui permet de différencier d'où provient l'écriture
            # Si is_tarif_speciaux == True alors c'est lors de la création d'un tarif spécial
            # qu'on écrit une liste de prix
            if context:
                context['is_tarif_speciaux'] = False
            vals.update({'property_product_pricelist':pricelist_record.id})
            
        return super(iller_partner, self).write(cr, uid, ids, vals, context=context)

    def name_search(self, cr, uid, name, args=None, operator='ilike', context=None, limit=80):
        if not args:
            args=[]
        args += [('Active', '=', True)]
        if not context:
            context={}
        if name:
            ids = self.search(cr, uid, [('ref', operator, name)] + args, limit=limit, context=context)
            if not ids:
                ids = self.search(cr, uid, [('name', operator, name)] + args, limit=limit, context=context)
        else:
            ids = self.search(cr, uid, args, limit=limit, context=context)
        return self.name_get(cr, uid, ids, context)


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
            elif today.year % 4 == 0:
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
        #'tele_user_id': fields.many2one('res.users', string='Télé-vendeuse'),
        'tele_user_id': fields.char(
            size=64,
            string='Télé-vendeur',
        ),

        ## Autres champs
        'commentaire_prep': fields.text(string='Commentaire Préparation'),
        'commentaire_livraison': fields.text(string='Commentaire Livraison'),
        'depose_ok': fields.boolean(string='Dépose possible ?'),

        ## Client bloqué -- non nécessaire. Le champ active suffit
        #'bloque': fields.boolean(string='Bloqué ?', help='Si la case est cochée, le partenaire \
        #                        n\'apparaitra plus dans les recherches sur les bon de commande'),
        'ref': fields.char('Code', size=64, required=True),

        'tarif_general_choice': fields.selection([('nu01', 'NU01'), ('nu02', 'NU02'), ('nu03', 'NU03'), ('nu04', 'NU04')], string=u'Tarif de base'),
        'prix_noel_choice': fields.selection([('oui', 'Oui'), ('non', 'Non')], string=u'Prix noël'),
        'tarif_special_choice': fields.selection([('oui', 'Oui'), ('non', 'Non')], string='Tarif spécial'),
        'mea_choice': fields.selection([('oui', 'Oui'), ('non', 'Non')], string='Mise en avant'),
        'promo_choice': fields.selection([('oui', 'Oui'), ('non', 'Non')], string='Promo'),
        'tarif_choice': fields.selection([('blanche', 'Blanche'), ('jaune', 'Jaune')], string='Tarification'),
        'no_frais_de_port': fields.boolean(string='Pas de frais de port'),
    }

    _defaults = {
        'type_ristourne': lambda *a: 'a',
#        'bloque': lambda *a: False,
        'reglement': lambda *a: 'virement',
        'facturation_bl': lambda *a: 'm',
        'lang': lambda *a: 'fr_FR',
        'tarif_general_choice': lambda *a: 'nu01',
        'prix_noel_choice': lambda *a: 'oui',
        'tarif_special_choice': lambda *a: 'non',
        'mea_choice': lambda *a: 'oui',
        'promo_choice': lambda *a: 'oui',
        'tarif_choice': lambda *a: 'blanche',
    }


    def _verif_rib(self, cr, uid, ids, context={}):
        '''
            On vérifie qu'un RIB existe pour le partenaire
        '''
        if isinstance(ids, (int, long)):
            ids = [ids]

        if not ids:
            return True

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

    _sql_constraints = [
        ('code_saler_key', 'UNIQUE (code_saler)', _('Ce code vendeur a déjà été attribué !'))
    ]

    _order = 'code_saler'

    def name_get(self, cr, uid, ids, context={}):
        """
        Ajoute le code vendeur devant le nom du représentant
        """
        res = []
        for r in self.read(cr, uid, ids, ['name', 'code_saler']):
            res.append((r['id'], '%s - %s' % (r['code_saler'], r['name'])))
        return res

res_users()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

