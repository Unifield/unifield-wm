#!/usr/bin/env python
# -*- coding: utf8 -*-
from oerplib.error import RPCError
from datetime import datetime
from dateutil.relativedelta import relativedelta
from finance import FinanceTest

class AccountTest(FinanceTest):

    def setUp(self):
        '''
        Initialize some accounting objects
        '''
        # Prepare some values
        self.ana_account_to_delete = []
        self.account_to_delete = []
        db = self.p1
        # Objects
        self.acc_obj = db.get('account.account')
        self.ana_obj = db.get('account.analytic.account')
        self.type_obj = db.get('account.account.type')
        self.dest_link_obj = db.get('account.destination.link')

    def tearDown(self):
        '''
        Clean up database by deleting created accounts.
        NB: this check that we can delete accounts.
        '''
        if self.ana_account_to_delete:
            self.ana_obj.unlink(self.ana_account_to_delete)
        if self.account_to_delete:
            for account in self.acc_obj.browse(self.account_to_delete):
                if account.destination_ids:
                    analytic_ids = [x.id for x in account.destination_ids]
                    to_delete = self.dest_link_obj.search([('account_id', '=', account.id), ('destination_id', 'in', analytic_ids)])
                    self.dest_link_obj.unlink(to_delete)
                self.acc_obj.unlink([account.id])

    def test_010_coa(self):
        '''Check Chart of Account length'''
        ids = self.acc_obj.search([])
        self.assert_(len(ids) == 357, "Chart of Account length: %s" % len(ids))

    def test_020_analytic_creation(self):
        '''Check activation date is 3 month ago for ANA account'''
        # Prepare some values
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

    def test_020_account_creation(self):
        '''Check payable account creation then expense one'''
        # Payable account
        try:
            payable_id = self.create_account(self.p1, '123456-test', 'other', 'payable')
        except RPCError, e:
            raise Exception('%s\n\n%s' % (e.message, e.oerp_traceback))
        # Do not forget to delete this account after tets
        self.account_to_delete.append(payable_id)
        # Expense account
        try:
            expense_id = self.create_account(self.p1, '6xxx-test', 'other', 'expense', 'SUP')
        except RPCError, e:
            raise Exception('%s\n\n%s' % (e.message, e.oerp_traceback))
        self.account_to_delete.append(expense_id)

    def test_100_acoa(self):
        '''Print Analytic Chart of Account through the wizard'''
        # Get report object
        wiz_obj = self.p1.get('account.analytic.chart')
        wiz_id = wiz_obj.create({ 'show_inactive': True, }, {})
        res = wiz_obj.button_export([wiz_id], {})
        # Check wizard result
        self.assert_(res.get('type', False) == 'ir.actions.report.xml', "Wrong report type")
        # Launch report. This use the name given in the parser declaration in the .py file in Unifield
        try:
            new_context = dict(self.p1.context)
            new_context.update({
                'show_inactive': True,
                'display_fp': True,
            })
            report_res = self.p1.report('account.analytic.chart.export', 'account.analytic.account', res.get('datas').get('ids'), 'webkit', new_context)
        except RPCError, e:
            raise Exception("Analytic chart of account report failed!\n%s\n\n%s" % (e.message, e.oerp_traceback))
        # report_res is the absolute path in the system where the result file is. If you want to make some test on it, you can.

def get_test_class():
    '''Return the class to use for tests'''
    return AccountTest

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
