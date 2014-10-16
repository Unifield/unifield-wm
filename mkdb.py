#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
  (C) 2012 OpenERP - All rights reserved

"""

#Load config file
import config
from config import coordo_count, project_count, hq_count

import sys
import os
import shutil
import time
import uuid

from bzrlib.workingtree import WorkingTree
from bzrlib.branch import BzrBranch

import argparse
from subprocess import call

assert hq_count > 0, "You must have at least one HQ!"

#from tests import *
from tests.openerplib import db

from scripts.common import *

#Load tests procedures
#TODO: use unittest2 instead of unittest to make the command-line arguments
#      work with python < 2.7
if sys.version_info >= (2, 7):
    import unittest
else:
    # Needed for setUpClass and skipIf methods
    import unittest27 as unittest

bool_configuration_only = False
bool_creation_only = False
master_dir = '/'.join(os.path.realpath(__file__).split('/')[0:-1]+['master_dump'])
master_prefix_name = 'msf_profile_sync_so'
dir_to_dump = os.path.join(config.dump_dir, time.strftime('%Y%m%d%H%M'))

def warn(*messages):
    sys.stderr.write(" ".join(messages)+"\n")

# Fake TestCase to enable/disable quickly some tests
class creation_only(unittest.TestCase):
    pass

class configuration_only(unittest.TestCase):
    pass

class skip_all(unittest.TestCase):
    pass


# Determin skip flags if needed
skipDrop = True
skipDumpDbs = False
skipBranchesUpdate = True

if __name__ == '__main__':
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--nodrop", "-n", action='store_true', default=False, help="Don't drop existing db")
    parser.add_argument("--nodump", action='store_true', default=False, help="Disable dbs dump at the end")
    parser.add_argument("--log-to-file", action='store_true', default=False, help="Log the unittest")
    parser.add_argument("--update-code", action='store_true', default=False, help="Update the code, restart servers and create db if needed")
    parser.add_argument('unit_test_option', nargs='*', help='Tests to start: server_creation hq01_creation coordo01_creation dump_all  ...')


    o = parser.parse_args()
    if o.nodump and 'dump_all' not in o.unit_test_option:
        skipDumpDbs = True
    elif o.unit_test_option and 'dump_all' not in o.unit_test_option:
        o.unit_test_option.append('dump_all')

    if o.update_code or 'update_branches' in  o.unit_test_option:
        skipBranchesUpdate = False
        if o.unit_test_option and 'update_branches' not in o.unit_test_option:
            o.unit_test_option.insert(0, 'update_branches')

    sys.argv = [sys.argv[0]] + o.unit_test_option
    skipDrop = o.nodrop

    bool_creation_only = bool('creation_only' in sys.argv) or bool('skip_all' in sys.argv)
    bool_configuration_only = bool('configuration_only' in sys.argv) or bool('skip_all' in sys.argv)
else:
    bool_skip_all = bool(__name__+'.skip_all' in sys.argv)
    if bool_skip_all:
        bool_creation_only = True
        bool_configuration_only = True
    else:
        bool_creation_only = bool(__name__+'.creation_only' in sys.argv)
        bool_configuration_only = bool(__name__+'.configuration_only' in sys.argv)

skipCreation = bool_configuration_only
skipModules = bool_configuration_only
skipSyncSo = bool_configuration_only
skipModuleUpdate = bool_configuration_only
skipUniUser = bool_configuration_only
skipMasterCreation = False
skipGroups = bool_creation_only
skipPropInstance = bool_creation_only
skipConfig = bool_creation_only
skipRegister = bool_creation_only
skipSync = bool_creation_only
skipModuleData = bool_creation_only
skipPartner = bool_creation_only
skipManualConfig = bool_creation_only
skipOpenPeriod = bool_creation_only

# eval cond during the run
def skip_test_real_eval(cond, reason):
    def deco(fun):
        def wrap(*a, **b):
            if eval(cond):
                raise unittest.SkipTest(reason)
            return fun(*a, **b)
        return wrap
    return deco

class update_branches(unittest.TestCase):

    @unittest.skipIf(skipBranchesUpdate, "Branches update deactivated")
    def test_01_update_branch(self):
        to_up = check_lp_update(True)
        if 'unifield-web' in to_up:
            if not config.web_restart_cmd:
                raise self.fail('web_restart_cmd not define in config.py')
            call(config.web_restart_cmd, shell=True)
            to_up.remove('unifield-web')
        if to_up:
            if not config.server_restart_cmd:
                raise self.fail('server_restart_cmd not define in config.py')
            call(config.server_restart_cmd, shell=True)
            time.sleep(5)
        if not to_up:
            raise self.fail('No new code to pull')


# Base of database creation
class db_creation(object):

    #ignore_wizard = ['sale.price.setup'] # Fixed in unifield-wm > SP5
    ignore_wizard = ['msf_button_access_rights.view_config_wizard_install']

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
        'currency.setup' : {
            'functional_id' : config.currency,
        } 
    }

    db = None
    parent = None

    @property
    def parent_name(self):
        return self.parent.db.name if self.parent else None

    @classmethod
    def getNameFormat(cls):
        return  {
            'db': config.prefix,
            'ind': cls.index,
            'pind': cls.parent and cls.parent.index or '','ppind': cls.parent and cls.parent.parent and cls.parent.parent.index or ''
        }

    @classmethod
    def setUpClass(cls):
        if cls.db is None and hasattr(cls, 'index'):
            if cls.parent is not None:
                cls.parent.setUpClass()


            name = cls.name_format % cls.getNameFormat()
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
            last_sync.test_cases.append(cls)

    def setUp(self):
        if self.db is None:
            self.fail("Bad use of class")

    @unittest.skipIf(skipDrop, "Drop DB deactivated")
    def test_00_drop(self):
        self.db.connect('admin')
        self.db.drop()

    @skip_test_real_eval("skipCreation", "Creation desactivated")
    def test_01_create_db(self):
        self.db.connect('admin')
        self.db.create_db(config.admin_password)
        self.db.wait()
        self.db.user('admin').addGroups('Useability / Extended View')

    @skip_test_real_eval("skipModules", "Modules installation desactivated")
    def test_02_base_install(self):
        self.db.connect('admin')
        self.db.module('msf_profile').install().do()


    @skip_test_real_eval("skipSyncSo", "Modules installation desactivated")
    def test_04_sync_so_install(self):
        self.db.connect('admin')
        self.db.module('sync_so').install().do()
        backup_obj = self.db.get('backup.config')
        # disable automatic backup
        if backup_obj:
            backup_obj.write([1], {
                'beforemanualsync': False,
                'beforeautomaticsync': False,
                'aftermanualsync': False,
                'afterautomaticsync': False,
                'scheduledbackup': False
            })

    @skip_test_real_eval("skipUniUser", "UniField user creation desactivated")
    def test_05_unifield_user_creation(self):
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
                if model in self.ignore_wizard or \
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
                warn("DEBUG: db=%s, model=%s" % (self.db.name, model))
                raise

    @classmethod
    def sync(cls, db=None):
        if db is None: db = cls.db
        db.connect('admin')
        db.get('sync.client.sync_server_connection').connect()
        if not db.get('sync.client.entity').sync():
            monitor = db.get('sync.monitor')
            ids = monitor.search([], 0, 1, '"end" desc')
            raise Exception('Synchronization process of database "%s" failed!\n%s' % (db.db_name,monitor.read(ids, ['error'])[0]['error']))
 
    # Create Cost Center and Proprietary Instance for Test Cases
    def make_prop_instance(self, hq, prop_instance=None, mission=None):
        hq.connect('admin')
        # Get 2 cost centers: the top one and the normal one
        cost_center_id = False
        top_cost_center_id = False
        if mission and mission.db is hq:
            top_data = {
                'name' : "HT%d" % (self.index),
                'code' : "HT%d" % (self.index),
                'category' : 'OC',
                'type' : 'view',
                'parent_id' : hq.search_data('account.analytic.account', {'Code':'OC'})[0],
            }
            top_cost_center_id = hq.get('account.analytic.account').create(top_data)
            data = {
                'name' : "HT%d01" % (self.index),
                'code' : "HT%d01" % (self.index),
                'category' : 'OC',
                'type' : 'normal',
                'parent_id' : top_cost_center_id,
            }
            cost_center_id = hq.get('account.analytic.account').create(data)
        elif self.db is not hq:
            parent_cost_center_id = hq.search_data('account.analytic.account', {'Code':"HT%d" % (mission.index)})[0]
            data = {
                'name' : "HT%d%d1" % (mission.index, self.index),
                'code' : "HT%d%d1" % (mission.index, self.index),
                'category' : 'OC',
                'type' : 'normal',
                'parent_id' : parent_cost_center_id,
            }
            top_cost_center_id = hq.get('account.analytic.account').create(data)
        data = {
            'code' : self.db.name,
            'name' : self.db.name,
            'instance' : self.db.name,
            'mission' : '%s_MISSION_%s' % (config.prefix, ("OC" if mission is None else "%02d" % mission.index)),
            'state' : 'active',
        }
        if prop_instance is not None:
            data.update(prop_instance)
        if not hq.test('msf.instance', data):
            instance_id = hq.get('msf.instance').create(data)
            if self.db is not hq:
                # Create/update cost center lines as needed by level
                if mission.db is hq:
                    # Coordo: add cost center lines to the instance, tick both
                    top_line_data = {
                        'instance_id' : instance_id,
                        'cost_center_id' : top_cost_center_id,
                        'is_target' : True,
                        'is_top_cost_center' : True,
                        'is_po_fo_cost_center' : False,
                    }
                    hq.get('account.target.costcenter').create(top_line_data)
                    line_data = {
                        'instance_id' : instance_id,
                        'cost_center_id' : cost_center_id,
                        'is_target' : True,
                        'is_top_cost_center' : False,
                        'is_po_fo_cost_center' : True,
                    }
                    hq.get('account.target.costcenter').create(line_data)
                else:
                    # Project: add cost center lines to parent coordo instance, tick them in instance
                    top_line_data = {
                        'instance_id' : data['parent_id'],
                        'cost_center_id' : top_cost_center_id,
                        'is_target' : False,
                        'is_top_cost_center' : False,
                        'is_po_fo_cost_center' : False,
                    }
                    hq.get('account.target.costcenter').create(top_line_data)
                    project_target_ids = hq.search_data('account.target.costcenter', {'instance_id' : instance_id, 'cost_center_id' : top_cost_center_id})
                    hq.write('account.target.costcenter', project_target_ids, {'is_target': True, 'is_top_cost_center': True, 'is_po_fo_cost_center' : True})
                self.sync(hq)

    def add_to_group(self, group_name, group_type):
        Synchro.connect('admin')
        entity_ids = Synchro.get('sync.server.entity').search([('name','=',self.db.name)])
        assert len(entity_ids) == 1, "The entity must exists!"
        # Make groups
        group = Synchro.get('sync.server.entity_group')
        # Make or update OC group
        group_ids = group.search([('name','=',group_name)])
        if group_ids:
            group.write(group_ids, {'entity_ids' : [(4,entity_ids[0])]})
        else:
            Type = Synchro.get('sync.server.group_type')
            type_ids = Type.search([('name', '=', group_type)])
            if not type_ids:
                type_ids = [Type.create({'name':group_type})]
            group.create({
                'name' : group_name,
                'type_id' : type_ids[0],
                'entity_ids' : [(6,0,entity_ids)],
            })

    @classmethod
    def dump_db(self, path, name=None):
        if self.db is None:
            self.setUpClass()
        if not os.path.exists(path):
            os.makedirs(path)
        if name is None:
            self.db.connect()
            name =self.db.db_name
        bckfile = os.path.join(path, '%s.dump' % name)
        orig_bck = bckfile
        i = 0
        while os.path.exists(bckfile):
            i += 1
            bckfile = os.path.join(path, '%s_%s.dump' % (name, i))
        if i:
            shutil.move(orig_bck, bckfile)

        bckfile_f = open(orig_bck, 'wb')
        bckfile_f.write(self.db.dump_db())
        bckfile_f.close()

    def restore_db(self):
        dump = os.path.join(master_dir, "%s.dump" % (master_prefix_name,) ) #self.db.name)
        f = open(dump, 'rb')
        self.db.connect('admin')
        self.db.restore_db(self.db.name, f.read())
        f.close()
        # wait process
        time.sleep(10)

# Run a last sync after all synchronization
class last_sync(unittest.TestCase):
    test_cases = []

    def test_50_last_synchronization(self):
        if not self.test_cases:
            self.skipTest("No database to update")
        for tc in self.test_cases:
            assert issubclass(tc, db_creation), "The object %s is not of type db_creation!"
            tc.sync()

class dump_all(unittest.TestCase):

    @unittest.skipIf(skipDumpDbs, "DBs dump directory creation deactivated")
    def test_00_create_dump_dir(self):
        if not os.path.exists(dir_to_dump):
            os.makedirs(dir_to_dump)

    @unittest.skipIf(skipDumpDbs, "DBs dump deactivated")
    def test_10_dump_all(self):
        for tc in test_cases:
            if issubclass(tc, db_creation):
                tc.dump_db(dir_to_dump)

    @unittest.skipIf(skipDumpDbs, "DBs dump deactivated")
    def test_20_dump_branch_info(self):
        info = {}
        for ad in config.addons:
            src_path = os.path.join(config.source_path, ad)
            if not os.path.exists(src_path):
                raise self.fail('%s does not exist ! Did you set source_path in config.py ?' % src_path)
            info[ad] = get_revno_from_path(src_path)
        f = open(os.path.join(dir_to_dump, 'info.txt'), 'w')
        for mod, data in info.items():
            f.write("%s_url=%s\n" % (mod, data['lpurl']))
            f.write("%s_revno=%s\n" % (mod, data['revno']))
        f.close()


# Specific Sync Server creation
class server_creation(db_creation, unittest.TestCase):
    db = Synchro
    
    @unittest.skipIf(skipMasterCreation, "Master dump creation desactivated") 
    def test_03_dump_master(self):
        self.dump_db(master_dir, master_prefix_name)

    @unittest.skipIf(skipModuleUpdate, "update_server installation desactivated")
    def test_10_install_update_server(self):
        self.db.connect('admin')
        self.db.module('update_server').install().do()

    @unittest.skipIf(skipModuleData, "Data module installation desactivated")
    def test_10_install_data_server(self):
        self.db.connect('admin')
        self.db.module('sync_remote_warehouse_server').install().do()
        self.db.module('msf_sync_data_server').install().do()

    @unittest.skipIf(skipConfig, "Modules configuration desactivated")
    def test_30_configuration_wizards(self):
        self.db.connect('admin')
        self.configure()

    @unittest.skipIf(skipSync, "Synchronization desactivated")
    def test_40_activate_rules(self):
        self.db.connect('admin')
        sync_rule_obj = Synchro.get('sync_server.message_rule')
        rule_ids = sync_rule_obj.search([('active', '=', 1)])
        for rule in sync_rule_obj.read(rule_ids, ['model_id']):
             sync_rule_obj.write(rule['id'], {'model_id': rule['model_id'] , 'status': 'valid'})
        #Synchro.activate('sync_server.sync_rule', [])

# Base for instances creation ('is not Synchro')
class client_creation(db_creation):

    @unittest.skipIf(skipMasterCreation, "Creation of coordo from master")
    def test_00_restore_from_master(self):
        global skipCreation
        global skipModules
        skipCreation = True
        skipModules = True
        self.restore_db()

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
        # search the current entity
        entity_id = self.db.get('sync.client.entity').search([])
        data = {'name': self.db.name, 'identifier': str(uuid.uuid1())}
        if entity_id:
            entity_data = self.db.get('sync.client.entity').read(entity_id[0])
            if entity_data['name'] != self.db.name:
                self.db.get('sync.client.entity').write(entity_id[0], data)
        else:
            self.db.get('sync.client.entity').create(data)
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
        
        res = self.db.get('res.partner')
        temp_partner = res.search([('name','=','Local Market')])
        # new CoA (2014-02-20)
        payable_ids = account.search([('code','=','30020')])
        if not payable_ids:
            payable_ids = account.search([('code','=','3000')])

        receivable_ids = account.search([('code','=','12050')])
        if not receivable_ids:
            receivable_ids = account.search([('code','=','1205')])
        if temp_partner:
            # set account values for local market
            self.db.write('res.partner', temp_partner,{
                'property_account_payable' : payable_ids[0],
                'property_account_receivable' : receivable_ids[0],
                'city': 'Geneva',
                })

        temp_partner = res.search([('name','=',self.db.name)])
        if temp_partner:
            # set account values for the default user
            self.db.write('res.partner', temp_partner,{
                'property_account_payable' : payable_ids[0],
                'property_account_receivable' : receivable_ids[0],
                })

    @unittest.skipIf(skipOpenPeriod, "Open Period desactivated")
    def test_92_open_period(self):
        self.db.connect('admin')
        today = time.strftime('%Y-%m-%d')
        month = time.strftime('%m')
        # search current fiscalyear
        fy_ids = self.db.search_data('account.fiscalyear', [('date_start', '<=', today), ('date_stop', '>=', today)])
        assert len(fy_ids) > 0, "No fiscalyear found!"
        period_ids = self.db.search_data('account.period', [('fiscalyear_id', 'in', fy_ids), ('number', '<=', month), ('state', '=', 'created')])
        # change all period by draft state (should use action_set_state but openerplib doesn't give way to do this)
        # as it's to open period from created to draft state, it's not very important
        self.db.write('account.period', period_ids, {'state': 'draft'})
            

# Replicable class to create hq n
class hqn_creation(client_creation, unittest.TestCase):
    name_format = "%(db)s_HQ%(ind)d"

    @unittest.skipIf(skipGroups, "Group creation desactivated")
    def test_30_make_groups_coordo(self):
        self.add_to_group('Coordinations of %s' % self.db.name, 'COORDINATIONS')
        self.add_to_group('OC_%02d' % self.index, 'OC')
        for i in range(1, coordo_count+1):
            self.add_to_group('HQ + Mission %s' % i, 'HQ + MISSION')

    @unittest.skipIf(skipPropInstance, "Proprietary Instance creation desactivated")
    def test_40_prop_instance(self):
        self.db.connect('admin')
        if self.db.search_data('msf.instance', [('instance','=',self.db.name)]):
            self.skipTest("Proprietary Instance already exists")
        self.make_prop_instance(self.db, {
            'level' : 'section',
            'reconcile_prefix' : self.prefix,
            'move_prefix' : self.prefix,
        })

    @unittest.skipIf(skipConfig, "Modules configuration desactivated")
    def test_41_configuration_wizards(self):
        self.db.connect('admin')
        self.configure()

    @unittest.skipIf(skipModuleData, "Data module installation desactivated")
    def test_42_install_data_client(self):
        self.db.connect('admin')
        self.db.module('msf_sync_data_hq').install().do()
        
    @unittest.skipIf(skipManualConfig, "Manual link on analytic account destination desactivated")
    def test_43_manual_link_on_analytic_account_destination(self):
        self.db.connect('admin')
        # new CoA (2014-02-20)
        link_ids = self.db.search_data('account.destination.link', [])
        if not link_ids:
            account_ids = self.db.search_data('account.account', [('type','!=','view'),('user_type.code','=','expense')])
            analytic_account_ids = self.db.search_data('account.analytic.account', [('name', 'in', ['Expatriates','National Staff','Operations','Support'])])
            self.db.write('account.analytic.account',  analytic_account_ids, {'destination_ids': [(6, 0, account_ids)]})


# Replicable class to create coordo n
class coordon_creation(client_creation):
    name_format = "%(db)s_HQ%(pind)dC%(ind)d"

    @unittest.skipIf(skipGroups, "Group creation desactivated")
    def test_30_make_groups_coordo(self):
        self.add_to_group('OC_%02d' % self.hq.index, 'OC')
        self.add_to_group('Coordinations of %s' % self.hq.db.name, 'COORDINATIONS')
        self.add_to_group('Mission %s' % self.index, 'MISSION')
        self.add_to_group('HQ + Mission %s' % self.index, 'HQ + MISSION')

    @unittest.skipIf(skipPropInstance, "Proprietary Instance creation desactivated")
    def test_40_prop_instance(self):
        self.hq.db.connect('admin')
        if self.hq.db.search_data('msf.instance', [('instance','=',self.db.name)]):
            self.skipTest("Proprietary Instance already exists")
        self.make_prop_instance(self.hq.db, {
            'level' : 'coordo',
            'reconcile_prefix' : self.prefix,
            'move_prefix' : self.prefix,
            'parent_id' : self.hq.db.search_data('msf.instance', [('instance','=',self.hq.db.name)])[0],
        }, self.hq)

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
    name_format = "%(db)s_HQ%(ppind)dC%(pind)dP%(ind)d"

    @unittest.skipIf(skipGroups, "Group creation desactivated")
    def test_30_make_groups_coordo(self):
        self.add_to_group('OC_%02d' % self.hq.index, 'OC')
        self.add_to_group('Mission %s' % self.parent.index, 'MISSION')
        self.add_to_group('HQ + Mission %s' % self.parent.index, 'HQ + MISSION')

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
        self.hq.db.connect('admin')
        if self.hq.db.search_data('msf.instance', [('instance','=',self.db.name)]):
            self.skipTest("Proprietary Instance already exists")
        self.make_prop_instance(self.hq.db, {
            'level' : 'project',
            'reconcile_prefix' : self.prefix,
            'move_prefix' : self.prefix,
            'parent_id' : self.hq.db.search_data('msf.instance', [('instance','=',self.parent_name)])[0],
        }, self.parent)

    @unittest.skipIf(skipConfig, "Modules configuration desactivated")
    def test_60_configuration_wizards(self):
        self.db.connect('admin')
        self.configure()


class verbose(unittest.TestCase):
    def test_10_show_dbs(self):
        warn("\n"+"-" * 40)
        for tc_hq in filter(lambda tc:issubclass(tc, hqn_creation), test_cases):
            warn( " * %s" % hqn_creation.name_format % tc_hq.getNameFormat())
            for tc in filter(lambda tc:issubclass(tc, coordon_creation) \
                                       and tc.parent is tc_hq, test_cases):
                warn( "    - %s" % coordon_creation.name_format % tc.getNameFormat())
                for tp in filter(lambda tp:issubclass(tp, projectn_creation) \
                                           and tp.parent is tc, test_cases):
                    warn( "        + %s" % projectn_creation.name_format % tp.getNameFormat())
            warn("-" * 40)



# Base Install
test_cases = [verbose, update_branches, server_creation]

# Create HQ classes
for i in range(1, hq_count+1):
    test_cases.append( type("HQ%d_creation" % i, (hqn_creation,unittest.TestCase), {
        'prefix' : 'HQ%s'%i,
        'index' : i,
    }) )
    # Make testcase visible for importation
    globals()[test_cases[-1].__name__] = test_cases[-1]


    # Create Coordo classes
    for ci in range(1, coordo_count+1):
        test_cases.append( type("HQ%d_C%d_creation" % (i, ci), (coordon_creation,unittest.TestCase), {
            'prefix' : 'C%s%s' % (i, ci),
            'index' : ci,
            'parent' : globals()["HQ%d_creation" % i],
        }) )
        test_cases[-1].hq = test_cases[-1].parent
        # Make testcase visible for importation
        globals()[test_cases[-1].__name__] = test_cases[-1]


        # Create Project classes
        for pi in range(1, project_count+1):
            test_cases.append( type("HQ%d_C%d_P%d_creation" % (i, ci, pi), (projectn_creation,unittest.TestCase), {
                'prefix' : 'P%s%s%s'%(i, ci, pi),
                'index' : pi,
                'parent' : globals()["HQ%d_C%d_creation" % (i, ci)],
            }) )
            test_cases[-1].hq = test_cases[-1].parent.parent
            # Make testcase visible for importation
            globals()[test_cases[-1].__name__] = test_cases[-1]


# Push last_sync test at last
test_cases.append(last_sync)

# and dump
test_cases.append(dump_all)


def load_tests(loader, tests, pattern):
    suite = unittest.TestSuite()
    for test_class in test_cases:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    return suite


if __name__ == '__main__':
    if o.log_to_file:
        if not os.path.exists(dir_to_dump):
            os.makedirs(dir_to_dump)
        f = open(os.path.join(dir_to_dump, 'script_result.log'), "w")
        stream = f
    else:
        stream = sys.stderr
    unittest.main(testRunner=unittest.TextTestRunner(stream,failfast=True, verbosity=2))
    if o.log_to_file:
        f.close()
