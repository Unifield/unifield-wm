#!/usr/bin/env python
# -*- coding: utf8 -*-
from unifield_test import UnifieldTest

class AccountTest(UnifieldTest):

    def test_010_coa(self):
        '''Check Chart of Account length'''
        ids = self.p1.get('account.account').search([])
        self.assert_(len(ids) == 357, "Chart of Account length: %s" % len(ids))

    def test_020_acoa(self):
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
