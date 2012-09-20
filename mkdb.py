#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
  (C) 2012 OpenERP - All rights reserved

  HOWTO
  =====

    -v is unittest's verbose flag
    -f is unittest's failsafe flag (stop execution at first error)

    * make specific databases, you can run the script by using
      one of these commands:
       python2 -m unittest -v -f mkdb.hq_creation
       python2 -m unittest -v -f mkdb.project01_creation mkdb.project02_creation
    
    * make creation step only:
       python2 -m unittest -v -f mkdb.creation_only mkdb.server_creation
    
    * make configuration step only:
       python2 -m unittest -v -f mkdb.configuration_only mkdb.coordo02_creation

    Note: you can't use the creation_only and configuration_only flag in the
          same command. Plus they are retroactive ('hq_creation creation_only'
          will make only creation of HQ).

    Default behavior:
      python2 -m unittest -v -f mkdb.hq_creation mkdb.coordo01_creation mkdb.project01_creation mkdb.project02_creation


  EXAMPLE OF config.py
  ====================

    # -*- coding: utf-8 -*-

    # postgres admin password
    db_password = 'admin'

    # default admin password
    admin_password = 'admin'

    # default user login & password (when connecting to db)
    user_login = 'unifield'
    user_password = 'unifield'

    # infos to connect to instances (client side)
    client_host = 'localhost'
    client_port = 8069

    # infos to connect to sync server
    server_host = 'localhost'
    server_port = 8069

    # infos for instance connection to sync server
    netrpc_port = 8070

    # database format name
    prefix = "TEST"

    # other stuffs
    default_email = 'nobody@nogroup.net'
    company_name = 'Médecins Sans Frontières'
    currency = 'base.EUR'

    # number instance of type coordo and project to create
    coordo_count = 1
    project_count = 2

"""

import sys

#Load config file
import config
from config import coordo_count, project_count

#Load OpenERP Client Library
import openerplib

#from tests import *
from tests.openerplib import db

from scripts.common import *

#Load tests procedures
if sys.version_info >= (2, 7):
    import unittest
else:
    # Needed for setUpClass and skipIf methods
    import unittest27 as unittest

try:
    import ipdb as pdb
except:
    import pdb

skipCreation = False
skipModules = False
skipModuleUpdate = False
skipUniUser = False
skipGroups = False
skipPropInstance = False
skipConfig = False
skipRegister = False
skipSync = False
skipModuleData = False
skipPartner = False


# Fake TestCase to enable/disable quickly some tests
class creation_only(unittest.TestCase):
    pass

class configuration_only(unittest.TestCase):
    pass


# Determin skip flags if needed
if not __name__ == '__main__':
    bool_creation_only = bool(__name__+'.creation_only' in sys.argv)
    bool_configuration_only = bool(__name__+'.configuration_only' in sys.argv)

    skipCreation = bool_configuration_only
    skipModules = bool_configuration_only
    skipModuleUpdate = bool_configuration_only
    skipUniUser = bool_configuration_only

    skipGroups = bool_creation_only
    skipPropInstance = bool_creation_only
    skipConfig = bool_creation_only
    skipRegister = bool_creation_only
    skipSync = bool_creation_only
    skipModuleData = bool_creation_only
    skipPartner = bool_creation_only


# Base of database creation
class db_creation(object):

    #buggy_models = ['sale.price.setup'] # Fixed in unifield-wm > SP5
    buggy_models = []

    base_wizards = {
        'base.setup.config' : {
            'button' : 'config',
        },
        'res.config.view' : {
            'name' : "auto_init",
            'view' : 'extended',
        },
        'sale.price.setup' : {
            'sale_price' : 0.10,
        },
        'stock.location.configuration.wizard' : {
            'location_type' : 'internal',
            'location_usage' : 'stock',
            'location_name' : 'Test Location',
            'button' : 'action_stop',
        },
    }

    db = None
    parent_name = None

    def setUp(self):
        if self.db is None:
            self.fail("Bad use of class")

    @unittest.skipIf(skipCreation, "Creation desactivated")
    def test_00_drop(self):
        self.db.connect('admin')
        self.db.drop()

    @unittest.skipIf(skipCreation, "Creation desactivated")
    def test_01_create_db(self):
        self.db.connect('admin')
        self.db.create_db(config.admin_password)
        self.db.wait()
        self.db.user('admin').addGroups('Useability / Extended View')

    @unittest.skipIf(skipModules, "Modules installation desactivated")
    def test_02_base_install(self):
        self.db.connect('admin')
        self.db.module('msf_profile').install().do()
        self.db.module('sync_so').install().do()

    @unittest.skipIf(skipUniUser, "Unifield user creation desactivated")
    def test_03_unifield_user_creation(self):
        self.db.connect('admin')
        self.db.user('unifield').add('admin').addGroups('Sync / User', 'Purchase / User')

    def configure(self):
        # We did rather start on msf_instance.setup...
        # Reason: For an unknown reason, this wizard is set as 'done' automatically after run any first wizard
        #model = 'base.setup.installer'
        model = 'msf_instance.setup'
        while model != 'ir.ui.menu':
            try:
                # skip account.installer if no parent_name providen (typically: HQ instance)
                if model in self.buggy_models or \
                   (model == 'account.installer' and self.parent_name is not None) or \
                   (model == 'msf_instance.setup' and self.db is Synchro):
                    proxy = self.db.get(model)
                    answer = proxy.action_skip([])
                elif model == 'msf_instance.setup':
                    answer = self.db.wizard(model, {
                        'instance_id' : self.db.search_data('msf.instance', [('instance','=',self.db.name)])[0],
                    }).action_next()
                else:
                    data = dict(self.base_wizards.get(model, {}))
                    button = data.pop('button', 'action_next')
                    answer = getattr(self.db.wizard(model, data), button)()
                model = answer.get('res_model', None)
            except:
                print "DEBUG: db=%s, model=%s" % (self.db.name, model)
                raise

    def sync(self, db=None):
        if db is None: db = self.db
        if not db.get('sync.client.entity').sync():
            monitor = db.get('sync.monitor')
            ids = monitor.search([], 0, 1, '"end" desc')
            self.fail('Synchronization process of database "%s" failed!\n%s' % (db.db_name,monitor.read(ids, ['error'])[0]['error']))
 
    # Create Cost Center and Proprietary Instance for Test Cases
    def make_prop_instance(self, prop_instance=None):
        try:
            cost_center_id = HQ.search_data('account.analytic.account', [('code','=',self.db.name)])[0]
        except IndexError:
            data = {
                'name' : self.db.name,
                'code' : self.db.name,
                'category' : 'OC',
            }
            if self.db is not HQ:
                data['parent_id'] = HQ.search_data('account.analytic.account', {'Code':'OC'})[0]
            cost_center_id = HQ.get('account.analytic.account').create(data)
        data = {
            'code' : self.db.name,
            'name' : self.db.name,
            'instance' : self.db.name,
            'mission' : '%s_MISSION' % config.prefix,
            'cost_center_id' : cost_center_id,
            'state' : 'active',
        }
        if prop_instance is not None:
            data.update(prop_instance)
        if not HQ.test('msf.instance', data):
            HQ.get('msf.instance').create(data)
            if self.db is not HQ:
                self.sync(HQ)


# Specific Sync Server creation
class server_creation(db_creation, unittest.TestCase):
    db = Synchro

    @unittest.skipIf(skipModuleUpdate, "update_server installation desactivated")
    def test_10_install_update_server(self):
        self.db.connect('admin')
        self.db.module('update_server').install().do()

    @unittest.skipIf(skipModuleData, "Data module installation desactivated")
    def test_10_install_data_server(self):
        self.db.connect('admin')
        self.db.module('msf_sync_data_server').install().do()

    @unittest.skipIf(skipConfig, "Modules configuration desactivated")
    def test_30_configuration_wizards(self):
        self.db.connect('admin')
        self.configure()

    @unittest.skipIf(skipSync, "Synchronization desactivated")
    def test_40_activate_rules(self):
        self.db.connect('admin')
        Synchro.activate('sync_server.sync_rule', [])


# Base for instances creation ('is not Synchro')
class client_creation(db_creation):
    @unittest.skipIf(skipModuleUpdate, "update_client installation desactivated")
    def test_10_install_update_client(self):
        self.db.connect('admin')
        self.db.module('update_client').install().do()

    @unittest.skipIf(skipModules, "Modules installation desactivated")
    def test_10_install_web_module(self):
        self.db.connect('admin')
        self.db.module('sync_client_web').install().do()

    @unittest.skipIf(skipRegister, "Registration desactivated")
    def test_20_register_entity(self):
        Synchro.connect('admin')
        Synchro.user(self.db.name).add(self.db.name).addGroups('Sync / User')
        self.db.connect('admin')
        wizard = self.db.wizard('sync.client.register_entity', {'email':config.default_email})
        # Fetch instances
        wizard.next()
        # Group state
        wizard.group_state()
        # Register instance
        wizard.validate()
        # Search entity record, server side
        entities = Synchro.get('sync.server.entity')
        entity_ids = entities.search([('name','=',self.db.name)])
        if not len(entity_ids) == 1:
            self.fail("Cannot find validation request for entity %s!" % self.db.name)
        # Set parent
        if self.parent_name is not None:
            parents = entities.search([('name','=',self.parent_name)])
            if not parents:
                self.fail('Cannot find parent entity for %s!' % self.db.name)
            entities.write(entity_ids, {'parent_id':parents[0]})
        # Server accept validation
        entities.validate_action(entity_ids)

    @unittest.skipIf(skipGroups, "Group creation desactivated")
    def test_30_make_groups_mission(self):
        Synchro.connect('admin')
        entity_ids = Synchro.get('sync.server.entity').search([('name','=',self.db.name)])
        # Add entity to groups
        group = Synchro.get('sync.server.entity_group')
        group.write(group.search([('name','=','OC')]), {
            'entity_ids' : [(4,entity_ids[0])],
        })

    @unittest.skipIf(skipSync, "Synchronization desactivated")
    def test_50_synchronize(self):
        self.db.connect('admin')
        self.sync()

    @unittest.skipIf(skipModuleData, "Data module installation desactivated")
    def test_90_install_post_data(self):
        self.db.connect('admin')
        self.db.module('msf_sync_data_post_synchro').install().do()

    @unittest.skipIf(skipPartner, "Partner creation desactivated")
    def test_91_instance_partner(self):
        self.db.connect('admin')
        account = self.db.get('account.account')
        self.db.get('res.partner').create({
            'name' : self.db.name,
            'customer' : 1,
            'supplier' : 1,
            'partner_type' : 'internal',
            'property_account_payable' : account.search([('code','=','3000')])[0],
            'property_account_receivable' : account.search([('code','=','1201')])[0],
        })


# Specific HQ creation
class hq_creation(client_creation, unittest.TestCase):
    db = HQ

    @unittest.skipIf(skipPropInstance, "Proprietary Instance creation desactivated")
    def test_40_prop_instance(self):
        HQ.connect('admin')
        if HQ.search_data('msf.instance', [('instance','=',self.db.name)]):
            self.skipTest("Proprietary Instance already exists")
        self.make_prop_instance({
            'level' : 'section',
            'reconcile_prefix' : '#1',
            'move_prefix' : '#1',
        })

    @unittest.skipIf(skipConfig, "Modules configuration desactivated")
    def test_41_configuration_wizards(self):
        self.db.connect('admin')
        self.configure()

    @unittest.skipIf(skipModuleData, "Data module installation desactivated")
    def test_42_install_data_client(self):
        self.db.connect('admin')
        self.db.module('msf_sync_data_hq').install().do()


# Replicable class to create coordo n
class coordon_creation(client_creation):
    index = None
    prefix = None
    db = None

    @classmethod
    def setUpClass(cls):
        name = "%s_COORDO_%02d" % (config.prefix, cls.index)
        cls.db = db_instance(
            server=client,
            name=name,
            synchro={
                'protocol' : 'netrpc',
                'host' : config.server_host,
                'port' : config.netrpc_port,
                'database' : Synchro.name,
                'login' : name,
                'password' : name,
            },
        )

    @unittest.skipIf(skipGroups, "Group creation desactivated")
    def test_31_make_groups_coordo(self):
        Synchro.connect('admin')
        entity_ids = Synchro.get('sync.server.entity').search([('name','=',self.db.name)])
        # Add entity to groups
        group = Synchro.get('sync.server.entity_group')
        group.write(group.search([('name','in',('Coordinations','Mission1'))]), {
            'entity_ids' : [(4,entity_ids[0])],
        })

    @unittest.skipIf(skipPropInstance, "Proprietary Instance creation desactivated")
    def test_40_prop_instance(self):
        HQ.connect('admin')
        if HQ.search_data('msf.instance', [('instance','=',self.db.name)]):
            self.skipTest("Proprietary Instance already exists")
        self.make_prop_instance({
            'level' : 'coordo',
            'reconcile_prefix' : self.prefix,
            'move_prefix' : self.prefix,
            'parent_id' : HQ.search_data('msf.instance', [('instance','=',HQ.name)])[0],
        })

    @unittest.skipIf(skipConfig, "Modules configuration desactivated")
    def test_60_configuration_wizards(self):
        self.db.connect('admin')
        self.configure()

    @unittest.skipIf(skipModuleData, "Data module installation desactivated")
    def test_61_install_data_client(self):
        self.db.connect('admin')
        self.db.module('msf_sync_data_coordo').install().do()


# Replicable class to create project n
class projectn_creation(client_creation):
    index = None
    prefix = None
    db = None

    @classmethod
    def setUpClass(cls):
        name = "%s_PROJECT_%02d" % (config.prefix, cls.index)
        cls.db = db_instance(
            server=client,
            name=name,
            synchro={
                'protocol' : 'netrpc',
                'host' : config.server_host,
                'port' : config.netrpc_port,
                'database' : Synchro.name,
                'login' : name,
                'password' : name,
            },
        )

    @unittest.skipIf(skipGroups, "Group creation desactivated")
    def test_31_make_groups_project(self):
        Synchro.connect('admin')
        entity_ids = Synchro.get('sync.server.entity').search([('name','=',self.db.name)])
        # Add entity to groups
        group = Synchro.get('sync.server.entity_group')
        group.write(group.search([('name','=','Mission1')]), {
            'entity_ids' : [(4,entity_ids[0])],
        })

    @unittest.skipIf(skipPropInstance, "Proprietary Instance creation desactivated")
    def test_40_prop_instance(self):
        HQ.connect('admin')
        if HQ.search_data('msf.instance', [('instance','=',self.db.name)]):
            self.skipTest("Proprietary Instance already exists")
        self.make_prop_instance({
            'level' : 'project',
            'reconcile_prefix' : self.prefix,
            'move_prefix' : self.prefix,
            'parent_id' : HQ.search_data('msf.instance', [('instance','=',self.parent_name)])[0],
        })

    @unittest.skipIf(skipConfig, "Modules configuration desactivated")
    def test_60_configuration_wizards(self):
        self.db.connect('admin')
        self.configure()


# Base Install
test_cases = [server_creation, hq_creation]


# Create Coordo classes
for i in range(1, coordo_count+1):
    test_cases.append( type("coordo%02d_creation" % i, (coordon_creation,unittest.TestCase), {
        'prefix' : hex(i+1)[2:].rjust(2,'#'),
        'index' : i,
        'parent_name' : HQ.name,
    }) )
    # Make testcase visible for importation
    globals()[test_cases[-1].__name__] = test_cases[-1]


# Create Project classes
for i in range(1, project_count+1):
    test_cases.append( type("project%02d_creation" % i, (projectn_creation,unittest.TestCase), {
        'prefix' : hex(i+1+coordo_count)[2:].rjust(2,'#'),
        'index' : i,
        'parent_name' : "%s_COORDO_%02d" % (config.prefix, \
                        (((i-1) / (project_count/coordo_count)) % coordo_count + 1)),
    }) )
    globals()[test_cases[-1].__name__] = test_cases[-1]


def load_tests(loader, tests, pattern):
    suite = unittest.TestSuite()
    for test_class in test_cases:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    return suite


if __name__ == '__main__':
    unittest.main(failfast=True, verbosity=2)

