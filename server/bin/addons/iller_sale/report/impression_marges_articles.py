#!/usr/bin/env python
#-*- encoding:utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution    
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    Tempo Consulting (<http://www.tempo-consulting.fr/>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from report import report_sxw
from osv import osv
import time
import locale

class impression_marges_articles(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        """
        Initialisation du 'parser'
        """
        super(impression_marges_articles, self).__init__(cr, uid, name, context)
        self.localcontext.update({
            'getCateg': self.get_categorie,
            'getElements': self.get_elements,
            'getMarge': self.get_marge,
            'getPrixHA': self.get_prix_ha,
            'getQteArticles': self.get_qte_articles,
            'time': time,
            'locale': locale,
        })

    def get_categorie(self, art=None, categ=None):
        """
        Donne la catégorie à afficher
        """
        if not art and not categ:
            return False
        else:
            if categ:
                return categ[1].split(' ')[1]
            art_id = art[0]
            return self.pool.get('product.product').browse(self.cr, self.uid, art_id).categ_id.name

    def get_elements(self, art=None, categ=None):
        """
        Donne les articles associés à la catégorie.
        Renvoi un tableau contenant soit l'article demandé, soit un ensemble d'articles de la catégorie demandée
        """
        prod_obj= self.pool.get('product.product')
        if not art and not categ:
            return False
        else:
            if categ:
                categ_id = categ[1].split(' ')[1]
                product_ids = prod_obj.search(self.cr, self.uid, [('categ_id', '=', categ_id)])
                return prod_obj.browse(self.cr, self.uid, product_ids)
            return prod_obj.browse(self.cr, self.uid, [art[0]])

    def get_factures_article(self, article_id=None, date_deb=None, date_fin=None):
        """
        Donne l'ensemble des lignes de factures pour un article donné dans une période donnée
        """
        if not article_id or not date_deb or not date_fin:
            return False
        # Requête pour récupérer des donnés sur le produit facturé (donc vendu), avec les critères suivants : 
        # - les factures sont en état ouverte ou payées
        # - les factures sont de type "out_invoice"
        # - on ne récupère que quelques données
        # - dans la période choisie (date début et date fin)
        self.cr.execute(
            '''
            SELECT invl.id, invl.price_unit, invl.price_subtotal, invl.quantity, invl.product_id, inv.date_invoice
            FROM account_invoice_line as invl, account_invoice as inv
            WHERE product_id = %s
            AND invl.invoice_id = inv.id
            AND type = 'out_invoice'
            AND state in ('open','paid')
            AND date_invoice >= %s
            AND date_invoice <= %s
            ''', (article_id, date_deb, date_fin)
        )
        res = self.cr.fetchall()
        return res

    def get_marge(self, article_id=None, date_deb=None, date_fin=None):
        """
        Donne la marge d'un article donné
        """
        if not article_id or not date_deb or not date_fin:
            return False
        # Récupération des lignes de factures nécessaires au calcul de la marge
        res = self.get_factures_article(article_id, date_deb, date_fin)
        if not res:
            return "Non vendu"
        # Préparation de la somme des marges (que nous diviserons par le nombre de lignes trouvées pour cet article)
        somme_marge = 0
        # On parcours les lignes de facture
        for facture in res:
            prix_ha = self.get_prix_ha(article_id, date_deb, date_fin)
            prix_vte = facture[1]
            ##### EXPLICATIONS
            # Marge = (prix_vente - prix_achat) ÷ prix_vente
            # Donc aussi égal à :
            # Marge = 1 - (prix_achat ÷ prix_vente)
            #####
            # On ajoute la marge à la somme
            somme_marge += (1 - (prix_ha/prix_vte))
        # Calcul de la moyenne des marges
        #+ somme des marges sur nombre total de lignes de factures trouvées
        #+ on ramène à 100 (pourcentage)
        #+ on arrondi à 2 chiffres après la virgule
        return round(somme_marge/len(res)*100, 2)

    def get_prix_ha(self, article_id=None, date_deb=None, date_fin=None):
        """
        Donne le prix d'achat
        """
        if not article_id or not date_deb or not date_fin:
            return False
        # Requête pour récupérer le prix d'achat dans la période choisie
        self.cr.execute('''SELECT nouveau_prix_achat FROM product_price_history WHERE product_id=%s AND (name >= %s OR name <= %s) ORDER BY name desc LIMIT 1''', (article_id, date_deb, date_fin))
        res = self.cr.fetchone()
        # Prix par défaut (si pas de retour de la requête)
        prix = self.pool.get('product.product').browse(self.cr, self.uid, article_id).standard_price
        if res:
            prix = res[0]
        return prix

    def get_qte_articles(self, article_id=None, date_deb=None, date_fin=None):
        """
        Donne le nombre d'articles vendus pour un produit donné
        NB: n'est potentiellement pas fiable, puisqu'aucune unité de mesure n'est enregistré sur la ligne de facture
        """
        if not article_id or not date_deb or not date_fin:
            return False
        # Récupération des lignes de factures pour le produit donné
        factures = self.get_factures_article(article_id, date_deb, date_fin)
        total = 0
        for ligne in factures:
            total += ligne[3]
        return total

report_sxw.report_sxw('report.marges.articles','product.product','addons/iller_sale/report/report_marges_articles.rml', parser=impression_marges_articles)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
