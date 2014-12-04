#!/usr/bin/env python
# -*- coding: utf8 -*-
from oerplib.error import RPCError
from finance import FinanceTest
from datetime import datetime

class RegisterTest(FinanceTest):

    def setUp(self):
        '''
        Initialize some accounting objects
        '''
        # Prepare some values
        db = self.p1
        # Objects
        self.a_obj = db.get('account.account')
        self.j_obj = db.get('account.journal')
        self.reg_obj = db.get('account.bank.statement') # Register
        self.absl_obj = db.get('account.bank.statement.line') # Register Line
        # Check that the register used for test already exists (check journal)
        j_ids = self.j_obj.search([('type', '=', 'bank'), ('code', '=', 'BNKCHF')])
        if not j_ids:
            register_id, journal_id = self.create_register(db, 'Banktest in CHF', 'BNKCHF', 'bank', '10200', 'CHF')
            self.journal_id = journal_id
            self.register_id = register_id
        else:
            self.journal_id = j_ids[0]
            register_ids = self.reg_obj.search([('journal_id', '=', self.journal_id)])
            self.register_id = register_ids[0]

    def create_register_line(self, register_id, code, amount, date=False, document_date=False, third_partner_id=False, third_employee_id=False, third_journal_id=False):
        """Create a register line with the given account code and amount. Optionnaly third party"""
        # Check register_id presence
        if not register_id:
            raise Exception("Register ID is missing.")
        register = self.reg_obj.browse(register_id)
        # Check account code
        code_ids = self.a_obj.search(['|', ('name', 'ilike', code), ('code', 'ilike', code)])
        if len(code_ids) != 1:
            raise Exception("Error searching for this account code: %s. Need %s codes." % (code, len(code_ids) > 1 and 'less' or 'more'))
        account_id = code_ids[0]
        # Check dates
        if not date:
            date_start = register.period_id.date_start or False
            date_stop = register.period_id.date_stop or False
            if not date_start or not date_stop:
                raise Exception("No date found for the period %s." % register.period_id.name)
            random_date = self.random_date(datetime.strptime(str(date_start), '%Y-%m-%d'), datetime.strptime(str(date_stop), '%Y-%m-%d'))
            date = datetime.strftime(random_date, '%Y-%m-%d')
        if not document_date:
            document_date = date
        # Prepare some values
        vals = {
            'statement_id': register_id,
            'account_id': account_id,
            'document_date': document_date,
            'date': date,
            'amount': amount,
        }
        if third_partner_id:
            vals.update({'partner_id': third_partner_id})
        if third_employee_id:
            vals.update({'employee_id': third_employee_id})
        if third_journal_id:
            vals.update({'transfer_journal_id': third_journal_id})
        return self.absl_obj.create(vals)

    def test_010_direct_payment(self):
        """Direct payment: a register line with an expense account and WITHOUT 3RD PARTY."""
        # Create the direct payment
        self.create_register_line(self.register_id, '63000', '333')

def get_test_class():
    '''Return the class to use for tests'''
    return RegisterTest

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
