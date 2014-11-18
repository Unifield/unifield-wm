#!/usr/bin/env python
# -*- coding: utf8 -*-
from unifield_test import UnifieldTest
from oerplib.error import RPCError
from datetime import datetime
from dateutil.relativedelta import relativedelta

class AccountTest(UnifieldTest):

    def setUp(self):
        '''
        Initialize some accounting objects
        '''
        self.ana_account_to_delete = []
        db = self.p1
        self.acc_obj = db.get('account.account')
        self.ana_obj = db.get('account.analytic.account')

    def tearDown(self):
        '''
        Clean up database
        '''
        if self.ana_account_to_delete:
            self.ana_obj.unlink(self.ana_account_to_delete)

    def test_010_coa(self):
        '''Check Chart of Account length'''
        ids = self.acc_obj.search([])
        self.assert_(len(ids) == 357, "Chart of Account length: %s" % len(ids))

    def test_020_analytic_creation(self):
        '''Check activation date is 3 month ago for ANA account'''
        nextDate = '%s-01-01' % (datetime.now().year + 2)
        vals = {
            'name': 'Test Account',
            'date': nextDate,
        }
        try:
            ana_id = self.ana_obj.create(vals)
        except RPCError, e:
            raise Exception("%s\n\n%s", (e.message, e.oerp_traceback))
        # Do not forget to delete this account after tests
        self.ana_account_to_delete.append(ana_id)
        # Check account data after creation process
        account = self.ana_obj.browse(ana_id)
        previousDate = (datetime.today() + relativedelta(months=-3)).strftime('%Y-%m-%d')
        self.assert_(str(account.date_start) == previousDate, "Wrong date: %s (%s). Should be: %s (%s)" % (account.date_start, type(account.date_start), previousDate, type(previousDate)))

    def test_100_acoa(self):
        '''Print Analytic Chart of Account through the wizard'''
        # Get report object
        wiz_obj = self.p1.get('account.analytic.chart')
        wiz_id = wiz_obj.create({ 'show_inactive': True, }, {})
        res = wiz_obj.button_export([wiz_id], {})
        # Check wizard result
        self.assert_(res.get('type', False) == 'ir.actions.report.xml', "Wrong report type")
        # Launch report
        # TODO: find a way to launch a report
#        report_res = self.p1.report('account_analytic_chart_export', 'account.analytic.account', res.get('datas').get('ids'), 'webkit', {'show_inactive': True})

def get_test_class():
    '''Return the class to use for tests'''
    return AccountTest

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
