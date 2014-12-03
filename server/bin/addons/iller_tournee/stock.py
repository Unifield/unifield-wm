#!/usr/bin/env python
# -*- encoding: utf-8 -*-

from osv import osv
from osv import fields
import netsvc

class iller_picking(osv.osv):
    _name = 'stock.picking'
    _inherit = 'stock.picking'
 # Mise à jour du code sur le changement du partenaire id
    def onchange_partner_id(self, cr, uid, ids, part, context=None):
        
        if not part:
            return {'value': {'code': False, 'tournee_id': False}}

        part = self.pool.get('res.partner').browse(cr, uid, part)

        val = {

            'code': part.ref,
            #~ 'tournee_id': tournee[0],
        }

        return {'value': val}
    
    # Récupération du code client à afficher dans le formulaire
    def _get_code_client(self, cr, uid, ids, field_name, arg, context=None):
        
        if isinstance(ids, (int, long)):
            ids = [ids]
        
        res = {}
        for stock_picking_record in self.browse(cr, uid, ids, context=context):
            partner = stock_picking_record.address_id.partner_id
            res[stock_picking_record.id] = partner.ref
            
        return res

    _columns = {
        'tournee_id': fields.many2one('tournee.iller', string='Tournée', required=False),
        'code': fields.function(_get_code_client, type='char', method=True, string='Code', readonly=True),
        'bac_qty': fields.integer(u'Quantité bacs'),
        'num_preparateur': fields.char(size=64, string=u'Numéro du préparateur'),
        'nb_elts': fields.integer(u'Nombre d\'éléments'),
    }

    def _postes_valides(self, cr, uid, ids, context={}):
        for sp in self.browse(cr, uid, ids):
            for move in sp.move_lines:
                if not move.poste_id.id:
                    raise osv.except_osv('Alerte', "Un ou plusieurs champs « Poste de préparation » n'est pas rempli. Veuillez remplir tous les champs « Poste de préparation » pour chacune des lignes de mouvement.")
        return True

    def draft_force_assign(self, cr, uid, ids, *args):
        self._postes_valides(cr, uid, ids)
        wf_service = netsvc.LocalService("workflow")
        for pick in self.browse(cr, uid, ids):
            wf_service.trg_validate(uid, 'stock.picking', pick.id,
                'button_confirm', cr)
        return True

    def draft_validate(self, cr, uid, ids, *args):
        self._postes_valides(cr, uid, ids)
        wf_service = netsvc.LocalService("workflow")
        self.draft_force_assign(cr, uid, ids)
        for pick in self.browse(cr, uid, ids):
            move_ids = [x.id for x in pick.move_lines]
            self.pool.get('stock.move').force_assign(cr, uid, move_ids)
            wf_service.trg_write(uid, 'stock.picking', pick.id, cr)

            self.action_move(cr, uid, [pick.id])
            wf_service.trg_validate(uid, 'stock.picking', pick.id, 'button_done', cr)
        return True

    def _create_invoice(obj, cr, uid, data, context=None):
        res = super(iller_picking, self)._create_invoice(self, cr, uid, data, context=context)
        if data['form'].get('new_picking', False):
            data['id'] = data['form']['new_picking']
            data['ids'] = [data['form']['new_picking']]
        pool = pooler.get_pool(cr.dbname)
        picking_obj = pooler.get_pool(cr.dbname).get('stock.picking')
        mod_obj = pool.get('ir.model.data')
        act_obj = pool.get('ir.actions.act_window')

        inv_type = data['form']['type']

        res = picking_obj.action_invoice_create(cr, uid, data['ids'],
                journal_id=data['form']['journal_id'], group=data['form']['group'],
                type=inv_type, context=context)

        invoice_ids = res.values()
        if not invoice_ids:
            raise wizard.except_wizard(_('Erreur'), _('La facture n\'est pas créée'))

        if inv_type == 'out_invoice':
            xml_id = 'action_invoice_tree5'
        elif inv_type == 'in_invoice':
            xml_id = 'action_invoice_tree8'
        elif inv_type == 'out_refund':
            xml_id = 'action_invoice_tree10'
        else:
            xml_id = 'action_invoice_tree12'

        result = mod_obj._get_id(cr, uid, 'account', xml_id)
        mod_id = mod_obj.read(cr, uid, result, ['res_id'], context=context)
        result = act_obj.read(cr, uid, mod_id['res_id'], context=context)
        result['res_id'] = invoice_ids
        result['context'] = context
        return result

iller_picking()

class iller_stock_move(osv.osv):
    _name = 'stock.move'
    _inherit = 'stock.move'

    def create(self, cr, uid, data, context=None):

        if not 'initial_qty' in data and 'product_qty' in data:
            data['initial_qty'] = data['product_qty']

        res = super(iller_stock_move, self).create(cr, uid, data, context=context)

        sp_obj = self.pool.get('stock.picking')
        sm_record = self.browse(cr, uid, res, context=context)

        # Si on a bien un stock move et qu'une tournée existe
        if sm_record and sm_record.picking_id.tournee_id:
            # On regarde si le produit en cours est de type prep ou decp
            if sm_record.product_id.code_affectation == 'DECP':
                self.write(cr, uid, [sm_record.id], {'poste_id':sm_record.picking_id.tournee_id.decoupe_id.id}, context=context)
            else:
                self.write(cr, uid, [sm_record.id], {'poste_id':sm_record.picking_id.tournee_id.prep_id.id}, context=context)

        return res

    _columns = {
        'poste_id': fields.many2one('iller.poste', string="Poste Prépa.", required=False),
        'num_lot': fields.char("Lot de production", size=64, required=False),
        'initial_qty': fields.float(
            string='Qté initiale',
            digits=(16,2),
        ),
        'reliquat': fields.float(
            string='Reliquat',
            digits=(16, 2),
        ),
        'state': fields.selection([('draft', 'Draft'), ('waiting', 'Waiting'), ('confirmed', 'Confirmed'), ('assigned', 'Available'), ('done', 'Done'), ('cancel', 'Cancelled')], 'Status', readonly=True, select=True),
    }

    _defaults = {
        'state': lambda *a:'assigned',
    }

    def onchange_product_id(self, cr, uid, ids, prod_id=False, loc_id=False, loc_dest_id=False, address_id=False):

        res = super(iller_stock_move, self).onchange_product_id(cr, uid, ids,
                prod_id=prod_id, loc_id=loc_id, loc_dest_id=loc_dest_id, address_id=address_id)

        # Si la quantité est modifiée
        if 'value' in res and res['value'] and 'product_qty' in res['value'] \
            and 'product_uos_qty' in res['value']:

            # On supprime les valeurs de quantité pou garder celles saisies
            del res['value']['product_qty']
            del res['value']['product_uos_qty']
            # Par défaut on utilise la même unité de mesure, on applique la règle ici
            if prod_id:
                product = self.pool.get('product.product').browse(cr, uid, [prod_id], context={})[0]
                res['value']['product_uos']  = product.uom_id and product.uom_id.id or False

        return res

    def onchange_quantity(self, cr, uid, ids, product_id=False, product_qty=0.00, product_uom=False, product_uos=False):
        res = super(iller_stock_move, self).onchange_quantity(cr, uid, ids,
                product_id=product_id, product_qty=product_qty, product_uom=product_uom, product_uos=product_uos)

        if ids:
            for move in self.browse(cr, uid, ids):
                move_init_qty = move.initial_qty
                reliquat = move.initial_qty - product_qty
                if reliquat >= 0.00:
                    res.setdefault('value', {})
                    res['value'].update({'reliquat': reliquat})
                else:
                    res['value'].update({'reliquat': 0.00})

        return res

iller_stock_move()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

