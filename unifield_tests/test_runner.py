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

import unittest
import sys

from os import path
from oerplib import error

from tests import colors
from HTMLTestRunner import HTMLTestRunner


def main():
    """
    Launch all tests found in the current directory and sub-directories
    """
    c = colors.TerminalColors()
    test_dir = '%s/tests/' % path.dirname(path.realpath(__file__))

    # Prepare some values
    loader = unittest.TestLoader()

    if len(sys.argv) > 1:
        # In case of specific module to run
        specific_suites = []
        for pattern in sys.argv[1:]:
            specific_suites.append(loader.discover(test_dir, pattern='%s.py' % pattern))
        suite = unittest.TestSuite(tuple(specific_suites))
    else:
        # Load all tests
        suite = loader.discover(test_dir)

    # Create a file for the output result
    output = file('output.html', 'wb')

    # Run tests
    campaign = HTMLTestRunner(
        stream=output,
        verbosity=2,
        title='Unifield tests',
        description='A suite of Unifield tests',
    )
    print 'Launch UnifieldTest ' + c.BGreen + 'Campaign' + c.Color_Off
    print '----------------------------\n'
    print 'Note: 1 point represents a test. F means Fail. E means Error.'
    try:
        campaign.run(suite)
    except error.RPCError as e:
        print e.oerp_traceback
        print e.message


if __name__ == "__main__":
    main()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
