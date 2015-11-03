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
from os import walk
from os import sys as os_sys
from oerplib import error

from tests import colors
from HTMLTestRunner import HTMLTestRunner


path_for_tests = 'tests'


import_server_base_rel_dir = '/../../unifield-server/bin/'
import_server_rel_dirs = [
    'addons',
    'ir',
    'osv',
    'service',
    'tools',
    'wizard',
]


def main():
    """
    Launch all tests found in the current directory and sub-directories
    """
    c = colors.TerminalColors()
    test_dir = '%s/tests/' % path.dirname(path.realpath(__file__))

    # Prepare some values
    suite = unittest.TestSuite()
    test_modules = []
    added_paths = []

    run_only_modules = False
    if len(sys.argv) > 1:
        # In case of specific module to run
        run_only_modules = sys.argv[1:]

    print c.BGreen + 'Browsing' + c.Color_Off + ' %s directory.' % path_for_tests
    for racine, _, files in walk(path_for_tests):
        directory = path.basename(racine)
        if directory == 'tests':
            for f in files:
                if (f.startswith('test') and f.endswith('.py') and f != 'test.py'):
                    mod_name = f[:-3]
                    if not run_only_modules or \
                     (run_only_modules and mod_name in run_only_modules):
                        name = path.join(racine, f)
                        test_modules.append((name, mod_name))

    print c.BGreen + 'Import' + c.Color_Off + ' modules + instanciate them'
    for module_info in sorted(test_modules, key=lambda x: x[1]):
        module_path = path.dirname(module_info[0])
        if module_path not in sys.path:
            sys.path.append(module_path)
            added_paths.append(module_path)

        module = __import__(module_info[1])
        if 'get_test_class' in module.__dict__:
            class_type = module.get_test_class()
            print ("%s module:" % (class_type.__module__,))
            test_suite = unittest.TestSuite((unittest.makeSuite(class_type), ))
            suite.addTest(test_suite)

        if 'get_test_suite' in module.__dict__:
            suite_type = module.get_test_suite()
            print ("%s module:" % (suite_type[0].__module__,))
            for class_type in suite_type:
                test_suite = unittest.TestSuite((unittest.makeSuite(class_type), ))
                suite.addTest(test_suite)


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

def import_dirs():
    current_dir = path.dirname(path.abspath(__file__))

    os_sys.path.append(path.abspath(current_dir + import_server_base_rel_dir))
    for rd in import_server_rel_dirs:
        os_sys.path.append(path.abspath(
            current_dir + import_server_base_rel_dir + rd))


if __name__ == "__main__":
    import_dirs()
    main()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
