#!/usr/bin/env python
# -*- encoding: utf-8 -*-
###########################################################################
#    This program is free software: you can redistribute it and/or modify #
#    it under the terms of the GNU General Public License as published by #
#    the Free Software Foundation, either version 3 of the License, or    #
#    (at your option) any later version.                                  #
#                                                                         #
#    This program is distributed in the hope that it will be useful,      #
#    but WITHOUT ANY WARRANTY; without even the implied warranty of       #
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the        #
#    GNU General Public License for more details.                         #
#                                                                         #
#    You should have received a copy of the GNU General Public License    #
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.#
#                                                                         #
#    Author : Julien BECOULET                                             #
#    Company: TeMPO Consulting <http://www.tempo-consulting.fr>           #
#    Version: 1.0                                                         #
#    Date: 02/09/2013 17:07                                               #
#    Description: This script is a script which allow to import data into #
#                 OpenERP database with XML-RPC. This script tests the    #
#                 behaviour of prices according to partner's parameters   #
###########################################################################

from optparse import OptionParser, OptionValueError
import sys
import time

from erp_proxy import ERPProxy
import xmlrpclib
from mx import DateTime as mx

"""
########### Données ###########
###############################
"""
# Partenaire
partner_test = ['029005']
# Produits dans la promo : Prix blanc = prix depart * coeff blanc et Prix jaune = prix blanc * 1.03, prix depart = prix achat * coeff depart
product_promo_test = [
    # A : Promo
    {'default_code':'010800', 'prix_achat':12.10, 'prix_blanche':18.39, 'prix_jaune':18.9417, 'prix_depart':15.97, 'coeff_depart':1.32, 'coeff_blanc':1.52,},
    # E : Promo / Mea
    {'default_code':'020101', 'prix_achat':8.30, 'prix_blanche':13.36, 'prix_jaune':13.7608, 'prix_depart':11.62, 'coeff_depart':1.40, 'coeff_blanc':1.61,},
    # F : Promo / Mea / Ts
    {'default_code':'030000', 'prix_achat':7.40, 'prix_blanche':12.06, 'prix_jaune':12.4218, 'prix_depart':10.51, 'coeff_depart':1.42, 'coeff_blanc':1.63,},
    # G : Promo / Ts
    {'default_code':'265000', 'prix_achat':1.17, 'prix_blanche':1.80, 'prix_jaune':1.854, 'prix_depart':1.59, 'coeff_depart':1.36, 'coeff_blanc':1.538462,},
]
# Produits dans la mea : Prix blanc / jaune libres
product_mea_test = [
    # B : Mea
    {'default_code':'040100', 'prix_achat':8.20, 'prix_blanche':80.05, 'prix_jaune':90.15, 'prix_depart':11.81, 'coeff_depart':1.44, 'coeff_blanc':1.65,},
    # E : Mea / Promo
    {'default_code':'020101', 'prix_achat':8.30, 'prix_blanche':81.05, 'prix_jaune':91.15, 'prix_depart':11.62, 'coeff_depart':1.40, 'coeff_blanc':1.61,},
    # F : Mea / Promo / Ts
    {'default_code':'030000', 'prix_achat':7.40, 'prix_blanche':82.05, 'prix_jaune':92.15, 'prix_depart':10.51, 'coeff_depart':1.42, 'coeff_blanc':1.63,},
    # H : Mea / Ts
    {'default_code':'270000', 'prix_achat':4.14, 'prix_blanche':83.05, 'prix_jaune':93.15, 'prix_depart':5.55, 'coeff_depart':1.34, 'coeff_blanc':1.49,},
]
# Produits dans les tarifs spéciaux : Prix libres
product_ts_test = [
    # C : Ts
    (0, 0, {'default_code':'150200', 'prix_special': 150.32,}),
    # F : Ts / Mea / Promo
    (0, 0, {'default_code':'030000', 'prix_special': 151.32,}),
    # G : Ts / Promo
    (0, 0, {'default_code':'265000', 'prix_special': 152.32,}),
    # H : Ts / Mea
    (0, 0, {'default_code':'270000', 'prix_special': 153.32,}),
]
# Produits dans aucun tarif
product_tg_test= [
    # D : Tg
    {'default_code':'012100', 'prix_achat':4.90, 'prix_blanche':7.69, 'prix_jaune':7.9207, 'prix_depart':6.76, 'coeff_depart':1.38, 'coeff_blanc':1.57, 'prix_nu01':7.68, 'prix_nu02':7.86, 'prix_nu03':7.68, 'prix_nu04':8.05},
]
# Prix des produits en tarifs general
product_tg_list= [
    # D : Tg
    {'default_code':'012100', 'prix_nu01':7.68, 'prix_nu02':7.86, 'prix_nu03':7.68, 'prix_nu04':8.05},
    # A : Promo
    {'default_code':'010800', 'prix_nu01':18.15, 'prix_nu02':18.57, 'prix_nu03':18.15, 'prix_nu04':19.01},
    # B : Mea
    {'default_code':'040100', 'prix_nu01':13.42, 'prix_nu02':13.73, 'prix_nu03':13.42, 'prix_nu04':14.06},
    # C : Ts
    {'default_code':'150200', 'prix_nu01':6.53, 'prix_nu02':6.69, 'prix_nu03':6.53, 'prix_nu04':6.85},
    # E : Promo / Mea
    {'default_code':'020101', 'prix_nu01':13.20, 'prix_nu02':13.51, 'prix_nu03':13.20, 'prix_nu04':13.83},
    # F : Promo / Mea / Ts
    {'default_code':'030000', 'prix_nu01':11.94, 'prix_nu02':12.22, 'prix_nu03':11.94, 'prix_nu04':12.51},
    # G : Promo / Ts
    {'default_code':'265000', 'prix_nu01':1.85, 'prix_nu02':1.85, 'prix_nu03':1.85, 'prix_nu04':1.89},
    # H : Ts / Mea
    {'default_code':'270000', 'prix_nu01':6.45, 'prix_nu02':6.61, 'prix_nu03':6.94, 'prix_nu04':6.94},
]
# Produits à insérer dans le devis
product_devis_test = [
    {'default_code':'010800', 'product_uom':2, 'price_unit':100, 'product_uom_qty':1.0},
    {'default_code':'040100', 'product_uom':2, 'price_unit':100, 'product_uom_qty':1.0},
    {'default_code':'150200', 'product_uom':2, 'price_unit':100, 'product_uom_qty':1.0},
    {'default_code':'012100', 'product_uom':2, 'price_unit':100, 'product_uom_qty':1.0},
    {'default_code':'020101', 'product_uom':2, 'price_unit':100, 'product_uom_qty':1.0},
    {'default_code':'030000', 'product_uom':2, 'price_unit':100, 'product_uom_qty':1.0},
    {'default_code':'265000', 'product_uom':2, 'price_unit':100, 'product_uom_qty':1.0},
    {'default_code':'270000', 'product_uom':2, 'price_unit':100, 'product_uom_qty':1.0},
]

"""
########### Cas de figure ########### 
#####################################
"""

param_partner_test = [
# 1 -> Tarif spécial non, mea non, promo non
    {'tarif_special':'non', 'mea':'non', 'promo':'non'},
# 2 -> Tarif spécial non, mea non, promo oui
    {'tarif_special':'non', 'mea':'non', 'promo':'oui'},
# 3 -> Tarif spécial non, mea oui, promo oui
    {'tarif_special':'non', 'mea':'oui', 'promo':'oui'},
# 4 -> Tarif spécial non, mea oui, promo non
    {'tarif_special':'non', 'mea':'oui', 'promo':'non'},
# 5 -> Tarif spécial oui, mea oui, promo oui
    {'tarif_special':'oui', 'mea':'oui', 'promo':'oui'},
# 6 -> Tarif spécial oui, mea non, promo non
    {'tarif_special':'oui', 'mea':'non', 'promo':'non'},
# 7 -> Tarif spécial oui, mea oui, promo non
    {'tarif_special':'oui', 'mea':'oui', 'promo':'non'},
# 8 -> Tarif spécial oui, mea non, promo oui
    {'tarif_special':'oui', 'mea':'non', 'promo':'oui'},
]

# Listes de prix de base
pricelist_base_test = ['nu01', 'nu02', 'nu03', 'nu04']

# Type de prix
pricetype_test = ['blanche', 'jaune']

"""
########### Objet de test ########### 
#####################################
"""

class DataTest:

    """
        Constructeur de l'objet contenant les différents cas de figure
        Initialise les attributs et initialise le partenaire
    """

    def __init__(self, tarif_special, mea, promo, pricelist_base, \
                    pricetype, partners, product_promo, product_mea, \
                    product_ts, product_tg, proxy):

        # Semaine en cours
        self.monday = str(mx.now() + mx.RelativeDateTime(weekday=(mx.Monday,0)))[:10]
        self.friday = str(mx.now() + mx.RelativeDateTime(weekday=(mx.Friday,0)))[:10]

        # Données d'entrée (ids)
        self.product_promo_ids = product_promo
        self.product_mea_ids = product_mea
        self.product_ts_ids = product_ts
        self.product_tg_ids = product_tg

        # Données cas de figure
        self.tarif_special = tarif_special
        self.mea = mea
        self.promo = promo
        self.pricelist_base = pricelist_base
        self.pricetype = pricetype

        # Listes de résultat
        self.errors = []
        self.ok = []
        self.list_devis = []

        self.proxy = proxy

        self.partners = partners

    """
    ########### Méthodes de vérification ########### 
    ################################################
    """

    """
        Fonction permettant de vérifier les pricelist correspondant aux paramètres
        du/des partenaires. Permet de s'assurer que la liste de prix correspond bien
        aux paramètres du partenaire.
    """

    def _check_pricelist_partner(self):
        for partner in self.partners:
            try:
                # On verifie que les parametre du cas de figure correspondent bien
                # aux parametres de la liste de prix
                pricelist = self.proxy.read('product.pricelist',[partner['property_product_pricelist'][0]],
                                    ['tarif_choice', 'mea_choice', 'promo_choice', 'tarif_special_choice', 'name'])
                # On verifie le type de prix 
                if pricelist[0]['tarif_choice'] and pricelist[0]['tarif_choice'] != partner['tarif_choice']:
                    error = 'Le type de prix est different - Partenaire : %s, Liste de prix %s : %s' % (partner['tarif_choice'], pricelist[0]['tarif_choice'], pricelist[0]['name'])
                    print error
                    self.errors.append(error)
                    return False
                # On verifie le parametre de mea
                if pricelist[0]['mea_choice'] and pricelist[0]['mea_choice'] != partner['mea_choice']:
                    error = 'Le parametre de mea est different - Partenaire : %s, Liste de prix %s : %s' % (partner['mea_choice'], pricelist[0]['mea_choice'], pricelist[0]['name'])
                    print error
                    self.errors.append(error)
                    return False
                # On verifie le parametre de promo
                if pricelist[0]['promo_choice'] and pricelist[0]['promo_choice'] != partner['promo_choice']:
                    error = 'Le parametre de promo est different - Partenaire : %s, Liste de prix %s : %s' % (partner['promo_choice'], pricelist[0]['promo_choice'], pricelist[0]['name'])
                    print error
                    self.errors.append(error)
                    return False
                # On verifie le parametre des tarifs speciaux
                if pricelist[0]['tarif_special_choice'] and pricelist[0]['tarif_special_choice'] == 'oui' and pricelist[0]['tarif_special_choice'] != partner['tarif_special_choice']:
                    error = 'Le parametre du tarif special est different - Partenaire : %s, Liste de prix %s : %s' % (partner['tarif_special_choice'], pricelist[0]['tarif_special_choice'], pricelist[0]['name'])
                    print error
                    self.errors.append(error)
                    return False
                # Verifier le tarif de base ?
            except xmlrpclib.Fault, e:
                raise
                error = 'Erreur lors de la verification de la liste de prix - Cas : ts : %s; mea : %s; promo : %s; base :%s; type : %s; du partenaire %s : %s' \
                     % (self.tarif_special, self.mea, self.promo, self.pricelist_base, \
                     self.pricetype, partner['name'], e.faultString)
                print error
                self.errors.append(error)
                return False
            except Exception, e:
                raise
                error = 'Erreur lors de la verification de la liste de prix - Cas : ts : %s; mea : %s; promo : %s; base :%s; type : %s; du partenaire %s : %s' \
                     % (self.tarif_special, self.mea, self.promo, self.pricelist_base, \
                     self.pricetype, partner['name'], str(e))
                print error
                self.errors.append(error)
                return False

            self.ok.append('Verification de la liste de prix - Cas : ts : %s; mea : %s; promo : %s; base :%s; type : %s; du partenaire %s : ok' \
                % (self.tarif_special, self.mea, self.promo, self.pricelist_base, \
                 self.pricetype, partner['name']))
        return True


    def _check_parameters_order(self):
        for devis in self.list_devis:
            try:
                order = self.proxy.read('sale.order', devis['order_id'], ['partner_id', 'pricelist_id', 'name'])
                # Vérification de la liste de prix 
                if order['pricelist_id'][0] != devis['pricelist_id'][0]:
                    error = 'La liste de prix %s du devis %s et %s du partenaire %s ne correspondent pas - Cas : ts : %s; mea : %s; promo : %s; base :%s; type : %s;' \
                         % ( order['pricelist_id'], order['name'], devis['pricelist_id'], \
                         devis['partner_name'], self.tarif_special, self.mea, self.promo, self.pricelist_base, \
                         self.pricetype)
                    print error
                    self.errors.append(error)
                    return False

            except xmlrpclib.Fault, e:
                raise
                error = 'Erreur lors de la verification du devis - Cas : ts : %s; mea : %s; promo : %s; base :%s; type : %s; - %s' \
                     % ( self.tarif_special, self.mea, self.promo, self.pricelist_base, \
                     self.pricetype, e.faultString)
                print error
                self.errors.append(error)
                return False
            except Exception, e:
                error = 'Erreur lors de la verification du devis - Cas : ts : %s; mea : %s; promo : %s; base :%s; type : %s; - %s' \
                     % ( self.tarif_special, self.mea, self.promo, self.pricelist_base, \
                    self.pricetype, str(e))
                print error
                self.errors.append(error)
                return False

            self.ok.append('Verification du devis: %s" - Cas : ts : %s; mea : %s; promo : %s; base :%s; type : %s; : ok' \
                 % (order['name'],self.tarif_special, self.mea, self.promo, self.pricelist_base, \
                 self.pricetype))

        return True

    def _check_tarif_priority(self, product_order, price_order):
        try:
            # Cas prioritaire : tarif special = oui et le produit est présent dans la liste
            if self.tarif_special == 'oui' and [product_order[0]] in self.product_ts_ids:
                # Doit avoir le prix special de la liste
                for product_ts in product_ts_test:
                    if product_ts[2]['product_id'] != product_order[0]:
                        continue
                    else:
                        if product_ts[2]['prix_special'] == price_order:
                            #OK
                            self.ok.append('Produit %s - prix devis %s - prix attendu %s - Cas : ts : %s; mea : %s; promo : %s; base :%s; type : %s; : ok' \
                                 % (product_order[1],price_order, product_ts[2]['prix_special'], self.tarif_special, self.mea, self.promo, self.pricelist_base, \
                                 self.pricetype))
                        else:
                            #Erreur
                            error = 'TS - Erreur lors de la vérification des prix de produits %s - Cas : ts : %s; mea : %s; promo : %s; base :%s; type : %s;' \
                                 % (product_order[1], self.tarif_special, self.mea, self.promo, self.pricelist_base, \
                                 self.pricetype)
                            print error
                            self.errors.append(error)
                            return False
            
            else:
                if self.mea == 'oui' and [product_order[0]] in self.product_mea_ids:
                    for product_mea in product_mea_test:
                        if product_mea['id'] != product_order[0]:
                            continue
                        else:
                            if self.pricetype == 'blanche' and product_mea['prix_blanche'] == price_order:
                                #OK
                                self.ok.append('Produit %s - prix devis %s - prix attendu %s - Cas : ts : %s; mea : %s; promo : %s; base :%s; type : %s; : ok' \
                                     % (product_order[1],price_order, product_mea['prix_blanche'], self.tarif_special, self.mea, self.promo, self.pricelist_base, \
                                     self.pricetype))
                            elif self.pricetype == 'jaune' and product_mea['prix_jaune'] == price_order:
                                #OK
                                self.ok.append('Produit %s - prix devis %s - prix attendu %s - Cas : ts : %s; mea : %s; promo : %s; base :%s; type : %s; : ok' \
                                     % (product_order[1],price_order, product_mea['prix_jaune'], self.tarif_special, self.mea, self.promo, self.pricelist_base, \
                                     self.pricetype))
                            else:
                                error = 'MEA TYPE - Erreur lors de la vérification des prix de produits %s - Cas : ts : %s; mea : %s; promo : %s; base :%s; type : %s;' \
                                     % (product_order[1], self.tarif_special, self.mea, self.promo, self.pricelist_base, \
                                     self.pricetype)
                                print error
                                self.errors.append(error)
                                return False
                else:
                    if self.promo == 'oui' and [product_order[0]] in self.product_promo_ids:
                        for product_promo in product_promo_test:
                            if product_promo['id'] != product_order[0]:
                                continue
                            else:
                                if self.pricetype == 'blanche' and product_promo['prix_blanche'] == price_order:
                                    #OK
                                    self.ok.append('Produit %s - prix devis %s - prix attendu %s - Cas : ts : %s; mea : %s; promo : %s; base :%s; type : %s; : ok' \
                                         % (product_order[1],price_order, product_promo['prix_blanche'], self.tarif_special, self.mea, self.promo, self.pricelist_base, \
                                         self.pricetype))
                                elif self.pricetype == 'jaune' and product_promo['prix_jaune'] == price_order:
                                    #OK
                                    self.ok.append('Produit %s - prix devis %s - prix attendu %s - Cas : ts : %s; mea : %s; promo : %s; base :%s; type : %s; : ok' \
                                         % (product_order[1],price_order, product_promo['prix_jaune'], self.tarif_special, self.mea, self.promo, self.pricelist_base, \
                                         self.pricetype))
                                else:
                                    #Erreur
                                    error = 'PROMO TYPE - Erreur lors de la vérification des prix de produits %s - Cas : ts : %s; mea : %s; promo : %s; base :%s; type : %s;' \
                                         % (product_order[1], self.tarif_special, self.mea, self.promo, self.pricelist_base, \
                                         self.pricetype)
                                    print error
                                    self.errors.append(error)
                                    return False
                    else:
                        for product_tg in product_tg_list:
                            if product_tg['id'] != product_order[0]:
                                continue
                            else:
                                if self.pricelist_base == 'nu01' and product_tg['prix_nu01'] == price_order:
                                    #OK
                                    self.ok.append('Produit %s - prix devis %s - prix attendu %s - Cas : ts : %s; mea : %s; promo : %s; base :%s; type : %s; : ok' \
                                         % (product_order[1],price_order, product_tg['prix_nu01'], self.tarif_special, self.mea, self.promo, self.pricelist_base, \
                                         self.pricetype))
                                elif self.pricelist_base == 'nu02' and product_tg['prix_nu02'] == price_order:
                                    #OK
                                    self.ok.append('Produit %s - prix devis %s - prix attendu %s - Cas : ts : %s; mea : %s; promo : %s; base :%s; type : %s; : ok' \
                                         % (product_order[1],price_order, product_tg['prix_nu02'], self.tarif_special, self.mea, self.promo, self.pricelist_base, \
                                         self.pricetype))
                                elif self.pricelist_base == 'nu03' and product_tg['prix_nu03'] == price_order:
                                    #OK
                                    self.ok.append('Produit %s - prix devis %s - prix attendu %s - Cas : ts : %s; mea : %s; promo : %s; base :%s; type : %s; : ok' \
                                         % (product_order[1],price_order, product_tg['prix_nu03'], self.tarif_special, self.mea, self.promo, self.pricelist_base, \
                                         self.pricetype))
                                elif self.pricelist_base == 'nu04' and product_tg['prix_nu04'] == price_order:
                                    #OK
                                    self.ok.append('Produit %s - prix devis %s - prix attendu %s - Cas : ts : %s; mea : %s; promo : %s; base :%s; type : %s; : ok' \
                                         % (product_order[1],price_order, product_tg['prix_nu04'], self.tarif_special, self.mea, self.promo, self.pricelist_base, \
                                         self.pricetype))
                                else:
                                    #Erreur
                                    error = 'TG TYPE -Erreur lors de la vérification des prix de produits %s - Cas : ts : %s; mea : %s; promo : %s; base :%s; type : %s;' \
                                         % (product_order[1], self.tarif_special, self.mea, self.promo, self.pricelist_base, \
                                         self.pricetype)
                                    print error
                                    self.errors.append(error)
                                    return False

        except xmlrpclib.Fault, e:
            #~ raise
            error = 'Erreur lors de la vérification des prix de produits - Cas : ts : %s; mea : %s; promo : %s; base :%s; type : %s;' \
                 % (product_order[1], self.tarif_special, self.mea, self.promo, self.pricelist_base, \
                 self.pricetype)
            print error
            self.errors.append(error)
            return False

        except Exception, e:
            #~ raise
            error = 'Erreur lors de la vérification des prix de produits %s - Cas : ts : %s; mea : %s; promo : %s; base :%s; type : %s;' \
                 % (product_order[1], self.tarif_special, self.mea, self.promo, self.pricelist_base, \
                 self.pricetype)
            print error
            self.errors.append(error)
            return False

        return True


    def _check_price_product_order(self):
        for devis in self.list_devis:
            try:
                ## Pour chaque devis, on regarde si tous les produits sont présents
                order = self.proxy.read('sale.order', devis['order_id'], ['order_line', 'name'])
                list_product_order = []
                for line_id in order['order_line']:
                    order_line = self.proxy.read('sale.order.line', line_id, ['product_id', 'price_unit'])
                    list_product_order.append(
                        {
                            'product_id':order_line['product_id'][0],
                            'price_unit':order_line['price_unit'],
                        })
                    # On check si la ligne possède un prix correspondant aux paramètres et à la priorité des tarifs
                    if not self._check_tarif_priority(order_line['product_id'], order_line['price_unit']):
                        error = 'Le produit %s ne possède pas le bon prix %s - Cas : ts : %s; mea : %s; promo : %s; base :%s; type : %s;' \
                             % (order_line['product_id'],order_line['price_unit'], self.tarif_special, self.mea, self.promo, self.pricelist_base, \
                             self.pricetype)
                        print error
                        self.errors.append(error)
                        return False

                list_id_product = [x['product_id'] for x in list_product_order]
                for product_promo in product_promo_test:
                    if product_promo['id'] not in list_id_product:
                        error = 'Le produit %s de promo n\'est pas present dans le devis %s - Cas : ts : %s; mea : %s; promo : %s; base :%s; type : %s;' \
                             % (product_promo['id'], order['name'], self.tarif_special, self.mea, self.promo, self.pricelist_base, \
                             self.pricetype)
                        print error
                        self.errors.append(error)

                for product_mea in product_mea_test:
                    if product_mea['id'] not in list_id_product:
                        error = 'Le produit %s de mea n\'est pas present dans le devis %s - Cas : ts : %s; mea : %s; promo : %s; base :%s; type : %s;' \
                             % (product_mea['id'], order['name'], self.tarif_special, self.mea, self.promo, self.pricelist_base, \
                             self.pricetype)
                        print error
                        self.errors.append(error)

                for product_ts in product_ts_test:
                    if product_ts[2]['product_id'] not in list_id_product:
                        error = 'Le produit %s de tarif special n\'est pas present dans le devis %s - Cas : ts : %s; mea : %s; promo : %s; base :%s; type : %s;' \
                             % (product_ts[2]['product_id'], order['name'], self.tarif_special, self.mea, self.promo, self.pricelist_base, \
                             self.pricetype)
                        print error
                        self.errors.append(error)

                for product_tg in product_tg_test:
                    if product_tg['id'] not in list_id_product:
                        error = 'Le produit %s de tarif general n\'est pas present dans le devis %s - Cas : ts : %s; mea : %s; promo : %s; base :%s; type : %s;' \
                             % (product_tg['id'], order['name'], self.tarif_special, self.mea, self.promo, self.pricelist_base, \
                             self.pricetype)
                        print error
                        self.errors.append(error)
                
            except xmlrpclib.Fault, e:
                raise
                error = 'Erreur lors de la verification des prix des produits - Cas : ts : %s; mea : %s; promo : %s; base :%s; type : %s; - %s' \
                     % ( self.tarif_special, self.mea, self.promo, self.pricelist_base, \
                     self.pricetype, e.faultString)
                print error
                self.errors.append(error)
                return False
            except Exception, e:
                error = 'Erreur lors de la verification des prix des produits - Cas : ts : %s; mea : %s; promo : %s; base :%s; type : %s; - %s' \
                     % ( self.tarif_special, self.mea, self.promo, self.pricelist_base, \
                    self.pricetype, str(e))
                print error
                self.errors.append(error)
                return False

            self.ok.append('Verification des prix des produits: %s" - Cas : ts : %s; mea : %s; promo : %s; base :%s; type : %s; : ok' \
                 % (order['name'],self.tarif_special, self.mea, self.promo, self.pricelist_base, \
                 self.pricetype))

        return True

    """
    ########### Méthodes de d'affichage ############ 
    ################################################
    """


    """
        Fonction permettant de d'afficher les erreurs et les succès stockés
        dans les dictionnaires de cas de figure en cours
    """

    def _state(self, message):
        print '############## %s ##############' % (message,)

        attr_ok = ['32', '1']
        for ok_val in self.ok:
            print '\x1b[%sm%s\x1b[0m' % (';'.join(attr_ok), ok_val)

        attr_err = ['31', '1']
        for err_val in self.errors:
            print '\x1b[%sm%s\x1b[0m' % (';'.join(attr_err), err_val)

        print '########################################################\n\n'
        return True


    """
    ########### Méthodes de création ############### 
    ################################################
    """

    """
        Fonction permettant de créer une promo sur la semaine en cours
        Comprend l'ajout des produits définis en variable globale
    """

    def create_promo(self):
        try:
            monday = self.monday 
            friday = self.friday

            #On construit le nom de cette promo par rapport a cette semaine
            nom_promo = 'promo %s - %s' % (monday, friday)

            data_promo = {
                'name':nom_promo,
                'start_date':str(monday),
                'end_date':str(friday),
            }
            # On la créé
            promo_id = self.proxy.create('product.pricelist.promo', data_promo)

            for product_promo_id in self.product_promo_ids:
                data_product_promo = {
                    'product_id':product_promo_id[0],
                    'promo_id':promo_id,
                }
                self.proxy.create('product.pricelist.promo.in', data_product_promo)
                self.ok.append('Creation de produit promo - Cas : ts : %s; mea : %s; promo : %s; base :%s; type : %s; : ok' \
                    % (self.tarif_special, self.mea, self.promo, self.pricelist_base, \
                     self.pricetype))

            # Validation de la promo
            self.proxy.call_method('product.pricelist.promo', '_create_promo', [promo_id])
            self.ok.append('Validation de la promo %s - Cas : ts : %s; mea : %s; promo : %s; base :%s; type : %s; : ok' \
                % (nom_promo, self.tarif_special, self.mea, self.promo, self.pricelist_base, \
                 self.pricetype))
        except xmlrpclib.Fault, e:
            raise
            error = 'Erreur lors de la creation de la promo %s - Cas : ts : %s; mea : %s; promo : %s; base :%s; type : %s; : %s' \
                 % (nom_promo, self.tarif_special, self.mea, self.promo, self.pricelist_base, \
                 self.pricetype,e.faultString)
            print error
            self.errors.append(error)
            return False
        except Exception, e:
            raise
            error = 'Erreur lors de la creation de la promo %s - Cas : ts : %s; mea : %s; promo : %s; base :%s; type : %s;' \
                 % (nom_promo, self.tarif_special, self.mea, self.promo, self.pricelist_base, \
                 self.pricetype, str(e))
            print error
            self.errors.append(error)
            return False

        self.ok.append('Creation de la promo %s - Cas : ts : %s; mea : %s; promo : %s; base :%s; type : %s; : ok' \
            % (nom_promo, self.tarif_special, self.mea, self.promo, self.pricelist_base, \
             self.pricetype))
        return True

    """
        Fonction permettant de créer une mea sur la semaine en cours
        Comprend l'ajout des produits définis en variable globale
    """

    def create_mea(self):
        try:
            monday = self.monday 
            friday = self.friday

            #On construit le nom de cette mea par rapport a cette semaine
            nom_mea = 'mea %s - %s' % (monday, friday)

            data_mea = {
                'name':nom_mea,
                'start_date':str(monday),
                'end_date':str(friday),
            }
            # On la créé
            mea_id = self.proxy.create('product.pricelist.mea', data_mea)
            for product_mea_id in product_mea_test:
                data_product_mea = {
                    'product_id':product_mea_id['id'],
                    'promo_id':mea_id,
                    'new_prix_blanche':product_mea_id['prix_blanche'],
                    'new_prix_jaune':product_mea_id['prix_jaune'],
                }
                self.proxy.create('product.pricelist.mea.in', data_product_mea)
                self.ok.append('Creation de produit mea - Cas : ts : %s; mea : %s; promo : %s; base :%s; type : %s; : ok' \
                    % (self.tarif_special, self.mea, self.promo, self.pricelist_base, \
                     self.pricetype))
            # Validation de la mea
            self.proxy.call_method('product.pricelist.mea', '_create_mea', [mea_id])
            self.ok.append('Validation de la mea %s - Cas : ts : %s; mea : %s; promo : %s; base :%s; type : %s; : ok' \
                % (nom_mea, self.tarif_special, self.mea, self.promo, self.pricelist_base, \
                 self.pricetype))
        except xmlrpclib.Fault, e:
            raise
            error = 'Erreur lors de la creation de la mea %s - Cas : ts : %s; mea : %s; promo : %s; base :%s; type : %s; -- %s' \
                 % (nom_mea, self.tarif_special, self.mea, self.promo, self.pricelist_base, \
                 self.pricetype, e.faultString)
            print error
            self.errors.append(error)
            return False
        except Exception, e:
            raise
            error = 'Erreur lors de la creation de la mea %s - Cas : ts : %s; mea : %s; promo : %s; base :%s; type : %s; -- %s' \
                 % (nom_mea, self.tarif_special, self.mea, self.promo, self.pricelist_base, \
                 self.pricetype, str(e))
            print error
            self.errors.append(error)
            return False

        self.ok.append('Creation de la mea %s - Cas : ts : %s; mea : %s; promo : %s; base :%s; type : %s; : ok' \
            % (nom_mea, self.tarif_special, self.mea, self.promo, self.pricelist_base, \
             self.pricetype))
        return True

    def create_tarspe(self):

        for partner in self.partners:
            try:
                # On crée d'abord le tarif spécial
                
                monday = self.monday
                friday = self.friday

                nom_tarif = 'Tarif client %s Periode %s -- %s' % (partner['name'], monday, friday)
                code_cli = partner['name'],

                tarif_id = self.proxy.search('product.tarifs.speciaux', [
                                                    ('client', '=', partner['id']),
                                                    ('start_date', '=', monday),
                                                    ('end_date', '=', friday),
                                                ])
                if tarif_id:
                    self.proxy.unlink('product.tarifs.speciaux', tarif_id)
                data_tarif = {
                    'name':nom_tarif,
                    'client':partner['id'],
                    'start_date':monday,
                    'end_date':friday,
                }
                wizard_id = self.proxy.create_wizard('pricelist.configure.tarif.special.client')
                data = {}
                data['report_type']= 'pdf'
                data['model']= 'ir.ui.menu'
                data['form']= {
                    'end_date': friday,
                    'start_date': monday,
                    'title': nom_tarif,
                    'client': partner['id'], 
                    'tarif_initial': '', 
                    'products': product_ts_test, 
                }
                self.proxy.appel_wizard('pricelist.configure.tarif.special.client', wizard_id, data, 'create', {'lang': 'fr_FR'})

            except xmlrpclib.Fault, e:
                raise
                error = 'Erreur lors de la creation du tarif special %s - Cas : ts : %s; mea : %s; promo : %s; base :%s; type : %s; -- %s' \
                     % (nom_tarif, self.tarif_special, self.mea, self.promo, self.pricelist_base, \
                     self.pricetype, e.faultString)
                print error
                self.errors.append(error)
                return False
            except Exception,e:
                raise
                error = 'Erreur lors de la creation de la mea %s - Cas : ts : %s; mea : %s; promo : %s; base :%s; type : %s; -- %s' \
                     % (nom_tarif, self.tarif_special, self.mea, self.promo, self.pricelist_base, \
                     self.pricetype, str(e))
                print error
                self.errors.append(error)
                return False

            self.ok.append('Creation du tarif special %s - Cas : ts : %s; mea : %s; promo : %s; base :%s; type : %s; pour le partenaire %s : ok' \
                % (nom_tarif, self.tarif_special, self.mea, self.promo, self.pricelist_base, \
                 self.pricetype, partner['name']))

        return True

    def create_devis(self):
        for partner in self.partners:
            try:
                part = self.proxy.read('res.partner', partner['id'], [
                                            'property_product_pricelist',
                                        ])

                data_devis = {
                    'partner_id': partner['id'],
                    'partner_order_id': partner['id'],
                    'partner_invoice_id': partner['id'],
                    'partner_shipping_id': partner['id'],
                    'pricelist_id': part['property_product_pricelist'][0],
                    'tournee_id': partner['tournee1'][0],
                }
                order_id = self.proxy.create('sale.order', data_devis)
                self.list_devis.append({
                    'order_id':order_id,
                    'partner_id':partner['id'],
                    'pricelist_id':part['property_product_pricelist'],
                    'partner_name':partner['name']
                })
                for product_devis_line in product_devis_test:
                    product_devis_line.update({'order_id':order_id})
                    order_line_id = self.proxy.create('sale.order.line', product_devis_line)
                    product = self.proxy.call_method('sale.order.line','product_id_change',[order_line_id],
                        part['property_product_pricelist'][0],
                        product_devis_line['product_id'],
                        product_devis_line['product_uom_qty'],
                        product_devis_line['product_uom'],
                        0,False,'',
                        partner['id'],
                    )
                    self.proxy.write('sale.order.line', [order_line_id], product['value'])

            except xmlrpclib.Fault, e:
                #~ raise
                error = 'Erreur lors de la creation du devis - Cas : ts : %s; mea : %s; promo : %s; base :%s; type : %s; -- %s' \
                     % (self.tarif_special, self.mea, self.promo, self.pricelist_base, \
                     self.pricetype, e.faultString)
                print error
                self.errors.append(error)
                return False
            except Exception,e:
                #~ raise
                error = 'Erreur lors de la creation du devis - Cas : ts : %s; mea : %s; promo : %s; base :%s; type : %s; -- %s' \
                     % (self.tarif_special, self.mea, self.promo, self.pricelist_base, \
                     self.pricetype, str(e))
                print error
                self.errors.append(error)
                return False
        return True

    """
        Fonction permettant de définir les paramètres du partenaires dans
        openerp en fonction du cas de figure en cours
    """

    def set_params_partner(self):
        for partner in self.partners:
            try:
                self.proxy.write('res.partner', partner['id'], {
                                'promo_choice':self.promo,
                                'mea_choice':self.mea,
                                'tarif_choice':self.pricetype,
                                'tarif_special_choice':self.tarif_special,
                                'tarif_general_choice':self.pricelist_base,})

            except xmlrpclib.Fault, e:
                raise
                error = 'Erreur lors de la mise à jour des parametres - Cas : ts : %s; mea : %s; promo : %s; base :%s; type : %s; du partenaire %s : %s' \
                     % (self.tarif_special, self.mea, self.promo, self.pricelist_base, \
                     self.pricetype, partner['name'], e.faultString)
                print error
                self.errors.append(error)
                return False
            except Exception, e:
                raise
                error = 'Erreur lors de la mise à jour des parametres - Cas : ts : %s; mea : %s; promo : %s; base :%s; type : %s; du partenaire %s : %s' \
                     % (self.tarif_special, self.mea, self.promo, self.pricelist_base, \
                     self.pricetype, partner['name'], str(e))
                print error
                self.errors.append(error)
                return False

            self.ok.append('Maj des parametres - Cas : ts : %s; mea : %s; promo : %s; base :%s; type : %s; -- %s: ok' \
                % (self.tarif_special, self.mea, self.promo, self.pricelist_base, \
                 self.pricetype, partner['name']))

        return True


"""
    Fonction Main qui contient l'algorithme principal
"""


def main():
    usage = "usage: %prog -u user -p password -d database"
    version = "%prog 0.1"
    parser = OptionParser(usage=usage, version=version)
    parser.add_option("-u", "--user", dest="user", default='admin', help=u"Avec qui je me connecte ?")
    parser.add_option("-p", "--password", dest="password")
    parser.add_option("-d", "--database", dest="db", default=False)
    parser.add_option("-o", "--port", dest="port", default='10069')
    parser.add_option("-H", "--host", dest="host", default='localhost')

    options, args = parser.parse_args()
    if not options.password:
        parser.error("Mot de passe necessaire !")
    if not options.db:
        parser.error("Database necessaire !")

    proxy = ERPProxy(username=options.user, pwd=options.password, dbname=options.db, host=options.host, port=options.port)
    proxy.setup()

    ### Initialisation des données ###

    partner_ids = proxy.search('res.partner', [('ref', 'in', partner_test)]) 
    if not partner_ids:
        print 'Aucun partenaire ne correspond %s' % ([str(x) + ',' for x in partner_test], )

    product_promo_ids = []
    for code in product_promo_test:
        product_promo_id = proxy.search('product.product', [('default_code', '=', code['default_code'])])
        product_promo_ids.append(product_promo_id)
        code.update({'id':product_promo_id[0]})
    if not product_promo_ids:
        print 'Aucun produit promo ne correspond %s' % ([str(x) + ',' for x in product_promo_test], )

    product_mea_ids = []
    for code in product_mea_test:
        product_mea_id = proxy.search('product.product', [('default_code', '=', code['default_code'])])
        product_mea_ids.append(product_mea_id)
        code.update({'id':product_mea_id[0]})

    if not product_mea_ids:
        print 'Aucun produit mea ne correspond %s' % ([str(x) + ',' for x in product_mea_test], )

    product_ts_ids = []
    for code in product_ts_test:
        product_ts_id = proxy.search('product.product', [('default_code', '=', code[2]['default_code'])])
        product_ts_ids.append(product_ts_id)
        code[2].update({'product_id':product_ts_id[0]})
        del code[2]['default_code']
    if not product_ts_ids:
        print 'Aucun produit ts ne correspond %s' % ([str(x) + ',' for x in product_ts_test], )

    product_tg_ids = []
    for code in product_tg_test:
        product_tg_id = proxy.search('product.product', [('default_code', '=', code['default_code'])])
        product_tg_ids.append(product_tg_id)
        code.update({'id':product_tg_id[0]})
    if not product_tg_ids:
        print 'Aucun produit tg ne correspond %s' % ([str(x) + ',' for x in product_tg_test], )

    for code in product_tg_list:
        product_tg_list_id = proxy.search('product.product', [('default_code', '=', code['default_code'])])
        code.update({'id':product_tg_list_id[0]})

    for code in product_devis_test:
        product_devis_id = proxy.search('product.product', [('default_code', '=', code['default_code'])])
        product_devis = proxy.read('product.product', product_devis_id[0], ['name'])
        code.update({'product_id':product_devis_id[0], 'name':product_devis['name']})
        del code['default_code']

    partners = proxy.read('res.partner', partner_ids, [
                                'tarif_general_choice',
                                'tarif_choice',
                                'promo_choice',
                                'mea_choice',
                                'tarif_special_choice',
                                'property_product_pricelist',
                                'ref',
                                'name',
                                'tournee1',
                            ])
    if not partners:
        print 'Aucun partenaire ne correspond %s' % ([str(x) + ',' for x in partner_test], )

    ### Début algorithme ###

    # Pour chaque type de prix (Blanche, jaune)
    for pricetype in pricetype_test:
        # Pour chaque liste de prix de base (NU01,NU02,NU03,NU04)
        for pricelist_base in pricelist_base_test:
            # Pour chaque paramètre de partenaire possible
            for param_partner in param_partner_test:
                # Création du cas de figure
                dataTest = DataTest(param_partner['tarif_special'],
                                    param_partner['mea'],
                                    param_partner['promo'],
                                    pricelist_base,
                                    pricetype,
                                    partners,
                                    product_promo_ids,
                                    product_mea_ids,
                                    product_ts_ids,
                                    product_tg_ids,
                                    proxy)
                # On applique les nouveaux paramètres au partenaire
                dataTest.set_params_partner()

                print '\x1b[34;1m%s\x1b[0m' % ('############################## Nouveau cas de figure ##############################')
                print '\x1b[34;1m%s\x1b[0m' % (' Ts : %s ; Mea : %s ; Promo : %s ; %s ; Tarif : %s ; Partenaire : %s' \
                    %(param_partner['tarif_special'], param_partner['mea'], param_partner['promo'], \
                     pricelist_base, pricetype, [str(x) + ',' for x in partner_test]))
                # On check si la pricelist du partenaire correspond aux paramètres
                dataTest._check_pricelist_partner()
                dataTest._state('CHECK PRICELIST PARTNER')

                # Création promo
                dataTest.create_promo()
                dataTest._state('CREATE PROMO')

                # Création mea
                dataTest.create_mea()
                dataTest._state('CREATE MEA')
                # On check les item de la liste de prix et les prix

                # Création tarif spécial
                if dataTest.tarif_special == 'oui':
                    dataTest.create_tarspe()
                    dataTest._state('CREATE TS')

                # Création du devis
                dataTest.create_devis()
                dataTest._state('CREATE DEVIS')

                # On check les paramètres du devis
                dataTest._check_parameters_order()
                dataTest._state('CHECK PRICELIST DEVIS')
                # On check les prix des produits
                dataTest._check_price_product_order()
                dataTest._state('CHECK PRICE PRODUCT')


# Jeu de données :
    # Un partenaire P
    # Des produits Promo
        ## Produits A, E, F, G
    # Des produits Mea
        ## Produits B, E, F, H
    # Des produits Tarifs spéciaux
        ## Produits C, F, G, H
    # Des produits Tarif général
        ## Produit D
    # Un devis
        ## Produits A(Promo),B(Mea),C(Ts),D(Tg),E(Promo, Mea),F(Promo, Mea, Ts),G(Ts, Promo),H(Ts, Mea)
####Scenario
    #0 1) Création / Récupération d'un partenaire de test
        # -> attribution de paramètres d'ordre des tarifs (Rejouer pour chaque cas possible**)
            # _Vérification de la récupération de la bonne liste de prix
    # 2) Création d'une promo de la semaine en cours
            # _Vérification des pricelist item / listes de prix
    # 3) Création d'une mea de la semaine en cours
            # _Vérification des pricelist item / listes de prix
    # 4) Création d'un tarif spécial pour la semaine en cours pour ce partenaire
            # _Vérification des pricelist_item / listes de prix
    #I 5) Création d'un devis pour ce partenaire (Rejouer pour chaque cas possible**)
            # _Vérification des paramètres du devis par rapport aux paramètres client
            # _Vérification des prix en fonction de la pricelist (promo/mea/ts/tarif base, blanche ou jaune) et des paramètre client
            # -> Rejouer 1) en changeant les paramètres par rapport à II

    # II ** Changement des paramètres du partenaire (A tester pour les 4 listes de prix de bases ***)
        # 1 -> Tarif spécial non, mea non, promo non
        # 2 -> Tarif spécial non, mea non, promo oui
        # 3 -> Tarif spécial non, mea oui, promo oui
        # 4 -> Tarif spécial non, mea oui, promo non
        # 5 -> Tarif spécial oui, mea oui, promo oui
        # 6 -> Tarif spécial oui, mea non, promo non
        # 7 -> Tarif spécial oui, mea oui, promo non
        # 8 -> Tarif spécial oui, mea non, promo oui
    # III *** Changement des listes de prix de base du partenaire (Rejouer pour chaque type de promo ?****)
        # 1 -> NU01
        # 2 -> NU02
        # 3 -> NU03
        # 4 -> NU04
    # IV **** Changement des type de promo
        # 1 -> Blanche
        # 2 -> Jaune

####Algorithme
# Préparer les données à utiliser (Variables globales)
# Préparer les cas de figure à jouer (Variables globales)
# Initialiser 0, puis jouer I pour chaque cas de II, pour chaque cas de III et pour chaque cas de IV
# I/IIx/IIIy/IVz
# Avec x = entre 1 et 8
# Avec y = entre 1 et 4
# Avec z = entre 1 et 2


if __name__ == '__main__':
    sys.exit(main())     
