#!/usr/bin/env python
# -*- coding: utf8 -*-
from oerplib.error import RPCError
from datetime import datetime
from finance import FinanceTest

class PeriodTest(FinanceTest):

    def setUp(self):
        '''
        Initialize some accounting objects
        '''
        # Prepare some values
        db = self.p1
        # Objects
        self.period_obj = db.get('account.period')
        self.period_wiz_obj = db.get('account.period.create')
        self.fy_obj = db.get('account.fiscalyear')

    def tearDown(self):
        '''
        Clean up database by deleting created periods/fiscalyears.
        '''
        # Search next periods
        self.period_to_delete = []
        self.fy_to_delete = []
        start = str(datetime.now().year+1) + "-01-01"
        fy_ids = self.fy_obj.search([('date_start', '=', start)])
        if fy_ids:
          p_ids = self.period_obj.search([('fiscalyear_id', 'in', fy_ids)])
          if p_ids:
              self.period_obj.unlink(p_ids)
          self.fy_obj.unlink(fy_ids)

    def test_010_period_wizard_creation(self):
        '''Create and check next fiscalyear/periods via Period Creation Wizard'''
        # Create next fiscalyear with periods
        wiz_id = self.period_wiz_obj.create({'fiscalyear': 'next'})
        self.period_wiz_obj.account_period_create_periods([wiz_id])
        # Searching March period of next month
        march_start = str(datetime.now().year+1) + "-03-01"
        march_stop = str(datetime.now().year+1) + "-03-31"
        march_ids = self.period_obj.search([
            ('date_start', '=', march_start),
            ('date_stop', '=', march_stop),
            ('special', '=', False),
            ('state', '=', 'created')
        ])
        self.assert_(march_ids != False, "March period for next year not found!")
        # Search Period 14
        start = str(datetime.now().year+1) + "-12-01"
        stop = str(datetime.now().year+1) + "-12-31"
        end_ids = self.period_obj.search([
            ('date_start', '=', start),
            ('date_stop', '=', stop),
            ('special', '=', True),
            ('state', '=', 'created')
        ])
        self.assert_(end_ids != False, "Period 14 for next year not found!")

def get_test_class():
    '''Return the class to use for tests'''
    return PeriodTest

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
