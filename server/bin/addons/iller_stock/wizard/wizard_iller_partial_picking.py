# -*- encoding: utf-8 -*-
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
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import netsvc
from tools.misc import UpdateableStr, UpdateableDict
import pooler

import wizard
from osv import osv
from tools.translate import _

_moves_arch = UpdateableStr()
_moves_fields = UpdateableDict()

_moves_arch_end = '''<?xml version="1.0"?>
<form string="Résultat d'empaquetage">
    <label
        string="Le processus d'empaquetage s'est terminé avec succès !"
        colspan="4" />
    <field
        name="back_order_notification"
        colspan="4"
        nolabel="1" />
</form>'''
_moves_fields_end = {
    'back_order_notification': {
        'string': 'Ordre de retour',
        'type': 'text',
        'readonly': True,
    },
}

_reliquat_arch = UpdateableStr()
_reliquat_fields = UpdateableDict()


def make_default(val):
    """
    ???
    """
    def fct(uid, data, state):
        return val
    return fct


def _to_xml(s):
    """
    Transforme un texte en une chaîne compatible XML.
    """
    return (s or '').\
        replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def _get_diff(qte_base=None, qte=None):
    if not qte_base and not qte:
        return 0.0
    return qte_base - qte


def _check_state(self, cr, uid, data, context):
    """
    Vérifie l'existence de reliquats, si oui on renvoie l'état "split2", sinon
    on renvoie "end2"
    """
    if data.get('form', False).get('reliquats', False):
        return 'split2'
    return 'end2'


def _check_reliquat(self, cr, uid, data, context=None):
    """
    Vérifie si des reliquats sont à faire et rempli la variable data['form'] 
    avec deux listes : 
     - la première contenant les articles qui sont équivalents à la quantité 
       commandée
     - la seconde contenant des articles ayant une différence entre la quantité
       commandée et celle livrée
    """
    sm_obj = pooler.get_pool(cr.dbname).get('stock.move')

    if context is None:
        context = {}

    # Préparation de divers éléments
    form = data.get('form', [])
    entrees = form.get('moves', [])

    data['form']['reliquats'] = []  # ensemble des paquets dits reliquats
    data['form']['complets'] = []  # ensemble des paquets à valider tels quels

    # On consulte les entrées s'il y a lieu
    if entrees:
        # Pour chacune on calcule la différence avec la quantité commandée
        for i in entrees:
            qte_choisie = form.get('move%s' % i) or 0.0
            qte_reelle = sm_obj.browse(cr, uid, i).product_qty or 0.0
            diff = qte_reelle - qte_choisie
            if diff > 0.0:
                # la différence est supérieure à 0 donc il manque des éléments 
                # pour la livraison. On doit faire un reliquat (en théorie)
                data['form']['reliquats'].append(i)
            else:
                # la différence est inférieure ou égale : on ne doit rien faire 
                # de particulier
                data['form']['complets'].append(i)

    return data['form']


def _get_moves(self, cr, uid, data, context=None):
    """
    Retourne l'ensemble des mouvements
    """
    pick_obj = pooler.get_pool(cr.dbname).get('stock.picking')

    if context is None:
        context = {}

    pick = pick_obj.browse(cr, uid, [data['id']], context)[0]
    res = {}

    _moves_fields.clear()
    _moves_arch_lst = [
        '<?xml version="1.0"?>', '<form string="Faire le colisage">',
    ]

    for m in pick.move_lines:
        if m.state in ('done', 'cancel'):
            continue

        quantity = m.product_qty
        if m.state != 'assigned':
            quantity = 0.00

        _moves_arch_lst.append('<field name="move%s" />' % (m.id,))
        _moves_fields['move%s' % m.id] = {
            'string': _to_xml(m.name),
            'type': 'float',
            'required': True,
            'default' : make_default(quantity),
        }

        if (pick.type == 'in') and (m.product_id.cost_method == 'average'):
            price = 0.00
            if hasattr(m, 'purchase_line_id') and m.purchase_line_id:
                price = m.purchase_line_id.price_unit

            currency = 0.00
            if hasattr(pick, 'purchase_id') and pick.purchase_id:
                currency = pick.purchase_id.pricelist_id.currency_id.id

            _moves_arch_lst.append(
                '<group col="6"><field name="uom%s" nolabel="1"/> \
                <field name="price%s"/>' % (m.id, m.id,)
            )

            _moves_fields['price%s' % m.id] = {
                'string': 'Unit Price',
                'type': 'float',
                'required': True,
                'default': make_default(price),
            }

            _moves_fields['uom%s' % m.id] = {
                'string': 'UOM',
                'type': 'many2one',
                'relation': 'product.uom',
                'required': True,
                'default': make_default(m.product_uom.id),
            }

            _moves_arch_lst.append(
                '<field name="currency%d" nolabel="1"/></group>' % (m.id,),
            )
            _moves_fields['currency%s' % m.id] = {
                'string': 'Currency',
                'type': 'many2one',
                'relation': 'res.currency',
                'required': True,
                'default': make_default(currency),
            }

        _moves_arch_lst.append('<newline/>')
        res.setdefault('moves', []).append(m.id)

    _moves_arch_lst.append('</form>')
    _moves_arch.string = '\n'.join(_moves_arch_lst)

    return res


def _generate_form(cr, uid, form={}, elements=[], readonly=False):
    """
    Génère un formulaire contenant les éléments donnés par elements.
    Ceci ne fonctionne QUE pour des éléments "move" contenus dans data['form'].
    Fonction utilisée par _get_reliquats.
    """
    # Préparation des éléments
    sm_obj = pooler.get_pool(cr.dbname).get('stock.move')

    arch_lst = []
    fields = {}

    # Boucle sur les éléments donnés
    arch_lst.append('<group colspan="4" col="5">')
    for move_id in elements:
        qte = form.get('move%s' % move_id)
        nom = sm_obj.browse(cr, uid, move_id).name

        arch_lst.append('<field name="move%s" colspan="1"/>' % (move_id,))
        fields['move%s' % move_id] = {
            'string': _to_xml(nom),
            'type': 'float',
            'required': True,
            'default': make_default(qte),
            'readonly': readonly,
            'on_change': "qty_change(" +
                         str(move_id) +
                         ", move" +
                         str(move_id) +
                         ")",
        }

        # Ajout d'un champ "Différence" pour chaque élément lisible
        # Par défaut nous n'en ajoutons pas
        if not readonly:
            move_qty = sm_obj.browse(cr, uid, move_id).product_qty
            arch_lst.append(
                '<field name="diff%s" string="Diff." colspan="2"/>' % move_id
            )
            fields['diff%s' % move_id] = {
                'type': 'float',
                'required': False,
                'readonly': True,
                'default': _get_diff(move_qty, qte),
                'help': "Différence entre la quantité demandée"\
                        "et celle à livrer"
            }

        # Ajout d'un champ "Reliquat" si l'élément est de type lisible
        # Par défaut nous n'en ajoutons pas
        if not readonly:
            arch_lst.append(
                '<field name="reliquat%s" nolabel="1" colspan="1"/>' % move_id
            )
            fields['reliquat%s' % move_id] = {
                'type': 'boolean',
                'required': False,
                'default': False,
                'help': "Faire un reliquat ?",
            }

        arch_lst.append('<newline />')

    arch_lst.append('</group>')
    return arch_lst, fields


def _get_reliquats(self, cr, uid, data, context={}):
    """
    Retourne un formulaire contenant les reliquats, puis les livraisons normales
    """
    # Préparation de différents éléments
    form = data.get('form', [])

    # Préparation du début du formulaire
    _reliquat_arch_lst = [
        '<?xml version="1.0"?>',
        '<form string="Résultat d\'empaquetage">',
        '  <separator string="À mettre en reliquat ?" />',
        '  <newline />',
        """  <label string="Cochez les éléments dont il faut faire un reliquat."
         colspan="6"/>""",
            '<newline />',
    ]

    # Affichage des reliquats
    reliquats = form.get('reliquats', [])
    (arch, fields) = _generate_form(cr, uid, form=form, elements=reliquats)
    for chaine in arch:
        _reliquat_arch_lst.append(chaine)
    for el in fields:
        _reliquat_fields[el] = fields[el]
    # Préparation de la suite du formulaire
    # Affichage des paquets complets
    complets = form.get('complets', [])
    (arch, fields) = _generate_form(cr, uid,
                                    form=form,
                                    elements=complets,
                                    readonly=True)
    # Ajout d'un titre si nous possédons un à plusieurs éléments complets
    if len(arch) > 0:
        _reliquat_arch_lst.append(
            '<separator string="Liste des éléments complets" />'
        )
        _reliquat_arch_lst.append(
            '<newline />'
        )
    # Ajout des éléments complets
    for chaine in arch:
        _reliquat_arch_lst.append(chaine)
    for el in fields:
        _reliquat_fields[el] = fields[el]
    # Fermeture du formulaire
    _reliquat_arch_lst.append('</form>')
    _reliquat_arch.string = '\n'.join(_reliquat_arch_lst)

    return {}


def _do_split(self, cr, uid, data, context):
    """
    Traite l'ensemble des éléments pour reliquat ou non
    """
    move_obj = pooler.get_pool(cr.dbname).get('stock.move')
    pick_obj = pooler.get_pool(cr.dbname).get('stock.picking')
    pick = pick_obj.browse(cr, uid, [data['id']])[0]
    new_picking = None

    complete, too_many, too_few = [], [], []
    pool = pooler.get_pool(cr.dbname)
    for move in move_obj.browse(cr, uid, data['form'].get('moves',[])):
#        reliquat = data['form'].get('reliquat%s' % move.id, False)
        reliquat = move.reliquat
        if not reliquat:
            if move.product_qty == move.initial_qty:
                complete.append(move)
            elif move.product_qty < move.initial_qty:
                too_many.append(move)
        else:
            too_few.append(move)
        """
        if move.product_qty == data['form']['move%s' % move.id]:
            complete.append(move)
        elif move.product_qty > data['form']['move%s' % move.id]:
            if reliquat:
                too_few.append(move)
            else:
                complete.append(move)
        else:
            too_many.append(move)
        """

        # Average price computation
        if (pick.type == 'in') and (move.product_id.cost_method == 'average'):
            product_obj = pool.get('product.product')
            currency_obj = pool.get('res.currency')
            users_obj = pool.get('res.users')
            uom_obj = pool.get('product.uom')

            product = product_obj.browse(cr, uid, [move.product_id.id])[0]
            user = users_obj.browse(cr, uid, [uid])[0]

            qty = data['form']['move%s' % move.id]
            uom = data['form']['uom%s' % move.id]
            price = data['form']['price%s' % move.id]
            currency = data['form']['currency%s' % move.id]

            qty = uom_obj.compute_qty(cr, uid, uom, qty, product.uom_id.id)
            if qty > 0:
                new_price = currency_obj.compute(cr, uid, currency,
                                                 user.company_id.currency_id.id,
                                                 price)
                new_price = uom_obj.compute_price(cr, uid, uom, new_price,
                                                  product.uom_id.id)
                if product.qty_available <= 0:
                    new_std_price = new_price
                else:
                    new_std_price = \
                        ((product.standard_price * product.qty_available) +
                         (new_price * qty)) / (product.qty_available + qty)

                product_obj.write(cr, uid, [product.id],
                        {'standard_price': new_std_price})
                move_obj.write(cr, uid, [move.id], {'price_unit': new_price})

    for move in too_few:
        if not new_picking:

            new_picking = pick_obj.copy(cr, uid, pick.id, {
                'name': pool.get('ir.sequence').get(cr, uid, 'stock.picking'),
                'move_lines' : [],
                'state':'draft',
            })

        if data['form']['move%s' % move.id] != 0:
            move_obj.copy(cr, uid, move.id, {
                'product_qty' : data['form']['move%s' % move.id],
                'product_uos_qty':data['form']['move%s' % move.id],
                'picking_id' : new_picking,
                'state': 'assigned',
                'move_dest_id': False,
                'price_unit': move.price_unit,
            })

        move_obj.write(cr, uid, [move.id], {
            'product_qty' : move.product_qty - data['form']['move%s' % move.id],
            'product_uos_qty':move.product_qty - data['form']['move%s' % move.id],
        })

    if new_picking:
        move_obj.write(cr, uid, [c.id for c in complete], {
            'picking_id': new_picking,
        })
        for move in too_many:
            move_obj.write(cr, uid, [move.id], {
                'product_qty' : data['form']['move%s' % move.id],
                'product_uos_qty': data['form']['move%s' % move.id],
                'picking_id': new_picking,
            })
    else:
        # Cas des éléments complets mais possiblement modifiés
        for move in complete:
            move_obj.write(cr, uid, [move.id], {
                'product_qty': data['form']['move%s' % move.id],
                'product_uos_qty': data['form']['move%s' % move.id]
            })
        for move in too_many:
            move_obj.write(cr, uid, [move.id], {
                'product_qty': data['form']['move%s' % move.id],
                'product_uos_qty': data['form']['move%s' % move.id]
            })

    data['new_picking'] = new_picking
    data['pick_id'] = pick.id

    return data

"""POUR FACTURATION"""
_invoice_arch = """<?xml version="1.0"?>
    <form string="Créer les factures invoices">
        <separator colspan="4" string="Créer les factures" />
        <field name="journal_id"/>
        <newline/>
        <field name="group"/>
        <newline/>
        <field name="type"/>
    </form>
"""

_invoice_fields = {
    'journal_id': {
        'string': 'Journal de destination',
        'type': 'many2one',
        'relation': 'account.journal',
        'required': True,
    },
    'group': {
        'string': 'Grouper par partenaire',
        'type': 'boolean',
    },
    'type': {
        'string': 'Type',
        'type': 'selection',
        'selection': [
            ('out_invoice', 'Facture Client'),
            ('in_invoice', 'Facture Fournisseur'),
            ('out_refund', 'Avoir Client'),
            ('in_refund', 'Avoir Fournisseur'),
            ],
        'required': True,
    },
}


def _check_invoicing(self, cr, uid, data, context=None):
    """
    Vérifie si le client possède un mode de facturation à "NON" ('n').
    Si oui, on renvoie l'état 'invoice', sinon on renvoie l'état 'end3' (fin)
    """
    move_obj = pooler.get_pool(cr.dbname).get('stock.move')
    pick_obj = pooler.get_pool(cr.dbname).get('stock.picking')

    if data.get('id', False):
        data_id = data.get('id')

        sp = pick_obj.browse(cr, uid, data_id, context=context)
        if sp.address_id and \
                sp.address_id.partner_id and \
                sp.address_id.partner_id.facturation_bl:
            type_facturation = sp.address_id.partner_id.facturation_bl
            # Si facturation = NON, alors on va vers l'état 'invoice'
            if type_facturation == 'n':
                return 'invoice'
            
    return 'end3'


def _get_type_invoice(obj, cr, uid, data, context=None):
    pick_obj = pooler.get_pool(cr.dbname).get('stock.picking')
    usage = 'customer'
    pick = pick_obj.browse(cr, uid, data['id'], context=context)
    if pick.invoice_state == 'invoiced':
        raise wizard.except_wizard(
            _('Erreur utilisateur'),
            _('La facture a déjà été créée.'),
        )
    if pick.invoice_state == 'none':
        raise wizard.except_wizard(
            _('Erreur utilisateur'),
            _('La facture ne peut être créée depuis le colisage.'),
        )

    if pick.move_lines:
        usage = pick.move_lines[0].location_id.usage

    if pick.type == 'out' and usage == 'supplier':
        inv_type = 'in_refund'
    elif pick.type == 'out' and usage == 'customer':
        inv_type = 'out_invoice'
    elif pick.type == 'in' and usage == 'supplier':
        inv_type = 'in_invoice'
    elif pick.type == 'in' and usage == 'customer':
        inv_type = 'out_refund'
    else:
        inv_type = 'out_invoice'
        
    data['type'] = inv_type
    return data


def _create_invoice(obj, cr, uid, data, context=None):
    """
    Create invoice from stock picking
    """
    pool = pooler.get_pool(cr.dbname)
    pick_obj = pool.get('stock.picking')
    jour_obj = pool.get('account.journal')

    if 'new_picking' in data and data['new_picking']:
        data['id'] = data['new_picking']
        data['ids'] = [data['new_picking']]

    inv_type = data['type']
    journal_id = jour_obj.search(cr, uid, [
        ('name', 'ilike', 'VENTES ILLER'),
        ('type', '=', 'sale'),
    ], context=context)
    if not journal_id:
        raise wizard.except_wizard(
            _('Erreur journal des ventes'),
            _('Le journal des ventes \'VENTES ILLER\' n\'a pas été trouvé.'),
        )

    res = pick_obj.action_invoice_create(cr, uid, data['ids'],
                                         journal_id[0], False,
                                         inv_type, context=context)

    invoice_ids = res.values()
    for invoice_id in invoice_ids:
        wf_service = netsvc.LocalService("workflow")
        wf_service.trg_validate(uid, 'account.invoice',
                                invoice_id, 'invoice_open', cr)

    if not invoice_ids:
        raise wizard.except_wizard(
            _('Erreur'),
            _('La facture n\'a pas été créée.'),
        )

    return 'end3'


def _workflow_validation(self, cr, uid, data, context=None):
    """
    Valide le workflow si toutes les étapes ont été accomplies
    """

    # Préparation des différents éléments
    new_picking = data['new_picking']
    pick_id = data['pick_id']
    pick_obj = pooler.get_pool(cr.dbname).get('stock.picking')

    # At first we confirm the new picking (if necessary)
    wf_service = netsvc.LocalService("workflow")
    if new_picking:
        wf_service.trg_validate(uid, 'stock.picking',
                                new_picking, 'button_confirm', cr)
    # Then we finish the good picking
    if new_picking:
        pick_obj.write(cr, uid, [pick_id], {
            'backorder_id': new_picking,
        })
        pick_obj.action_move(cr, uid, [new_picking])
        wf_service.trg_validate(uid, 'stock.picking',
                                new_picking, 'button_done', cr)
        wf_service.trg_write(uid, 'stock.picking', pick_id, cr)
    else:
        pick_obj.action_move(cr, uid, [pick_id])
        wf_service.trg_validate(uid, 'stock.picking',
                                pick_id, 'button_done', cr)

    bo_name = ''
    if new_picking:
        bo_name = pick_obj.read(cr, uid, [new_picking], ['name'])[0]['name']

    return {'new_picking':new_picking or False, 'back_order':bo_name}


class iller_partial_picking(wizard.interface):

    states = {
        'init': {
            'actions': [
                _get_moves,
            ],
            'result': {
                'type': 'form',
                'arch': _moves_arch,
                'fields': _moves_fields,
                'state': (
                    ('end', '_Annuler'),
                    ('split', '_Faire colisage')
                )
            },
        },
        'split': {
            'actions': [
                _check_reliquat,
                ],
            'result': {
                'type': 'choice',
                'next_state': _check_state,
            },
        },
        'split2': {
            'actions': [
                _get_reliquats,
            ],
            'result': {
                'type': 'form',
                'arch': _reliquat_arch,
                'fields': _reliquat_fields,
                'state': (
                    ('end', '_Annuler'),
                    ('end2', '_Terminer')
                )
            },
        },
        'end2': {
            'actions': [
                _do_split
            ],
            'result': {
                'type': 'choice',
                'next_state': _check_invoicing,
            },
        },
        'invoice': {
            'actions': [
                _get_type_invoice,
            ],
            'result': {
                'type': 'choice',
                'next_state': _create_invoice,
            },
#            'result': {
#                'type': 'form',
#                'arch': _invoice_arch,
#                'fields': _invoice_fields,
#                'state': (
#                    ('end', '_Annuler'),
#                    ('create_invoice', '_Continuer'),
#                )
#            }

        },
#         'create_invoice': {
#             'actions': [],
#             'result': {
#                 'type': 'action',
#                 'action': _create_invoice,
#                 'state': 'end3'
#             }
#         },
        'end3': {
            'actions': [],
            'result': {
                'type': 'action',
                'action': _workflow_validation,
                'state': 'end',
            },
        },
    }

iller_partial_picking('iller_partial_picking')


class wizard_iller_partial_picking(osv.osv_memory):
    _name = "wizard.iller_partial_picking"

    def qty_change(self, cr, uid, ids, move_id=None, qty=None):
        """
        Retourne la différence entre la quantité commandée et la quantité 
        réellement livrée.
        Si jamais la différence est supérieure à zéro, alors on affiche la 
        coche permettant de faire un reliquat.
        """
        # Vérification de la présence des variables nécessaires
        if not move_id and not qty:
            return False
        # Valeur par défaut
        diff = 0.00
        # Récupération de divers éléments
        sm_obj = pooler.get_pool(cr.dbname).get('stock.move')
        # Calcul
        for sm in sm_obj.browse(cr, uid, [move_id]):
            diff = sm.product_qty - qty
        # Résultat
        res = {'value': {'diff%s' % move_id: diff}}
        return res

wizard_iller_partial_picking()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

