#!/usr/bin/env python2

#Load config file
import config

#Load OpenERP Client Library
import openerplib

#Load tests procedures
import unittest
#from tests import *
from tests.openerplib import db

from scripts.common import Synchro, HQ, Coordo, Project, Project2

try:
    import ipdb as pdb
except:
    import pdb

skipCreation = False
skipModules = False
skipModuleData = False
skipModuleUpdate = False
skipGroups = False
skipUniUser = False
skipConfig = False
skipRegister = False
skipSync = False

class db_creation(object):

    buggy_models = ('sale.price.setup',)

    base_wizards = {
        'res.config.view' : {
            'name' : "auto_init",
            'view' : 'extended',
        },
        'sale.price.setup' : {
            'sale_price' : 0.10,
        },
        'msf_instance.setup' : {
            'button' : 'action_skip',
        },
        'account.installer' : {
            'charts' : 'msf_chart_of_account',
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
        model = 'base.setup.installer'
        while model != 'ir.ui.menu':
            try:
                if model in self.buggy_models or (model == 'account.installer' and self.db is not HQ):
                    proxy = self.db.get(model)
                    answer = proxy.action_skip([])
                elif model == 'base.setup.config':
                    answer = self.db.wizard(model, data).config()
                else:
                    data = self.base_wizards.get(model, {})
                    button = data.pop('button', 'action_next')
                    answer = getattr(self.db.wizard(model, data), button)()
                model = answer.get('res_model', None)
            except:
                print "DEBUG: db=%s, model=%s" % (self.db.__name__, model)
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

    @unittest.skipIf(skipModuleData, "server_test installation desactivated")
    def test_10_install_data_server(self):
        self.db.connect('admin')
        self.db.module('msf_sync_data_synchro').install().do()

    @unittest.skipIf(skipGroups, "Group creation desactivated")
    def test_20_make_groups(self):
        group = Synchro.get('sync.server.entity_group')
        group.unlink(group.search([]))
        group_type = Synchro.get('sync.server.group_type')
        group.create({
            'name' : 'Section',
            'type_id' : group_type.search([('name','=','Section')])[0],
        })
        group.create({
            'name' : 'Mission',
            'type_id' : group_type.search([('name','=','Coordination')])[0],
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
        if self.db is Synchro: return
        Synchro.connect('admin')
        Synchro.user(self.db.__name__).add(self.db.__name__).addGroups('Sync / User')
        self.db.connect('admin', reconnect=True)
        wizard = self.db.wizard('sync.client.register_entity', {'email':config.default_email})
        # Fetch instances
        wizard.next()
        # Group state
        wizard.group_state()
        # Register instance
        wizard.validate()
        # Search entity record, server side
        entities = Synchro.get('sync.server.entity')
        ids = entities.search([('name','=',self.db.__name__)])
        if not len(ids) == 1: raise Exception, "Cannot find validation request for entity %s!" % self.db.__name__
        # Set parent
        if self.db is not HQ:
            if self.db is Coordo:
                parents = entities.search([('name','=','HQ')])
            elif self.db in (Project, Project2):
                parents = entities.search([('name','=','Coordo')])
            else:
                raise NotImplementedError('Cannot identify database %s' % self.db.__name__)
            if not parents:
                raise Exception('Cannot find parent entity for %s!' % self.db.__name__)
            entities.write(ids, {'parent_id':parents[0]})
        # Server accept validation
        entities.validate_action(ids)
        # Add entity to groups
        group = Synchro.get('sync.server.entity_group')
        group.write(group.search([('name','=','Section')]), {
            'entity_ids' : [(4,ids[0])],
        })
        group.write(group.search([('name','=','Mission')]), {
            'entity_ids' : [(4,ids[0])],
        })

    @unittest.skipIf(skipSync, "Synchronization desactivated")
    def test_40_synchronize(self):
        self.db.connect('admin')
        self.sync()

class hq_creation(client_creation, unittest.TestCase):
    db = HQ

    @unittest.skipIf(skipModuleData, "client_test installation desactivated")
    def test_10_install_data_client(self):
        self.db.connect('admin')
        self.db.module('msf_sync_data_hq').install().do()

    @unittest.skipIf(skipConfig, "Modules configuration desactivated")
    def test_30_configuration_wizards(self):
        self.db.connect('admin')
        self.configure()

class coordo_creation(client_creation, unittest.TestCase):
    db = Coordo

    @unittest.skipIf(skipModuleData, "client_test installation desactivated")
    def test_10_install_data_client(self):
        self.db.connect('admin')
        self.db.module('msf_sync_data_coordo').install().do()

    @unittest.skipIf(skipConfig, "Modules configuration desactivated")
    def test_50_configuration_wizards(self):
        self.db.connect('admin')
        self.configure()

class project_creation(client_creation, unittest.TestCase):
    db = Project

    @unittest.skipIf(skipConfig, "Modules configuration desactivated")
    def test_50_configuration_wizards(self):
        self.db.connect('admin')
        self.configure()

class project2_creation(client_creation, unittest.TestCase):
    db = Project2

    @unittest.skipIf(skipConfig, "Modules configuration desactivated")
    def test_50_configuration_wizards(self):
        self.db.connect('admin')
        self.configure()

test_cases = (synchro_creation, hq_creation, coordo_creation, project_creation, project2_creation)
#test_cases = (project_creation, project2_creation)
#test_cases = (synchro_creation,)
#test_cases = (hq_creation,)
#test_cases = (coordo_creation,)
#test_cases = (synchro_creation, hq_creation, coordo_creation,)
#test_cases = (project_creation,project2_creation,)
#test_cases = (project_creation,)

def load_tests(loader, tests, pattern):
    suite = unittest.TestSuite()
    for test_class in test_cases:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    return suite

if __name__ == '__main__':
    unittest.main(failfast=True, verbosity=2)

