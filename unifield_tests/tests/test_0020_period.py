#!/usr/bin/env python
# -*- coding: utf8 -*-
from oerplib.error import RPCError
from datetime import datetime
from finance import FinanceTest
import unittest

class PeriodTest(FinanceTest):

    def setUp(self):
        '''
        Initialize some accounting objects
        '''
        # Prepare some values
        db = self.p1
        self.next_year = str(datetime.now().year+1)
        # Objects
        self.period_obj = db.get('account.period')
        self.period_wiz_obj = db.get('account.period.create')
        self.fy_obj = db.get('account.fiscalyear')

    @classmethod
    def tearDownClass(self):
        '''
        Clean up database by deleting created periods/fiscalyears.
        '''
        # Prepare some values
        self.period_to_delete = []
        self.fy_to_delete = []
        start = str(datetime.now().year+1) + "-01-01"
        db = self.db.get('p1')
        fy_obj = db.get('account.fiscalyear')
        period_obj = db.get('account.period')
        # Search next periods
        fy_ids = fy_obj.search([('date_start', '=', start)])
        if fy_ids:
          p_ids = period_obj.search([('fiscalyear_id', 'in', fy_ids)])
          if p_ids:
              period_obj.unlink(p_ids)
          fy_obj.unlink(fy_ids)

    def test_010_period_wizard_creation(self):
        '''Create and check next fiscalyear/periods via Period Creation Wizard'''
        # Create next fiscalyear with periods
        wiz_id = self.period_wiz_obj.create({'fiscalyear': 'next'})
        self.period_wiz_obj.account_period_create_periods([wiz_id])
        # Searching March period of next month
        march_start = self.next_year + "-03-01"
        march_stop = self.next_year + "-03-31"
        march_ids = self.period_obj.search([
            ('date_start', '=', march_start),
            ('date_stop', '=', march_stop),
            ('special', '=', False),
            ('state', '=', 'created')
        ])
        self.assert_(march_ids != False, "March period for next year not found!")
        # Search Period 14
        start = self.next_year + "-12-01"
        stop = self.next_year + "-12-31"
        end_ids = self.period_obj.search([
            ('date_start', '=', start),
            ('date_stop', '=', stop),
            ('special', '=', True),
            ('state', '=', 'created')
        ])
        self.assert_(end_ids != False, "Period 14 for next year not found!")

    def test_020_period_states(self):
        '''Check all states from the january period from next year. Then attempt to close March (forbidden)'''
        # Search first January period
        jan_start = self.next_year + "-01-01"
        jan_ids = self.period_obj.search([('date_start', '=', jan_start)])
        self.assert_(jan_ids != [], "No period found for January %s" % self.next_year)
        self.assert_(len(jan_ids) == 1, "Too many january period found: %s." % len(jan_ids))
        period_id = jan_ids[0]
        # Attempt to change state of January period
        for state in ['draft', 'field-closed', 'mission-closed', 'done']:
            period = self.period_obj.browse(period_id)
            try:
                self.period_obj.action_set_state(jan_ids, {'state': state})
            except RPCError, e:
                raise Exception('Change January period failed! Should be: %s. Current: %s\n%s\n\n%s' % (state, period.state, e.message, e.oerp_traceback))
            # Refresh period content to test its current state
            period = self.period_obj.browse(period_id)
            # Check new state
            self.assert_(period.state == state, "Wrong period state for january. Should be: %s. Current: %s." % (state, period.state))
        # Attempt to open March period: should be forbidden!
        march_start = self.next_year + "-03-01"
        march_ids = self.period_obj.search([('date_start', '=', march_start)])
        self.assert_(march_ids != [], "No period found for January %s" % self.next_year)
        self.assert_(len(march_ids) == 1, "Too many march period found: %s" % len(march_ids))
        period_id = march_ids[0]
        try:
            self.period_obj.action_set_state([march_ids], {'state': 'open'})
            self.AssertTrue(False, "You should not be allowed to open march period!")
        except RPCError, e:
            pass # all is OK because we're not allowed to open march period. System should return an RPCError, which make our test valid.

def get_test_class():
    '''Return the class to use for tests'''
    return PeriodTest

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
