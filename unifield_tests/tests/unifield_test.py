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
from random import randrange, choice
from datetime import timedelta

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
    test_module_name = 'unifield_tests'
    test_module_obj_name = 'unifield.test'
    already_loaded = False

    # FIXME/TODO: Make unittest.TestCase inherit from oerplib.error class because of RPCError that could be raised by unittest.TestCase

    def _addConnection(self, db_suffix, name):
        '''
        Add new connection
        '''
        con = XMLConn(db_suffix)
        setattr(self, name, con)
        self.db[name] = con
        # Set colors
        colors = self.colors
        database_display = colors.BRed + '[' + colors.Color_Off + name.center(6) + colors.BRed + ']' + colors.Color_Off
        self.db[name].colored_name = database_display

    def _hook_db_process(self, name, database):
        '''
        Some process to do for each database (except SYNC DB)
        '''
        return True

    def __init__(self, *args, **kwargs):
        # Default behaviour
        super(UnifieldTest, self).__init__(*args, **kwargs)
        # Prepare some values
        c = UnifieldTestConfigParser()
        self.config = c.read()
        tempo_mkdb = c.getboolean('DB', 'tempo_mkdb')
        db_suffixes = ['SYNC_SERVER', 'HQ1', 'HQ1C1', 'HQ1C1P1']
        names = ['sync', 'hq1', 'c1', 'p1']
        if not tempo_mkdb:
            db_suffixes = ['SYNC_SERVER', 'HQ_01', 'COORDO_01', 'PROJECT_01']
        # Check Remote warehouse and complete old params
        remote_warehouse = c.get('DB', 'RW') or False
        self.is_remote_warehouse = False
        if remote_warehouse:
            self.is_remote_warehouse = True
        self.is_remote_warehouse = False
        # Other values
        colors = TerminalColors()
        self.colors = colors
        # Keep each database connection
        for db_tuple in zip(db_suffixes, names):
            self._addConnection(db_tuple[0], db_tuple[1])
        # Add remote warehouse
        if remote_warehouse:
            self._addConnection(remote_warehouse, 'rw')
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
            m_ids = module_obj.search([('name', '=', self.test_module_name)])
            database_display = database.colored_name
            for module in module_obj.read(m_ids, ['state']):
                state = module.get('state', '')
                if state == 'uninstalled':
                    print (database_display + ' [' + colors.BYellow + 'UP'.center(4) + colors.Color_Off + '] Module %s' % (self.test_module_name))
                    module_obj.button_install([module.get('id')])
                    database.get('base.module.upgrade').upgrade_module([])
                elif state in ['to upgrade', 'to install']:
                    print (database_display + ' [' + colors.BYellow + 'UP'.center(4) + colors.Color_Off + '] Module %s' % (self.test_module_name))
                    database.get('base.module.upgrade').upgrade_module([])
                elif state in ['installed']:
                    print (database_display + ' [' + colors.BGreen + 'OK'.center(4) + colors.Color_Off + '] Module %s' % (self.test_module_name))
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
            module = self.test_module_name

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

    def random_date(self, start, end):
        """Take a random date between the first date (start) and the second one (stop).
        This method was taken from http://stackoverflow.com/questions/553303/generate-a-random-date-between-two-other-dates"""
        delta = end - start
        int_delta = (delta.days * 24 * 60 * 60) + delta.seconds
        random_second = randrange(int_delta)
        return (start + timedelta(seconds=random_second))

    def random_word(self):
        """Give a random word using a dictionnary containing a lot of french words"""
        f = 'french_words.txt'
        WORDS = open(f).read().splitlines()
        return choice(WORDS)

    def generate_analytic_distribution(self, db, record=False, write=False):
        """Create an analytic distribution and return its ID.
        :param db: DB connection to fetch data
        :param record: Browse record of the object on which we want a generic analytic distribution. If False, give a default analytic distribution.
        :param write: If True, attempt to write the analytic distribution result to the given object. It only works if you give a record!
        :return: analytic distribution ID (or False if failed)
        """
        # Prepare some value
        res = False
        company_obj = db.get('res.company')
        company_ids = company_obj.search([])[0]
        company = company_obj.browse(company_ids)
        instance = company.instance_id
        default_cost_center = instance.top_cost_center_id and instance.top_cost_center_id.id or False
        default_funding_pool = self.get_record(db, 'analytic_account_msf_private_funds', 'analytic_distribution') or False
        distrib_obj = db.get('analytic.distribution')

        # Some functions
        def create_analytic_distribution(account_id=False):
            """If not account, search a random destination"""
            if not account_id:
                # Search a random destination
                destination_ids = db.get('account.analytic.account').search([('category', '=', 'DEST')])
                if not destination_ids:
                    raise Exception("No destination found in this database (%s)!" % (db))
                destination_id = choice(destination_ids)
            else:
                account = db.get('account.account').browse(account_id)
                destination_id = account.default_destination_id and account.default_destination_id.id or False
                if not destination_id:
                    raise Exception("No default destination found for this account: %s." % (account.code))
            distrib_id = distrib_obj.create({'name': "Autogenerated Distribution"})
            for analytic_obj, value, cc_id in [('cost.center.distribution.line', default_cost_center, False), ('funding.pool.distribution.line', default_funding_pool, default_cost_center)]:
                vals = {
                    'distribution_id': distrib_id,
                    'name': "Autogenerated Line",
                    'analytic_id': value,
                    'cost_center_id': cc_id,
                    'percentage': 100.0,
                    'currency_id': company.currency_id.id,
                    'destination_id': destination_id,
                }
                db.get(analytic_obj).create(vals)
            return distrib_id

        # Begin
        if not record:
            res = create_analytic_distribution(False)
        else:
            object_name = db.get_osv_name(record) or ''
            if not object_name:
                raise Exception("No name for this record: %s." % (record))
            pool_object = db.get(object_name)
            field = 'analytic_distribution_id'
            if object_name == 'account.bank.statement.line': # default field
                account_id = record.account_id.id or False
            elif object_name == 'purchase.order': # default field
                account_id = False
            elif object_name == 'sale.order': # default field
                account_id = False
            elif object_name == 'purchase.order.line': # default field
                pass
            elif object_name == 'sale.order.line': # default field
                pass
            elif object_name == 'account.move.line': # default field
                pass
            elif object_name == 'account.commitment': # default field
                account_id = False
            elif object_name == 'account.commitment.line': # default field
                pass
            elif object_name == 'account.invoice': # default field
                account_id = False
            elif object_name == 'account.invoice.line': # default field
                pass
            elif object_name == 'account.analytic.line':
                field = 'distribution_id'
                account_id = record.general_account_id.id or False
            # TODO: Direct invoice wizard lines, open advance wizard lines
            else:
                raise Exception("Not implemented for this object: %s" % (object_name))
            # Create analytic distribution. First search a compatible destination
            res = create_analytic_distribution(account_id)
            # Write it, if asked
            if write: # only possible if record given
                pool_object.write([record.id], {field: res}, {})
        return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
