#!/usr/bin/env python
#-*- encoding:utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution    
#    Copyright (C) 2011 TeMPO Consulting. All Rights Reserved
#    TeMPO Consulting (<http://www.tempo-consulting.fr/>).
#    Author: Olivier DOSSMANN
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

from osv import osv
from osv import fields

class nbre_cmde_par_tournee(osv.osv):
    _name = "nbre.cmde.par.tournee"
    _description = "Nombre de commandes par code regroupement (tournee)"
    _auto = False

    _order = 'heure_depart'

    _columns = {
        'name': fields.char(string="Nom", size=64, readonly=True),
        'heure_depart': fields.integer(string='Heure depart', readonly=True),
        'tot_non_validees': fields.integer(string="Non validées", readonly=True),
        'tot_facturees': fields.integer(string="Facturées", readonly=True),
    }

    def init(self, cr):
        cr.execute("""
            create or replace view nbre_cmde_par_tournee as (

                SELECT
                    tournee.id AS id, 
                    tournee.name AS name, 
                    tournee.heure_depart AS heure_depart, 
                    COALESCE(nonval.non_validees,0) AS tot_non_validees, 
                    COALESCE(fact.facturees, 0) AS tot_facturees 
                FROM
                    (
                        SELECT 
                            ti2.id, 
                            COUNT(so.id) AS non_validees
                        FROM 
                            sale_order AS so, 
                            tournee_iller AS ti 
                        RIGHT JOIN 
                            tournee_iller AS ti2 ON (ti.id = ti2.id)
                        WHERE 
                            so.tournee_id = ti.id
                        AND 
                            so.state != 'done'
                        GROUP BY 
                            ti2.id, 
                            ti2.name, 
                            ti.heure_depart
                        ORDER BY 
                            ti2.id
                    ) AS nonval
                LEFT JOIN 
                    (
                        SELECT 
                            ti2.id, 
                            COUNT(so.id) AS facturees
                        FROM 
                            sale_order AS so, 
                            sale_order_invoice_rel AS soir, 
                            account_invoice AS ai, 
                            tournee_iller AS ti
                        RIGHT JOIN 
                            tournee_iller AS ti2 ON (ti.id = ti2.id)
                        WHERE 
                            so.tournee_id = ti.id
                        AND 
                            so.id = soir.order_id
                        AND 
                            soir.invoice_id = ai.id
                        GROUP BY 
                            ti2.id, 
                            ti2.name, 
                            ti.heure_depart
                        ORDER BY 
                            ti.heure_depart
                    ) AS fact 
                ON nonval.id = fact.id
                RIGHT JOIN 
                    tournee_iller AS tournee ON tournee.id = nonval.id OR tournee.id = fact.id
            )""")

nbre_cmde_par_tournee()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
