#!/usr/bin/env python
#-*- encoding:utf-8 -*-
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

from osv import fields, osv
from tools.misc import currency
from tools.translate import _
from tools import config

class account_move(osv.osv):
    _name = "account.move"
    _inherit = "account.move"

    #
    # Validate a balanced move. If it is a centralised journal, create a move.
    #
    def validate(self, cr, uid, ids, context={}):
        if context and ('__last_update' in context):
            del context['__last_update']

        valid_moves = [] #Maintains a list of moves which can be responsible to create analytic entries

        for move in self.browse(cr, uid, ids, context):
            # Unlink old analytic lines on move_lines
            for obj_line in move.line_id:
                ###### TEMPO GROUP LINES #######
                if obj_line.analytic_account_id:
                    for obj in obj_line.analytic_lines:
                        self.pool.get('account.analytic.line').unlink(cr,uid,obj.id)

            journal = move.journal_id
            amount = 0
            line_ids = []
            line_draft_ids = []
            company_id = None
            for line in move.line_id:
                amount += line.debit - line.credit
                line_ids.append(line.id)
                if line.state == 'draft':
                    line_draft_ids.append(line.id)

                if not company_id:
                    company_id = line.account_id.company_id.id
                if not company_id == line.account_id.company_id.id:
                    raise osv.except_osv(_('Error'), _("Couldn't create move between different companies"))

                if line.account_id.currency_id:
                    if line.account_id.currency_id.id != line.currency_id.id and (line.account_id.currency_id.id != line.account_id.company_id.currency_id.id or line.currency_id):
                        raise osv.except_osv(_('Error'), _("""Couldn't create move with currency different from the secondary currency of the account "%s - %s". Clear the secondary currency field of the account definition if you want to accept all currencies.""" % (line.account_id.code, line.account_id.name)))

            # Check that the move balances, the tolerance for debit/credit must
            # be smaller than the smallest value according to price accuracy
            # (hence the +1 below)
            # Example:
            #    difference == 0.01 is OK iff price_accuracy <= 1!
            #    difference == 0.0001 is OK iff price_accuracy <= 3!
            if abs(amount) < 10 ** -(int(config['price_accuracy'])+1):
                # If the move is balanced
                # Add to the list of valid moves
                # (analytic lines will be created later for valid moves)
                valid_moves.append(move)

                # Check whether the move lines are confirmed
                
                if not len(line_draft_ids):
                    continue
                # Update the move lines (set them as valid)

                self.pool.get('account.move.line').write(cr, uid, line_draft_ids, {
                    'journal_id': move.journal_id.id,
                    'period_id': move.period_id.id,
                    'state': 'valid'
                }, context, check=False)

                account = {}
                account2 = {}
                
                if journal.type in ('purchase','sale'):

                    for line in move.line_id:
                        code = amount = 0
                        key = (line.account_id.id, line.tax_code_id.id)
                        if key in account2:
                            code = account2[key][0]
                            amount = account2[key][1] * (line.debit + line.credit)
                        elif line.account_id.id in account:
                            code = account[line.account_id.id][0]
                            amount = account[line.account_id.id][1] * (line.debit + line.credit)
                        if (code or amount) and not (line.tax_code_id or line.tax_amount):
                            self.pool.get('account.move.line').write(cr, uid, [line.id], {
                                'tax_code_id': code,
                                'tax_amount': amount
                            }, context, check=False)
                            
            elif journal.centralisation:
                # If the move is not balanced, it must be centralised...

                # Add to the list of valid moves
                # (analytic lines will be created later for valid moves)
                valid_moves.append(move)

                #
                # Update the move lines (set them as valid)
                #
                
                self._centralise(cr, uid, move, 'debit', context=context)
                self._centralise(cr, uid, move, 'credit', context=context)
                self.pool.get('account.move.line').write(cr, uid, line_draft_ids, {
                    'state': 'valid'
                }, context, check=False)
            else:
                # We can't validate it (it's unbalanced)
                # Setting the lines as draft
                self.pool.get('account.move.line').write(cr, uid, line_ids, {
                    'journal_id': move.journal_id.id,
                    'period_id': move.period_id.id,
                    #'tax_code_id': False,
                    #'tax_amount': False,
                    'state': 'draft'
                }, context, check=False)

        # Create analytic lines for the valid moves
        
        for record in valid_moves:
            self.pool.get('account.move.line').create_analytic_lines(cr, uid, [line.id for line in record.line_id], context)

        return len(valid_moves) > 0

account_move()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
