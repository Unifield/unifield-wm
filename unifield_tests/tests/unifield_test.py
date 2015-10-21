#!/usr/bin/env python
# -*- coding: utf8 -*-
'''
Created on Feb 28, 2014

@author: qt
Modified by 'od' on 2014 March, the 11th
'''
from __future__ import print_function
import unittest
from connection import XMLRPCConnection as XMLConn
from connection import UnifieldTestConfigParser
from colors import TerminalColors

class UnifieldTest(unittest.TestCase):
    '''
    Main test class for Unifield tests using TestCase and Openerplib as main inheritance
    @var sync: contains Synchro Server oerplib connection
    @var hq1: same as sync for HQ1 DB
    @var c1: same as sync for HQ1C1 DB
    @var p1: same as sync for HQ1C1P1 DB
    @var db: contains the list of DB connections
    @var test_module_name: name of the module used to create extended table for tests
    @var test_module_obj_name: name of the OpenERP object to use to access to extended table
    '''
    # global variable
    db = {}
    test_data_module_name = 'unifield_tests_data'
    test_module_obj_name = 'unifield.test'
    already_loaded = False
    description = ''        # Description of the test class (used in Automated Tests)
    category = 'Unifield'   # Category of the test (used in Automatic Tests)

    # FIXME/TODO: Make unittest.TestCase inherit from oerplib.error class because of RPCError that could be raised by unittest.TestCase

    def getDBConnectionsFromConfigFile(self):
        """
        Read the Configuration file and add Connection toh the good databases
        """
        # Read config file
        c = UnifieldTestConfigParser()
        c.read()

        tempo_mkdb = c.getboolean('DB', 'tempo_mkdb')
        db_suffixes = ['SYNC_SERVER', 'HQ1', 'HQ1C1', 'HQ1C1P1']
        names = ['sync', 'hq1', 'hq1c1', 'hq1c1p1']
        if not tempo_mkdb:
            db_suffixes = ['SYNC_SERVER', 'HQ_01', 'COORDO_01', 'PROJECT_01']

        # Check Remote warehouse and complete old params
        self.is_remote_warehouse = False
        remote_warehouse = c.get('DB', 'RW') or False
        if remote_warehouse:
            self.is_remote_warehouse = True

        # Add remote warehouse
        if remote_warehouse:
            self._addConnection(remote_warehouse, 'rw')

        # Prepare paramaters for XMLRPCConnection
        self.server_port = c.getint('Server', 'port')
        self.server_url = c.get('Server', 'url')
        self.uid = c.get('DB', 'username')
        self.pwd = c.get('DB', 'password')
        db_prefix = c.get('DB', 'db_prefix')

        # Create XMLRPCConnections
        for db_tuple in zip(db_suffixes, names):
            db_name = '%s%s' % (db_prefix, db_tuple[0])
            self._addConnection(db_name, db_tuple[1])

    def getDBConnectionsFromSyncServer(self):
        """
        Open a Connection to the Sync. Server database and read the DB mapping
        to create DB connections.
        """
        # TODO: Put this configuration on a osv object
        self.server_port = '8069'
        self.server_url = '127.0.0.1'
        self.uid = 'admin'
        self.pwd = 'admin'

        # Create a first connection to the sync. server database
        sync_db_name = self.cr.dbname
        self._addConnection(sync_db_name, 'sync')

        # Read all mapped DB
        db_map_obj = self.sync.get('test.db.mapping')
        db_map_ids = db_map_obj.search([('keyword', '!=', 'sync'), ('db_to_use', '!=', '')])
        for db_map in db_map_obj.browse(db_map_ids):
            self._addConnection(db_map.db_to_use, db_map.keyword)

    def _addConnection(self, db_name, name):
        '''
        Add new connection
        '''
        if name not in self.db:
            con = XMLConn(db_name, self.server_port, self.server_url, self.uid, self.pwd)
            setattr(self, name, con)
            self.db[name] = con

        # Set colors
        colors = self.colors
        database_display = colors.BRed + '[' + colors.Color_Off + name.center(6) + colors.BRed + ']' + colors.Color_Off
        self.db[name].colored_name = database_display

    def __getattr__(self, attr):
        """
        Returns the DB connection if exists or an error if not
        """
        if attr != 'test_id' and attr in self.db:
            return self.db[attr]
        else:
            raise NameError("No DB connection found the keyword '%s'!" % attr)

    def _hook_db_process(self, name, database):
        '''
        Some process to do for each database (except SYNC DB)
        '''
        return True

    def run(self, *args, **kwargs):
        return super(UnifieldTest, self).run(*args, **kwargs)

    def __init__(self, *args, **kwargs):
        """
        Initialize the TestCase from Sync. Database or Config. file
        """
        # DB values
        self.cr = kwargs.pop('cr', None)
        self.uid = kwargs.pop('uid', None)
        self.cid = kwargs.pop('cid', None)
        self.update_module = kwargs.pop('update_module', False)

        super(UnifieldTest, self).__init__(*args, **kwargs)

        # In case of update test cases at unifield_test module update
        if self.update_module:
            return

        # Get TerminalColors
        colors = TerminalColors()
        self.colors = colors

        if not self.db:
            if not self.cr:
                self.getDBConnectionsFromConfigFile()
            else:
                self.getDBConnectionsFromSyncServer()

        # For each database, check that unifield_tests module is loaded
        #+ If not, load it.
        #+ Except if the database is sync one
        if UnifieldTest.already_loaded:
            return
        for database_name in self.db:
            if database_name == 'sync':
                continue
            database = self.db.get(database_name)
            module_obj = database.get('ir.module.module')
            m_ids = module_obj.search([('name', '=', self.test_data_module_name)])
            database_display = database.colored_name
            for module in module_obj.read(m_ids, ['state']):
                state = module.get('state', '')
                if state == 'uninstalled':
                    print (database_display + ' [' + colors.BYellow + 'UP'.center(4) + colors.Color_Off + '] Module %s' % (self.test_data_module_name))
                    module_obj.button_install([module.get('id')])
                    database.get('base.module.upgrade').upgrade_module([])
                elif state in ['to upgrade', 'to install']:
                    print (database_display + ' [' + colors.BYellow + 'UP'.center(4) + colors.Color_Off + '] Module %s' % (self.test_data_module_name))
                    database.get('base.module.upgrade').upgrade_module([])
                elif state in ['installed']:
                    print (database_display + ' [' + colors.BGreen + 'OK'.center(4) + colors.Color_Off + '] Module %s' % (self.test_data_module_name))
                    pass
                else:
                    raise EnvironmentError(' Wrong module state: %s' % (state or '',))
            # Some processes after instanciation for this database
            self._hook_db_process(database_name, database)
        UnifieldTest.already_loaded = True

    def is_keyword_present(self, db, keyword):
        '''
        Check that the given keyword is present in given db connection and active.
        '''
        res = False
        if not db or not keyword:
            return res
        t_obj = db.get(self.test_module_obj_name)
        t_ids = t_obj.search([('name', '=', keyword), ('active', '=', True)])
        if not t_ids:
            return res
        return True

    def get_record(self, db, object_ref, module=None):
        '''
        Returns the object created by the test files.

        :param db: Connection to the database
        :param object_ref: XML ID of the object to find

        :return The ID of the object given in object_ref
        :rtype integer or False
        '''
        # Object
        data_obj = db.get('ir.model.data')

        if module is None:
            module = self.test_data_module_name

        obj = data_obj.get_object_reference(module, object_ref)

        if obj:
            return obj[1]

        return False

    def synchronize(self, db=None):
        '''
        Connect the 'db' database to the sync. server
        and run  synchronization.
        If no database givent in parameters, sync. all
        databases.
        :param db: DB connection to synchronize (can be None
                   or a list.
        :return: True
        '''
        if not db:
            for db_conn in self.db:
                self.synchronize(db=db_conn)

        if db and isinstance(db, list):
            for db_conn in db:
                self.synchronize(db=db_conn)

        conn_obj = db.get('sync.client.sync_server_connection')
        sync_obj = db.get('sync.client.sync_manager')

        conn_ids = conn_obj.search([])
        conn_obj.action_connect(conn_ids)
        sync_ids = sync_obj.search([])
        sync_obj.sync(sync_ids)

    def get_db_partner_name(self, db):
        '''
        Return the name of partner associated
        to the company of the database
        :param db: DB connection of which we
                   get the partner.
        :return: Name of the partner associated
                 to the company of the database
        '''
        company_obj = db.get('res.company')

        company_ids = company_obj.search([])
        return company_obj.browse(company_ids[0]).partner_id.name


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
