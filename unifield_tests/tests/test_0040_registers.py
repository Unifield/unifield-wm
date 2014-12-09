#!/usr/bin/env python
# -*- coding: utf8 -*-
from oerplib.error import RPCError
from finance import FinanceTest
from datetime import datetime
from random import randint, choice

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
        self.partner_obj = db.get('res.partner')
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
        line_id, distrib_id = self.create_register_line(self.register_id, '63000', amount, True)
        if not line_id:
            raise Exception("No register line created.")
        # Some checks on it
        line = self.absl_obj.browse(line_id)
        # Check the line state (should be draft)
        self.assert_(line.state == 'draft', "Wrong line state (ID: %s). Should be: %s. Current: %s." % (line_id, 'draft', line.state or ''))
        # Check that no move line is attached
        move_ids = [x.id for x in line.move_ids]
        self.assert_(move_ids == [], "Move lines detected on line (ID: %s). Should not. Current: %s" % (line_id, move_ids))
        # Temp post the line
        try:
            self.absl_obj.posting([line.id], 'temp')
        except RPCError as e:
            raise Exception('ERROR WHILE %s POSTING LINE:\n%s\n\n%s' % ('temp', e.message, e.oerp_traceback))
        line = self.absl_obj.browse(line_id) # need to browse register line to update record values
        # Check state, move lines presence and journal entry state
        self.assert_(line.state == 'temp', "Wrong line state (ID: %s). Should be: %s. Current: %s" % (line_id, 'temp', line.state or ''))
        move_ids = [x.id for x in line.move_ids]
        self.assert_(move_ids != [], "No move lines detected on line (ID: %s)." % (line_id))
        for move in line.move_ids:
            self.assert_(move.state == 'draft', "Register line (ID: %s) have journal entry (ID: %s) in wrong state. Should be draft. Current: %s." % (line.id, move.id, move.state))
        # Hard post the line
        try:
            self.absl_obj.posting([line.id], 'hard')
        except RPCError as e:
            raise Exception('ERROR WHILE %s POSTING LINE:\n%s\n\n%s' % ('hard', e.message, e.oerp_traceback))
        line = self.absl_obj.browse(line_id) # need to browse register line to update record values
        move_ids = [x.id for x in line.move_ids]
        # Check state, move lines presence and journal entry state
        self.assert_(line.state == 'hard', "Wrong line state (ID: %s). Should be: %s. Current: %s" % (line.id, 'hard', line.state))
        for move in line.move_ids:
            self.assert_(move.state == 'posted', "Register line (ID: %s) have journal entry (ID: %s) in wrong state. Should be posted. Current: %s." % (line.id, move.id, move.state))

    def test_020_direct_expense(self):
        """A direct expense is a register expense line with a supplier 3RD party that generates a supplementary Journal Entry"""
        # Prepare some values
        amount = -1 * randint(1, 10000)
        partner_ids = self.partner_obj.search([('supplier', '=', True)])
        self.assert_(partner_ids != [], "No partner found!")
        partner_id = choice(partner_ids)
        # Create the direct expense
        line_id, distrib_id = self.create_register_line(self.register_id, '61000', amount, True, False, False, partner_id)
        if not line_id:
            raise Exception("No register line created.")
        # Some checks on it
        line = self.absl_obj.browse(line_id)
        move_ids = [x.id for x in line.move_ids]
        self.assert_(line.state == 'draft', "Wrong line state (ID: %s). Should be: %s. Current: %s" % (line_id, 'draft', line.state or ''))
        self.assert_(move_ids == [], "Move lines detected on line (ID: %s). Should not. Current: %s" % (line_id, move_ids))
        # Temp post the line
        try:
            self.absl_obj.posting([line.id], 'temp')
        except RPCError as e:
            raise Exception('ERROR WHILE %s POSTING LINE:\n%s\n\n%s' % ('temp', e.message, e.oerp_traceback))
        line = self.absl_obj.browse(line_id) # need to browse register line to update record values
        move_ids = [x.id for x in line.move_ids]
        # Check state, move lines presence and journal entry state
        self.assert_(line.state == 'temp', "Wrong line state (ID: %s). Should be: %s. Current: %s" % (line_id, 'temp', line.state or ''))
        # Hard post the line
        try:
            self.absl_obj.posting([line.id], 'hard')
        except RPCError as e:
            raise Exception('ERROR WHILE %s POSTING LINE:\n%s\n\n%s' % ('hard', e.message, e.oerp_traceback))
        line = self.absl_obj.browse(line_id) # need to browse register line to update record values
        move_ids = [x.id for x in line.move_ids]
        # Check state, move lines presence and journal entry state
        self.assert_(line.state == 'hard', "Wrong line state (ID: %s). Should be: %s. Current: %s" % (line.id, 'hard', line.state))
        for move in line.move_ids:
            self.assert_(move.state == 'posted', "Register line (ID: %s) have journal entry (ID: %s) in wrong state. Should be posted. Current: %s." % (line.id, move.id, move.state))
        # Direct expense generates a second Journal Entry with same amount, partner and with reconciled lines. So we search if these lines exists.
        # As the system is not well designed (with move_ids field in register lines) we have to make a search in move lines instead of using move_ids field that doesn't contain all linked move_ids.
        move_line_ids = self.p1.get('account.move.line').search([('name', '=', line.name), ('statement_id', '=', line.statement_id.id), ('partner_id', '=', partner_id), ('is_reconciled', '=', True)])
        self.assert_(move_line_ids != [], "No move lines found for the direct expense (ID: %s)" % line.id)
        self.assert_(len(move_line_ids) == 2, "Problem occured for register line '%s' (ID: %s). Should find 2 reconciled journal items. Found: %s." % (line.name, line.id, len(move_line_ids)))

def get_test_class():
    '''Return the class to use for tests'''
    return RegisterTest

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
