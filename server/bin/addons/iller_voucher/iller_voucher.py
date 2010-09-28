#!/usr/bin/env python
# -*- coding: UTF8 -*-

from osv import osv
from osv import fields
import time


class voucher_move_line(osv.osv):
        _name = 'account.voucher.move.line'
        _description = 'Lignes d\'écriture pour une ligne de souche'

        def _get_amount(self, cursor, user, context=None):
            return context.get('amount', 0.0)

        def compute_total_entries(self, cr, uid, ids, context={}):
            amount = 0.00
            for line in self.browse(cr, uid, ids):
                for l in line.move_line_ids:
                    amount += l.debit
            self.write(cr, uid, ids, {'total_entries': amount})
            return True

        def _get_balance(self, cr, uid, ids, field_name, arg, context={}):
            balance = 0.00
            v = {}
            for id in self.browse(cr, uid, ids):
                v[id.id] = id.total_entries - id.amount

            return v


        def name_get(self, cr, uid, ids, context={}):
            res = []
            for move in self.browse(cr, uid, ids):
                res.append((move.id, '[%.2f]' %move.total_entries))

            return res

        _columns = {
            'name': fields.char(size=64, string='Nom'),
            'amount': fields.float(digits=(16,2), string='Total paiement',
                                                                readonly=True),
            'voucher_line_id': fields.many2one('account.voucher.line', 
                                        string='Ligne de souche'),
            'move_line_ids': fields.many2many('account.move.line', 
                                              'voucher_move_line_rel',
                                              'voucher_line_id', 'move_line_id',
                                              string='Lignes d\'écriture'),
            'total_entries': fields.float(digits=(16,2), 
                                string='Total des écritures', readonly=True),
            'balance': fields.function(_get_balance, type='float', method=True, 
                                string='Balance'),
        }

        _defaults = {
            'amount': _get_amount,
        }


        def onchange_move_lines(self, cr, uid, ids, move_lines, total_entries):
            total_entries = 0.00
            for line in self.pool.get('account.move.line').browse(cr, uid, move_lines[0][2]):
                total_entries += line.debit

            return {'value': {'total_entries': total_entries}}


voucher_move_line()


class voucher_line(osv.osv):
    _name = 'account.voucher.line'
    _inherit = 'account.voucher.line'

    _columns = {
        'voucher_move_id': fields.many2one('account.voucher.move.line',
                                                string='Lignes d\'écritures'),
    }

voucher_line()


class account_voucher(osv.osv):
    _name = 'account.voucher'
    _inherit = 'account.voucher'

    def action_move_line_create(self, cr, uid, ids, *args):
        rec_line = []
        for inv in self.browse(cr, uid, ids):
            if inv.move_id:
                continue
            company_currency = inv.company_id.currency_id.id

            line_ids = self.read(cr, uid, [inv.id], ['payment_ids'])[0]['payment_ids']
            ils = self.pool.get('account.voucher.line').read(cr, uid, line_ids)

            iml = self._get_analytic_lines(cr, uid, inv.id)

            diff_currency_p = inv.currency_id.id <> company_currency

            total = 0
            if inv.type in ('pay_voucher', 'journal_voucher', 'rec_voucher','cont_voucher','bank_pay_voucher','bank_rec_voucher','journal_sale_vou','journal_pur_voucher'):
                ref = inv.reference
            else:
                ref = self._convert_ref(cr, uid, inv.number)
                
            date = inv.date
            total_currency = 0
            acc_id = None
            for i in iml:
                partner_id=i['partner_id']
                acc_id = i['account_id']    
                if inv.currency_id.id != company_currency:
                    i['currency_id'] = inv.currency_id.id
                    i['amount_currency'] = i['amount']
                else:
                    i['amount_currency'] = False
                    i['currency_id'] = False
                if inv.type in ('rec_voucher','bank_rec_voucher','journal_pur_voucher','journal_voucher'):
                    total += i['amount']
                    total_currency += i['amount_currency'] or i['amount']
                    i['amount'] = - i['amount']
                else:
                    total -= i['amount']
                    total_currency -= i['amount_currency'] or i['amount']

            name = inv['name'] or '/'
            totlines = False

            iml.append({
                'type': 'dest',
                'name': name,
                'amount': total or False,
                'account_id': acc_id,
                'amount_currency': diff_currency_p \
                        and total_currency or False,
                'currency_id': diff_currency_p \
                        and inv.currency_id.id or False,
                'ref': ref,
                'partner_id':partner_id or False,
            })

            date = inv.date
            inv.amount=total

            line = map(lambda x:(0,0,self.line_get_convert(cr, uid, x,date, context={})) ,iml)
            an_journal_id=inv.journal_id.analytic_journal_id.id
            journal_id = inv.journal_id.id
            
            journal = self.pool.get('account.journal').browse(cr, uid, journal_id)
            if journal.sequence_id:
                name = self.pool.get('ir.sequence').get_id(cr, uid, journal.sequence_id.id)

            move = {
                'name' : name, 
                'journal_id': journal_id, 
                'type' : inv.type,
                'narration' : inv.narration
            }
            if inv.period_id:
                move['period_id'] = inv.period_id.id
                for i in line:
                    i[2]['period_id'] = inv.period_id.id
            move_id = self.pool.get('account.move').create(cr, uid, move)
            ref = move['name']
            amount=0.0
            
            #create the first line our self
            move_line = {
                'name': inv.name,
                'debit': False,
                'credit':False,
                'account_id': inv.account_id.id or False,
                'move_id':move_id ,
                'journal_id':journal_id ,
                'period_id':inv.period_id.id,
                'partner_id': False,
                'ref': ref, 
                'date': inv.date
            }
            if inv.type in ('rec_voucher', 'bank_rec_voucher', 'journal_pur_voucher', 'journal_voucher'):
                move_line['debit'] = inv.amount
            else:
                move_line['credit'] = inv.amount * (-1)
            self.pool.get('account.move.line').create(cr, uid, move_line)
            
            for line in inv.payment_ids:
                    
                move_line = {
                    'name':line.name,
                     'debit':False,
                     'credit':False,
                     'account_id':line.account_id.id or False,
                     'move_id':move_id ,
                     'journal_id':journal_id ,
                     'period_id':inv.period_id.id,
                     'partner_id':line.partner_id.id or False,
                     'ref':ref, 
                     'date':inv.date
                 }
                
                if line.type == 'dr':
                    move_line['debit'] = line.amount or False
                    amount=line.amount
                elif line.type == 'cr':
                    move_line['credit'] = line.amount or False
                    amount=line.amount * (-1)
                
                ml_id=self.pool.get('account.move.line').create(cr, uid, move_line)

                rec_line.append(ml_id)
                for invoice_mv_line in line.voucher_move_id.move_line_ids:
                    rec_line.append(invoice_mv_line.id)

                if inv.narration:
                    line.name=inv.narration
                else:
                    line.name=line.name
                
                if line.account_analytic_id:
                    an_line = {
                         'name':line.name,
                         'date':inv.date,
                         'amount':amount,
                         'account_id':line.account_analytic_id.id or False,
                         'move_id':ml_id,
                         'journal_id':an_journal_id ,
                         'general_account_id':line.account_id.id,
                         'ref':ref
                     }
                    self.pool.get('account.analytic.line').create(cr,uid,an_line)
                
            self.write(cr, uid, [inv.id], {'move_id': move_id})
            obj=self.pool.get('account.move').browse(cr, uid, move_id)

            self.pool.get('account.move.line').reconcile_partial(cr, uid, rec_line, 'manual', context={})
            
            for line in obj.line_id :
                cr.execute('insert into voucher_id (account_id,rel_account_move) values (%d, %d)',(int(ids[0]),int(line.id)))
                
        return True

account_voucher()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

