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
            # open register
            self.open_register(db, [self.register_id])
        else:
            self.journal_id = j_ids[0]
            register_ids = self.reg_obj.search([('journal_id', '=', self.journal_id)])
            self.register_id = register_ids[0]
            self.open_register(db, [self.register_id])

    def test_010_direct_payment(self):
        """Direct payment: a register line with an expense account and WITHOUT 3RD PARTY."""
        # Create the direct payment
        self.create_register_line(self.register_id, '63000', '333')

def get_test_class():
    '''Return the class to use for tests'''
    return RegisterTest

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
