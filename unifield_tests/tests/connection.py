#!/usr/bin/env python
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

from __future__ import print_function
from ConfigParser import ConfigParser
from oerplib.oerp import OERP
import os
import time

class UnifieldTestConfigParser(ConfigParser):
    '''
    Special ConfigParser for Unifield tests battery
    '''

    def read(self, filenames=[]):
        '''
        Override readfp() method to add the config file path
        '''
        conf_file = 'unifield.config'
        if not os.path.exists(conf_file):
            raise NameError('unifield.config file not found!')
        return ConfigParser.read(self, [conf_file])

class XMLRPCConnection(OERP):
    '''
    XML-RPC connection class to connect with OERP
    '''

    def __init__(self, db_name, port, url, uid, pwd):
        '''
        Constructor
        '''
        # OpenERP connection
        super(XMLRPCConnection, self).__init__(
            server=url,
            protocol='xmlrpc',
            port=port,
            timeout=3600
        )
        # Login initialization
        try:
            self.login(uid, pwd, db_name)
            print ('%s :: Connection...' % db_name)
        except Exception as e:
            if e.message.startswith('ServerUpdate:'):
                time.sleep(5)
                self.login(uid, pwd, db_name)
        self.db_name = db_name

if __name__ == '__main__':
    c = XMLRPCConnection('HQ1C1P1')
    if c:
        print("Connection succeeded")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
