#!/usr/bin/env python
# -*- encoding: utf-8 -*-
################################################################################
#
#    TeMPO CONSULTING
#    Copyright (C) 2004-2009 TeMPO CONSLTING (<http://www.tempo-consulting.fr>). 
#
################################################################################

from osv import fields,osv
import pooler


class account_invoice(osv.osv):
    _name = 'account.invoice'
    _inherit = 'account.invoice'

    def finalize_invoice_move_lines(self, cr, uid, invoice_browse, move_lines):
        account_ids = {}
        lines = []
        analytic_journal = invoice_browse.journal_id.analytic_journal_id
        if not analytic_journal:
            raise osv.except_osv('Pas de journal analytique !',u"Vous devez definir un journal analytique sur le journal  '%s'!" % (invoice_browse.journal_id.name,))
        
        for l in move_lines:
            line = l[2]
            #tax_code_id currency_id analytic_account_id date date_maturity
            key = (line.get('account_id'), line.get('tax_code_id'), line.get('currency_id'), line.get('date'), line.get('date_maturity'), line.get('partner_id') )
            account_ids.setdefault(key,[]).append(line)
        for k in account_ids:
            debit = 0.00
            credit = 0.00
            tax_amount = 0.00
            amount_currency = 0.00
            name = invoice_browse.name or self.pool.get('account.account').read(cr, uid, k[0], ['name']).get('name')
            analytic_lines = []
            for line in account_ids[k]:
                debit += line.get('debit',0.00)
                credit += line.get('credit',0.00) 
                amount_currency += line.get('amount_currency', 0.00)
                tax_amount += line.get('tax_amount', 0.00)
                if line.get('analytic_lines'):
                    for ana_line in line['analytic_lines']:
                        ana_line[2]['journal_id'] = analytic_journal.id
                    analytic_lines += line['analytic_lines']
            if debit or credit:
                move_line = {
                    'debit': debit,
                    'credit': credit,
                    'amount_currency': amount_currency, 
                    'tax_amount': tax_amount,
                    'analytic_lines': analytic_lines,
                    'name': name,
                    'account_id': k[0],
                    'tax_code_id':k[1], 
                    'currency_id':k[2], 
                    'analytic_account_id': False, 
                    'date': k[3], 
                    'date_maturity':k[4], 
                    'partner_id':k[5]
                }
                lines.append((0,0,move_line))
        return lines

account_invoice()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

