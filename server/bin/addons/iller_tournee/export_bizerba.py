#!/usr/bin/env python
#-*- encoding:utf-8 -*-

import base64
from osv import osv
import datetime
from tools import ustr

class export_bizerba(osv.osv_memory):
    _name = "export.bizerba"
    _inherit = ''

    def gen_bizerba_string(self, cr, uid, sol_id=None, num_ligne=None, context={}):
        """
        Génère une chaîne de caractère compatible avec Bizerba à partir de la ligne de commande
        """
        # Préparation des variables
        res = []
        sol_obj = self.pool.get('sale.order.line')
        if not sol_id or not num_ligne:
            return False
        sol = sol_obj.browse(cr, uid, sol_id, context=context)
        tournee = sol.order_id.tournee_id
        commande = sol.order_id
        # LCOM
        res.append('LCOM')
        # (9) Num commande sur 9 chiffres (complété par des 0)
        res.append(ustr(commande.client_order_ref[:10] or 0).rjust(9, "0"))
        # (9) Numéro de ligne de commande (complété par des 0)
        res.append(ustr(num_ligne or 0).rjust(9, "0"))
        # (20) Nom du client (complété par des espaces)
        res.append(ustr(sol.order_partner_id.name or " ")[:20].ljust(20, " "))
        # Une espace
        res.append(" ")
        # (6) JJMMAA de commande
        date = datetime.datetime.strptime(commande.date_order, '%Y-%m-%d')
        res.append(ustr(date.strftime('%d%m%y') or "000000"))
        # Une espace
        res.append(" ")
        # (10) Ville sur 10
        res.append(ustr(commande.partner_shipping_id.city or " ")[:10].rjust(10, " "))
        # (3) Numéro tournée sur 3 (complété par 0)
        res.append(ustr(tournee.id or "0").rjust(3, "0"))
        # (30) Nom tournée sur 30
        res.append(ustr(tournee.name or " ")[:30].ljust(30, " "))
        # (8) Date de livraison AAAAMMJJ
        # date de commande + delay (sur sale_order_line)
        date_livraison = datetime.datetime(date.year, date.month, date.day) + datetime.timedelta(days=sol.delay)
        res.append(ustr(date_livraison.strftime('%Y%m%d') or "00000000"))
        # (4) Heure de départ HHMM (compléter avec un 0 si besoin)
        res.append(ustr(tournee.heure_depart or "0").rjust(4, "0"))
        # (2) "00"
        res.append("00")
        # (30) commentaire de commande(compléter avec des espaces)
        res.append(ustr(commande.note or " ")[:30].ljust(30, " "))
        # (30) commentaire ligne (compléter avec des espaces)
        res.append(ustr(sol.notes or " ")[:30].ljust(30, " "))
        # (8) "00000000"
        res.append("0".ljust(8, "0"))
        # (6) Code article (compléter avec des 0)
        produit = sol.product_id
        res.append(ustr(produit.default_code or "0")[:6].rjust(6, "0"))
        # (4) Code emballage (compléter avec des 0) (semble être toujours à 1)
        res.append("1".rjust(4, "0"))
        # (4) Type de conditionnement (compléter avec des 0)
        res.append(ustr(produit.type_cond or "0").rjust(4, "0"))
        # (15) espaces
        res.append(" ".ljust(15, " "))
        # (4) Type étiquette article (toujours à 1)
        res.append("1".rjust(4, "0"))
        # (6) "999999"
        res.append("9".ljust(6, "9"))
        # (6) "999999"
        res.append("9".ljust(6, "9"))
        # (1) Article type préselection
        type_preselec = produit.type_preselec or 0
        res.append(ustr(type_preselec)[:1])
        # (1) Article type pesée (0, 7 ou 8)
        type_pesee = produit.type_pesee or 0
        res.append(ustr(type_pesee)[:1])
        # (7) "0000000"
        res.append("0".rjust(7, "0"))
        # (7) Article poids fixe si article type pesée = 2, sinon "0000000"
        if type_pesee == 2:
            res.append(ustr(produit.weight_net or "0").rjust(7, "0"))
        else:
            res.append("0".rjust(7, "0"))
        # (3) "000"
        res.append("0".rjust(3, "0"))
        # (6) "000000"
        res.append("0".rjust(6, "0"))
        # (7) Qté ligne fois 1000 si article type préselection = 1, sinon afficher quantité ligne (compléter avec des 0)
        qte = sol.product_uom_qty or 0
        if type_preselec == 1:
            qte *= 1000
        res.append(ustr(qte).rjust(7, "0"))
        # (4) Article type emballage (toujours à 0)
        res.append("0".rjust(4, "0"))
        # (50) Espaces
        res.append(" ".rjust(50, " "))
        # (50) Espaces
        res.append(" ".rjust(50, " "))
        # (2) Poste (par exemple SE)
        res.append(ustr(sol.poste_id.name or tournee.decoupe_id.name or "XX00")[:4])
        # (2) Poste (par exemple O4) (plus nécessaire car déjà donné avec name)
        
        # On retourne le résultat sous forme d'une seule chaîne
        return ''.join(res)

    def get_file(self, cr, uid, ids, context={}):
        """
        Génère un binaire 'hote.txt' contenant des informations sur les découpes à faire pour une commande donnée.
        Ceci afin de l'exporter vers Bizerba qui affiche lesdites informations.
        """
        # Préparation de variables
        nom_fichier = 'hote.txt'
        attachement_obj = self.pool.get('ir.attachment')
        sale_order_obj = self.pool.get('sale.order')
        sol_obj = self.pool.get('sale.order.line')
        total = 0
        # Parcours de chaque commande
        for sale_order in sale_order_obj.browse(cr, uid, ids):
            chaine = ''
            lines = sale_order_obj.read(cr, uid, sale_order.id, ['order_line']).get('order_line', False)
            # Parcours de chaque ligne
            num_ligne = 1
            for sol_id in lines:
                # Vérification si découpe, si oui, alors on génère une chaîne de caractère
                if sol_obj.browse(cr, uid, sol_id, context=context).product_id.code_affectation == 'DECP':
                    # Génération de la chaine de la ligne de commande
                    chaine_ligne = self.gen_bizerba_string(cr, uid, sol_id, num_ligne, context=context)
                    # Ajout au fichier de commande
                    chaine += chaine_ligne
                    chaine += "\n"
                    num_ligne += 1
                    total += 1
            
            # Écriture de la chaine créée et association avec la commande si jamais on a plus d'une ligne
            if total > 0:
                data = base64.encodestring(chaine.encode("utf-8"))
                vals = {
                    'name': 'Fichier bizerba',
                    'datas': data,
                    'datas_fname': nom_fichier,
                    'description': 'Fichier prévu pour le PC Bizerba',
                    'res_model': 'sale.order',
                    'res_id': sale_order.id,
                }
                # Création de l'élément "fichier joint" dans OpenERP
                attachement_obj.create(cr, uid, vals)
        return True

export_bizerba()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
