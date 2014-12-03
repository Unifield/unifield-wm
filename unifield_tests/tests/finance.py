#!/usr/bin/env python
# -*- coding: utf8 -*-
from __future__ import print_function
from unifield_test import UnifieldTest
from time import strftime
from random import randint
from oerplib import error

class FinanceTest(UnifieldTest):

    def __init__(self, *args, **kwargs):
        '''
        Include some finance data in the databases (except sync one).
        Include/create them only if they have not been already created.
        To know this, we use the key: "finance_test_class"
        '''
        super(FinanceTest, self).__init__(*args, **kwargs)

    def _hook_db_process(self, name, database):
        '''
        Check that finance data are loaded into the given database
        '''
        keyword = 'finance_test_class'
        colors = self.colors
        # If no one, do some changes on DBs
        if not self.is_keyword_present(database, keyword):
            # 00 Open periods from january to today's one
            month = strftime('%m')
            today = strftime('%Y-%m-%d')
            fy_obj = database.get('account.fiscalyear')
            period_obj = database.get('account.period')
            # Fiscal years
            fy_ids = fy_obj.search([('date_start', '<=', today), ('date_stop', '>=', today)])
            if not fy_ids:
                raise Exception('error', 'No fiscalyear found!')
            # Sort periods by number
            periods = period_obj.search([('fiscalyear_id', 'in', fy_ids), ('number', '<=', month), ('state', '=', 'created')], 0, 16, 'number')
            for period in periods:
                try:
                    period_obj.action_set_state(period, context={'state': 'draft'})
                except error.RPCError as e:
                    print(e.oerp_traceback)
                    print(e.message)
                except Exception, e:
                    raise Exception('error', str(e))
            # Write the fact that data have been checked
            database.get(self.test_module_obj_name).create({'name': keyword, 'active': True})
        return super(FinanceTest, self)._hook_db_process(name, database)

    def create_journal_entry(self, database):
        '''
        Create a journal entry (account.move) with 2 lines: 
          - an expense one (with an analytic distribution)
          - a counterpart one
        Return the move ID, expense line ID, then counterpart ID
        '''
        # Prepare some values
        move_obj = database.get('account.move')
        aml_obj = database.get('account.move.line')
        period_obj = database.get('account.period')
        journal_obj = database.get('account.journal')
        partner_obj = database.get('res.partner')
        account_obj = database.get('account.account')
        distrib_obj = database.get('analytic.distribution')
        curr_date = strftime('%Y-%m-%d')
        # Search journal
        journal_ids = journal_obj.search([('type', '=', 'purchase')])
        self.assert_(journal_ids != [], "No purchase journal found!")
        # Search period
        period_ids = period_obj.get_period_from_date(curr_date)
        # Search partner
        partner_ids = partner_obj.search([('partner_type', '=', 'external')])
        # Create a random amount
        random_amount = randint(100, 10000)
        # Create a move
        move_vals = {
            'journal_id': journal_ids[0],
            'period_id': period_ids[0],
            'date': curr_date,
            'document_date': curr_date,
            'partner_id': partner_ids[0],
            'status': 'manu',
        }
        move_id = move_obj.create(move_vals)
        self.assert_(move_id != False, "Move creation failed with these values: %s" % move_vals)
        # Create some move lines
        account_ids = account_obj.search([('is_analytic_addicted', '=', True), ('code', '=', '6101-expense-test')])
        random_account = randint(0, len(account_ids) - 1)
        vals = {
            'move_id': move_id,
            'account_id': account_ids[random_account],
            'name': 'fp_changes expense',
            'amount_currency': random_amount,
        }
        # Search analytic distribution
        distribution_ids = distrib_obj.search([('name', '=', 'DISTRIB 1')])
        distribution_id = distrib_obj.copy(distribution_ids[0], {'name': 'distribution-test'})
        vals.update({'analytic_distribution_id': distribution_id})
        aml_expense_id = aml_obj.create(vals)
        counterpart_ids = account_obj.search([('is_analytic_addicted', '=', False), ('code', '=', '401-supplier-test'), ('type', '!=', 'view')])
        random_counterpart = randint(0, len(counterpart_ids) - 1)
        vals.update({
            'account_id': counterpart_ids[random_counterpart],
            'amount_currency': -1 * random_amount,
            'name': 'fp_changes counterpart',
            'analytic_distribution_id': False,
        })
        aml_counterpart_id = aml_obj.create(vals)
        # Validate the journal entry
        move_obj.button_validate([move_id]) # WARNING: we use button_validate so that it check the analytic distribution validity/presence
        return move_id, aml_expense_id, aml_counterpart_id

    def create_account(self, database, code, account_type='other', user_type_code='specific', destination_code='OPS'):
        '''
        Create an account and send the ID
        '''
        # Prepare some values
        acc_obj = database.get('account.account')
        type_obj = database.get('account.account.type')
        ana_obj = database.get('account.analytic.account')
        destination_mandatory_types = ['expense']
        # Search user_type
        type_ids = type_obj.search([('code', '=ilike', user_type_code)])
        user_type_id = type_ids and type_ids[0] or False
        if not user_type_id:
            raise Exception("User type not found: %s" % (user_type_code))
        # Search destination (only for expense accounts)
        destination_id = False
        if user_type_code in destination_mandatory_types:
            dest_ids = ana_obj.search([('category', '=', 'DEST'), ('code', '=ilike', destination_code)])
            destination_id = dest_ids and dest_ids[0] or False
            if not destination_id:
                raise Exception("Destination not found: %s" % (destination_code))
        # Create values
        vals = {
            'name': code,
            'code': code,
            'type': account_type,
            'user_type': user_type_id,
        }
        if destination_id:
            vals.update({'default_destination_id': destination_id})
        # Create account
        try:
            res_id = acc_obj.create(vals)
        except error.RPCError, e:
            raise Exception("Account creation failed!\n%s\n\n%s", (e.message, e.oerp_traceback))
        except Exception, e:
            raise Exception('error', str(e))
        return res_id

    def create_journal(self, database, name, code, journal_type, analytic_journal_id=False, account_code=False, currency_name=False, bank_journal_id=False):
        '''
        Create a journal with given info.
        If journal type is bank/cash/cheque, it needs account_code and currency_name.
        '''
        # Some checks
        if not name or not code or not journal_type:
            raise Exception("Some info missing. Name: '%s'. Code: '%s'. Type: '%s'" % (name or '', code or '', journal_type or ''))
        # Case where journal type is bank/cash/cheque
        if journal_type in ['bank', 'cheque', 'cash']:
            if not account_code or not currency_name:
                raise Exception("Bank/Cash/Cheque journals need an account code and a currency. Account: '%s'. Currency: '%s'" % (account_code or '', currency_name or ''))
        # Bank journal ID is mandatory for cheque journal
        if journal_type == 'cheque' and not bank_journal_id:
            raise Exception("Bank journal is mandatory for cheque journals!")
        # Check that we have an analytic journal
        if not analytic_journal_id:
            aj_obj = database.get('account.analytic.journal')
            analytic_journal_type = journal_type
            if journal_type in ['bank', 'cheque']:
                analytic_journal_type = 'cash'
            aj_ids =aj_obj.search([('type', '=', analytic_journal_type)])
            self.assert_(aj_ids != [], "No analytic journal found with this type: %s. Please add an analytic journal ID instead." % journal_type)
            analytic_journal_id = aj_ids[0]
        # Prepare values
        vals = {
            'name': name,
            'code': code,
            'type': journal_type,
            'analytic_journal_id': analytic_journal_id,
        }
        if account_code:
            a_obj = database.get('account.account')
            a_ids = a_obj.search([('code', '=', account_code)])
            self.assert_(a_ids != [], "No account found for the given code: %s." % account_code)
            account_id = a_ids[0]
            vals.update({
                'default_debit_account_id': account_id,
                'default_credit_account_id': account_id,
            })
        if currency_name:
            c_obj = database.get('res.currency')
            c_ids = c_obj.search([('name', '=', currency_name)])
            self.assert_(c_ids != [], "Currency not found: %s" % currency_name)
            vals.update({'currency': c_ids[0]})
        if bank_journal_id:
            vals.update({'bank_journal_id': bank_journal_id})
        # Create the journal
        return database.get('account.journal').create(vals)

    def create_register(self, database, name, code, register_type, account_code, currency_name, bank_journal_id=False):
        '''
        Create a register in the current period.
        Return register_id and journal_id.
        '''
        # Create the journal
        j_id = self.create_journal(database, name, code, register_type, account_code=account_code, currency_name=currency_name, bank_journal_id=bank_journal_id)
        # Search the register
        reg_ids = database.get('account.bank.statement').search([('journal_id', '=', j_id)])
        r_id = False
        if reg_ids:
            r_id = reg_ids[0]
        # Return register ID, journal ID
        return r_id, j_id

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
