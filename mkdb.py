#!/usr/bin/env python2

import sys

#Load config file
import config

#Load OpenERP Client Library
import openerplib

#from tests import *
from tests.openerplib import db

from scripts.common import Synchro, HQ, Coordo, Project, Project2

#Load tests procedures
if sys.version_info >= (2, 7):
    import unittest
else:
    import unittest27 as unittest

try:
    import ipdb as pdb
except:
    import pdb

skipCreation = False
skipModules = False
skipModuleData = False
skipModuleUpdate = False
skipGroups = False
skipCostCenter = False
skipPropInstance = False
skipConfig = False
skipRegister = False
skipSync = False
skipUniUser = False
skipPartner = False

class db_creation(object):

    buggy_models = ('sale.price.setup',)

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

    def setUp(self):
        if self.db is None:
            raise Exception("Bad use of class")

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
                if model in self.buggy_models or \
                   (model == 'account.installer' and self.db is not HQ) or \
                   (model == 'msf_instance.setup' and self.db in (Synchro, HQ,)):
                    proxy = self.db.get(model)
                    answer = proxy.action_skip([])
                elif model == 'msf_instance.setup':
                    answer = self.db.wizard(model, {
                        'instance_id' : self.db.search_data('msf.instance', [('instance','=',self.db.db_name)])[0],
                    }).action_next()
                else:
                    data = dict(self.base_wizards.get(model, {}))
                    button = data.pop('button', 'action_next')
                    answer = getattr(self.db.wizard(model, data), button)()
                model = answer.get('res_model', None)
            except:
                print "DEBUG: db=%s, model=%s" % (self.db.db_name, model)
                pdb.set_trace()
                raise

    def sync(self, db=None):
        if db is None: db = self.db
        if not db.get('sync.client.entity').sync():
            monitor = db.get('sync.monitor')
            ids = monitor.search([], 0, 1, '"end" desc')
            self.fail('Synchronization process of database "%s" failed!\n%s' % (db.db_name,monitor.read(ids, ['error'])[0]['error']))
 
class synchro_creation(db_creation, unittest.TestCase):
    db = Synchro

    @unittest.skipIf(skipModuleUpdate, "update_server installation desactivated")
    def test_10_install_update_server(self):
        self.db.connect('admin')
        self.db.module('update_server').install().do()

    @unittest.skipIf(skipModuleData, "Data module installation desactivated")
    def test_10_install_data_server(self):
        self.db.connect('admin')
        self.db.module('msf_sync_data_synchro').install().do()

    @unittest.skipIf(skipGroups, "Group creation desactivated")
    def test_20_make_groups(self):
        group = Synchro.get('sync.server.entity_group')
        group.unlink(group.search([]))
        group_type = Synchro.get('sync.server.group_type')
        group.create({
            'name' : 'OC',
            'type_id' : group_type.search([('name','=','OC')])[0],
        })
        group.create({
            'name' : 'Mission',
            'type_id' : group_type.search([('name','=','MISSION')])[0],
        })
        group.create({
            'name' : 'Coordo',
            'type_id' : group_type.search([('name','=','COORDINATIONS')])[0],
        })

    @unittest.skipIf(skipConfig, "Modules configuration desactivated")
    def test_30_configuration_wizards(self):
        self.db.connect('admin')
        self.configure()

    @unittest.skipIf(skipSync, "Synchronization desactivated")
    def test_40_activate_rules(self):
        self.db.connect('admin')
        Synchro.activate('sync_server.sync_rule', [])

class client_creation(db_creation):

    entity_ids = None

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
        Synchro.user(self.db.db_name).add(self.db.db_name).addGroups('Sync / User')
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
        entity_ids = entities.search([('name','=',self.db.db_name)])
        if not len(entity_ids) == 1:
            raise Exception, "Cannot find validation request for entity %s!" % self.db.db_name
        # Set parent
        if self.db is not HQ:
            if self.db is Coordo:
                parents = entities.search([('name','=',HQ.name)])
            else:
                parents = entities.search([('name','=',Coordo.name)])
            if not parents:
                raise Exception('Cannot find parent entity for %s!' % self.db.db_name)
            entities.write(entity_ids, {'parent_id':parents[0]})
        # Server accept validation
        entities.validate_action(entity_ids)

    @unittest.skipIf(skipGroups, "Group creation desactivated")
    def test_30_make_groups_mission(self):
        Synchro.connect('admin')
        entity_ids = Synchro.get('sync.server.entity').search([('name','=',self.db.db_name)])
        # Add entity to groups
        group = Synchro.get('sync.server.entity_group')
        group.write(group.search([('name','in',('Mission','OC'))]), {
            'entity_ids' : [(4,entity_ids[0])],
        })

    @unittest.skipIf(skipCostCenter, "Cost Center creation desactivated")
    def test_30_make_costcenter(self):
        if self.db is HQ: return
        HQ.connect('admin')
        if not HQ.test('account.analytic.account', [('code','=',self.db.shortname)]):
            HQ.get('account.analytic.account').create({
                'name' : self.db.shortname,
                'code' : self.db.shortname,
                'category' : 'OC',
                'parent_id' : HQ.search_data('account.analytic.account', {'Code':'OC'})[0],
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
            'name' : self.db.db_name,
            'customer' : 1,
            'supplier' : 1,
            'property_account_payable' : account.search([('code','=','1201')])[0],
            'property_account_receivable' : account.search([('code','=','3000')])[0],
        })

class hq_creation(client_creation, unittest.TestCase):
    db = HQ

    @unittest.skipIf(skipPropInstance, "Proprietary Instance creation desactivated")
    def test_40_prop_instance(self):
        HQ.connect('admin')
        data = {
            'code' : self.db.shortname,
            'name' : self.db.shortname,
            'instance' : self.db.db_name,
            'level' : 'section',
            'mission' : '%s_MISSION' % config.prefix,
            'cost_center_id' : HQ.search_data('account.analytic.account', {'code':'OC'})[0],
            'state' : 'active',
        }
        if not HQ.test('msf.instance', data):
            HQ.get('msf.instance').create(data)

    @unittest.skipIf(skipConfig, "Modules configuration desactivated")
    def test_41_configuration_wizards(self):
        self.db.connect('admin')
        self.configure()

    @unittest.skipIf(skipModuleData, "Data module installation desactivated")
    def test_42_install_data_client(self):
        self.db.connect('admin')
        self.db.module('msf_sync_data_hq').install().do()

    @unittest.skipIf(skipConfig, "Modules configuration desactivated")
    def test_43_sync(self):
        self.db.connect('admin')
        self.sync(HQ)


class coordo_creation(client_creation, unittest.TestCase):
    db = Coordo

    @unittest.skipIf(skipGroups, "Group creation desactivated")
    def test_31_make_groups_coordo(self):
        Synchro.connect('admin')
        entity_ids = Synchro.get('sync.server.entity').search([('name','=',self.db.db_name)])
        # Add entity to groups
        group = Synchro.get('sync.server.entity_group')
        group.write(group.search([('name','=','Coordo')]), {
            'entity_ids' : [(4,entity_ids[0])],
        })

    @unittest.skipIf(skipPropInstance, "Proprietary Instance creation desactivated")
    def test_40_prop_instance(self):
        HQ.connect('admin')
        data = {
            'code' : self.db.shortname,
            'name' : self.db.shortname,
            'instance' : self.db.db_name,
            'level' : 'coordo',
            'mission' : '%s_MISSION' % config.prefix,
            'parent_id' : HQ.search_data('msf.instance', [('instance','=',HQ.name)])[0],
            'cost_center_id' : HQ.search_data('account.analytic.account', {'code':self.db.shortname})[0],
            'state' : 'active',
        }
        if not HQ.test('msf.instance', data):
            HQ.get('msf.instance').create(data)
            self.sync(HQ)

    @unittest.skipIf(skipConfig, "Modules configuration desactivated")
    def test_60_configuration_wizards(self):
        self.db.connect('admin')
        self.configure()

    @unittest.skipIf(skipModuleData, "Data module installation desactivated")
    def test_61_install_data_client(self):
        self.db.connect('admin')
        self.db.module('msf_sync_data_coordo').install().do()

class project_base_creation(client_creation):
    @unittest.skipIf(skipPropInstance, "Proprietary Instance creation desactivated")
    def test_40_prop_instance(self):
        HQ.connect('admin')
        data = {
            'code' : self.db.shortname,
            'name' : self.db.shortname,
            'instance' : self.db.db_name,
            'level' : 'project',
            'mission' : '%s_MISSION' % config.prefix,
            'parent_id' : HQ.search_data('msf.instance', [('instance','=',Coordo.name)])[0],
            'cost_center_id' : HQ.search_data('account.analytic.account', {'code':self.db.shortname})[0],
            'state' : 'active',
        }
        if not HQ.test('msf.instance', data):
            HQ.get('msf.instance').create(data)
            self.sync(HQ)

    @unittest.skipIf(skipConfig, "Modules configuration desactivated")
    def test_60_configuration_wizards(self):
        self.db.connect('admin')
        self.configure()

class project_creation(project_base_creation, unittest.TestCase):
    db = Project

class project2_creation(project_base_creation, unittest.TestCase):
    db = Project2

test_cases = (synchro_creation, hq_creation, coordo_creation, project_creation, project2_creation)
#test_cases = (project_creation, project2_creation)
#test_cases = (synchro_creation,)
#test_cases = (hq_creation,)
#test_cases = (coordo_creation,project_creation, project2_creation)
#test_cases = (synchro_creation, hq_creation, coordo_creation,)
#test_cases = (project_creation,project2_creation,)
#test_cases = (project_creation,)
#test_cases = (project2_creation,)

def load_tests(loader, tests, pattern):
    suite = unittest.TestSuite()
    for test_class in test_cases:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    return suite

if __name__ == '__main__':
    unittest.main(failfast=True, verbosity=2)

