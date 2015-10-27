#!/usr/bin/python
# -*- coding: utf8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2014 TeMPO Consulting, MSF. All Rights Reserved
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################


from unifield_test import UnifieldTest

class AccountTest(UnifieldTest):

    def test_010_coa(self):
        '''Check Chart of Account length'''
        ids = self.hq1c1p1.get('account.account').search([])
        self.assert_(len(ids) == 357, "Chart of Account length: %s" % len(ids))

def get_test_class():
    '''Return the class to use for tests'''
    return AccountTest

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
