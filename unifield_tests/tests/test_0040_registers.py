#!/usr/bin/env python
# -*- coding: utf8 -*-
from oerplib.error import RPCError
from finance import FinanceTest
from datetime import datetime
from random import randint

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
        amount = -1 * randint(1, 10000)
        line_id = self.create_register_line(self.register_id, '63000', amount)
        if not line_id:
            raise Exception("No register line created.")
        # Some checks on it
        line = self.absl_obj.browse(line_id)
        # Check the line state (should be draft)
        self.assert_(line.state == 'draft', "Wrong line state (ID: %s). Should be: %s. Current: %s." % (line_id, 'draft', line.state or ''))
        # Check that no move line is attached
        move_ids = [x.id for x in line.move_ids]
        self.assert_(move_ids == [], "Move lines detected on line (ID: %s). Should not. Current: %s" % (line_id, move_ids))
        # Attach a distribution analytic on it
        distrib_id = self.generate_analytic_distribution(self.p1)
        self.absl_obj.write([line.id], {'analytic_distribution_id': distrib_id}, {})
        # Temp post the line
        try:
            self.absl_obj.posting([line.id], 'temp')
        except RPCError, e:
            raise Exception('ERROR WHILE %s POSTING LINE:\n%s\n\n%s' % ('temp', e.message, e.oerp_traceback))
        # Check state, move lines presence and journal entry state
        self.assert_(line.state == 'temp', "Wrong line state (ID: %s). Should be: %s. Current: %s" % (line_id, 'temp', line.state or ''))
        move_ids = [x.id for x in line.move_ids]
        self.assert_(move_ids != [], "No move lines detected on line (ID: %s)." % (line_id))

def get_test_class():
    '''Return the class to use for tests'''
    return RegisterTest

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
