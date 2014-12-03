#!/usr/bin/env python
# -*- coding: utf8 -*-
from oerplib.error import RPCError
from finance import FinanceTest
from datetime import datetime

class JournalTest(FinanceTest):

    def setUp(self):
        '''
        Initialize some accounting objects
        '''
        # Prepare some values
        db = self.p1
        self.journal_to_delete = []
        # Objects
        self.a_obj = db.get('account.account')
        self.j_obj = db.get('account.journal')
        self.reg_obj = db.get('account.bank.statement') # Register
        self.aj_obj = db.get('account.analytic.journal')
        self.type_obj = db.get('account.account.type')
        self.cur_obj = db.get('res.currency')

    def tearDown(self):
        '''Delete created journals (and their linked registers)'''
        if self.journal_to_delete:
            for journal in self.j_obj.browse(self.journal_to_delete):
                register_ids = self.reg_obj.search([('journal_id', '=', journal.id)])
                if register_ids:
                    # deleting a register need a specific context
                    self.reg_obj.unlink(register_ids, {'from': 'journal_deletion'})
            self.j_obj.unlink(self.journal_to_delete)

    def create_cash_journal(self, name='Cash Journal Test', currency_name='EUR'):
        """Create a journal which type is 'cash'"""
        # Search default cash account
        type_ids = self.type_obj.search([('code', '=', 'cash')])
        self.assert_(type_ids != [], "No cash account type found!")
        a_ids = self.a_obj.search([('type', '=', 'liquidity'), ('user_type', 'in', type_ids)])
        self.assert_(a_ids != [], "No cash account found!")
        account_id = a_ids[0]
        code = self.a_obj.browse(account_id).code
        # Create the journal
        j_id = self.create_journal(self.p1, name, 'CSHEUR', 'cash', account_code=code, currency_name=currency_name)
        return j_id

    def test_010_creation(self):
        '''Create a cash/pur journal and check that a register exists (or not)'''
        # Prepare some values
        journal_name = "Cash Journal EUR"
        j_id = self.create_cash_journal(journal_name, 'EUR')
        # Add it to journal to clean up after tests
        self.journal_to_delete.append(j_id)
        # Check data
        journal = self.j_obj.browse(j_id)
        self.assert_(journal.allow_date is False, "Allow date should be False. Current: %s" % journal.allow_date)
        self.assert_(journal.centralisation is False, "Centralisation should be False. Current: %s" % journal.centralisation)
        self.assert_(journal.entry_posted is False, "Entry posted should be False. Current: %s" % journal.entry_posted)
        self.assert_(journal.update_posted is True, "Update posted should be True. Current: %s" % journal.update_posted)
        self.assert_(journal.group_invoice_lines is False, "Group invoice lines should be False. Current: %s" % journal.group_invoice_lines)
        # Check that a register have been created
        reg_ids = self.reg_obj.search([('journal_id', '=', j_id)])
        self.assert_(reg_ids != [], "No register found after journal's creation.")
        self.assert_(len(reg_ids) == 1, "More than one register found for the new created cash journal!")
        register_id = reg_ids[0]
        register = self.reg_obj.browse(register_id)
        self.assert_(register.name == journal_name, "Wrong cash register name. Expected: %s. Current: %s" % (journal_name, register.name))
        self.assert_(register.currency.id == journal.currency.id, "Wrong cash register currency. Expected: %s. Current: %s" % ("EUR", register.currency.name))
        # Check that a normal journal doesn't generate any new register
        all_register_ids = self.reg_obj.search([])
        purchase_journal_id = self.create_journal(self.p1, "Purchase Journal TEST", 'PURTEST', 'purchase', account_code=False)
        self.journal_to_delete.append(purchase_journal_id)
        new_all_register_ids = self.reg_obj.search([])
        self.assert_(len(all_register_ids) == len(new_all_register_ids), "The purchase journal creation seems to have generated registers. It should not.")

def get_test_class():
    '''Return the class to use for tests'''
    return JournalTest

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
