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

    _columns = {
        'poste_id': fields.many2one('iller.poste', string="Poste Prépa.", required=False),
    }
    def onchange_product_id(self, cr, uid, ids, prod_id=False, loc_id=False, loc_dest_id=False, address_id=False):
        if not prod_id:
            return {}
        lang = False
        if address_id:
            addr_rec = self.pool.get('res.partner.address').browse(cr, uid, address_id)
            if addr_rec:
                lang = addr_rec.partner_id and addr_rec.partner_id.lang or False
        ctx = {'lang': lang}

        product = self.pool.get('product.product').browse(cr, uid, [prod_id], context=ctx)[0]
        uos_id  = product.uos_id and product.uos_id.id or False
        result = {
            'name': product.partner_ref,
            'product_uom': product.uom_id.id,
            'product_uos_qty' : self.pool.get('stock.move').onchange_quantity(cr, uid, ids, prod_id, 1.00, product.uom_id.id, uos_id)['value']['product_uos_qty']
        }
        if uos_id:
            result['product_uos'] = uos_id
        if loc_id:
            result['location_id'] = loc_id
        if loc_dest_id:
            result['location_dest_id'] = loc_dest_id
        return {'value': result}

iller_stock_move()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

