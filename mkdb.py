#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
  (C) 2012 OpenERP - All rights reserved

"""

#Load config file
import config
from config import coordo_count, project_count, hq_count, default_oc

import sys
import os
import shutil
import time
import uuid
import re

import argparse
from subprocess import call

import base64
import csv
from passlib.hash import bcrypt

assert hq_count > 0, "You must have at least one HQ!"

from scripts.common import client, db_instance, Synchro, check_lp_update, get_revno_from_path

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

def get_file_from_source(filename):
    if filename:
        last = filename.split('/')[-1]
        newfile = os.path.expanduser('~/unifield-server/bin/addons/msf_profile/user_rights/%s' % last)
        if os.path.exists(newfile):
            return newfile
    return filename

def get_oc(dbname):
    if isinstance(default_oc, dict):
        hq_name = re.findall(r'HQ[0-9]+', dbname)
        if hq_name:
            return default_oc.get(hq_name[-1], 'oca')
        return 'oca'
    return default_oc

def warn(*messages):
    sys.stderr.write(" ".join(messages)+"\n")

# Fake TestCase to enable/disable quickly some tests
class creation_only(unittest.TestCase):
    pass

class configuration_only(unittest.TestCase):
    pass

class skip_all(unittest.TestCase):
    pass

def get_users_from_file(filename):

    LOGIN_COLUMN_INDEX=1
    PASSWD_COLUMN_INDEX=2
    FOR_HQ_COLUMN_INDEX=3
    FOR_COORDO_COLUMN_INDEX=4
    FOR_PROJECT_COLUMN_INDEX=5

    FIRST_GROUP_COLUMN_INDEX=6

    SELECTION_CHAR='X'

    users = []
    with open(filename, 'rb') as csvfile:
        reader = csv.reader(csvfile, delimiter=';')
        header=False

        groups = []

        for row in reader:
            if not header:
                header=True

                for index in range(FIRST_GROUP_COLUMN_INDEX, len(row)):
                    groups.append((index, row[index]))
            else:
                user_groups = []
                for grp in groups:
                    if row[grp[0]] == SELECTION_CHAR:
                        user_groups.append(grp[1])

                data = {
                    'login': row[LOGIN_COLUMN_INDEX],
                    'passwd': row[PASSWD_COLUMN_INDEX],
                    'for_hq': True if row[FOR_HQ_COLUMN_INDEX] == SELECTION_CHAR else False,
                    'for_co': True if row[FOR_COORDO_COLUMN_INDEX] == SELECTION_CHAR else False,
                    'for_pr': True if row[FOR_PROJECT_COLUMN_INDEX] == SELECTION_CHAR else False,
                    'groups': user_groups
                }

                users.append(data)
    return users


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
skipSync = bool_creation_only
skipModuleData = bool_creation_only
skipPartner = bool_creation_only
skipManualConfig = bool_creation_only
skipOpenPeriod = bool_creation_only
skipLoadUACFile = bool_creation_only
skipCreateUsers = bool_creation_only
skipLoadExtraFiles = bool_creation_only

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
            'functional_id' : config.default_currency,
        },
        'base.setup.company': {
            'contact_name': 'msf',
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
            if hasattr(config, 'sync_user_admin') and config.sync_user_admin:
                sync_user = 'admin'
            else:
                sync_user = name

            cls.db = db_instance(
                server=client,
                name=name,
                synchro={
                    'protocol' : 'xmlrpc',
                    'host' : config.server_host,
                    'port' : config.server_port,
                    'database' : Synchro.name,
                    'login' : sync_user,
                    'password' : config.admin_password,
                    'timeout': 600,
                    'netrpc_retry': 10,
                    'xmlrpc_retry': 10,
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
        # disable automatic backup
        backup_ids = self.db.get('ir.model').search([('model', '=', 'backup.config')])
        if backup_ids:
            self.db.get('backup.config').write([1], {
                'beforemanualsync': False,
                'beforeautomaticsync': False,
                'aftermanualsync': False,
                'afterautomaticsync': False,
                'scheduledbackup': False
            })

    @skip_test_real_eval("skipUniUser", "UniField user creation desactivated")
    def test_05_unifield_user_creation(self):
        self.db.connect('admin')
        if not hasattr(config, 'load_uac_file') or not config.load_uac_file:
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
                    instance_id = self.db.search_data('msf.instance', [('instance','=',self.db.name)])[0]
                    self.db.get('res.company').write([1], {'instance_id': instance_id})
                    answer = self.db.wizard(model, {'instance_id': instance_id}).action_next()
                else:
                    data = dict(self.base_wizards.get(model, {}))
                    if model == 'currency.setup':
                        hq_name = self.db and self.db.name and re.findall(r'HQ[0-9]+', self.db.name)
                        if hq_name and hasattr(config, 'currency_tree'):
                            data['functional_id'] = config.currency_tree.get(hq_name[-1], config.default_currency)
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
        mission_suffix = 'OC'
        if mission and mission.db is hq:
            # coordo
            mission_suffix = "%02d" % self.index
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
            # project
            mission_suffix = "%02d" % mission.index
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
            'mission' : '%s_MISSION_%s' % (config.prefix, mission_suffix),
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
        oc = get_oc(self.db.name)
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
                'oc': oc
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
        self.db.dump_db_file(orig_bck)

    def restore_db(self):
        dump = os.path.join(master_dir, "%s.dump" % (master_prefix_name,) ) #self.db.name)
        self.db.connect('admin')
        self.db.restore_db_file(self.db.name, dump)
        # wait process
        time.sleep(10)

# Run a last sync after all synchronization
class last_sync(unittest.TestCase):
    test_cases = []

    def test_50_last_synchronization(self):
        if not self.test_cases:
            self.skipTest("No database to update")
        for i in [0,1]:
            for tc in self.test_cases:
                assert issubclass(tc, db_creation), "The object %s is not of type db_creation!"
                tc.sync()

class activate_inter_partner(unittest.TestCase):

    def test_99_activate_inter_partner(self):
        all_projects = []
        for tc in test_cases:
            if issubclass(tc, projectn_creation):
                all_projects.append(tc.db.name)
        for tc in test_cases:
            if issubclass(tc, (coordon_creation, projectn_creation)):
                db = tc.db
                db.connect('admin')
                p_obj = db.get('res.partner')
                exclude_name = [db.name]
                same_mission_ids = p_obj.search([('partner_type', '=', 'internal')])
                for p in p_obj.read(same_mission_ids, ['name']):
                    exclude_name.append(p['name'])
                exclude_name += all_projects
                partner_ids = p_obj.search([('partner_type', 'in', ['section', 'intermission']), ('active', '=', False), ('name', 'not in', exclude_name)])
                if partner_ids:
                    p_obj.write(partner_ids, {'active': True})
                ext_ids = p_obj.search([('partner_type', '=', 'external'), ('active', '=', False)])
                if ext_ids:
                    p_obj.write(ext_ids, {'active': True})

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

    def test_02_install_lang(self):
        self.db.connect('admin')
        lang = False
        if hasattr(config, 'lang'):
            lang = config.lang
        if lang:
            #if self.db.get('sync.client.entity'):
            #    call(config.server_restart_cmd, shell=True)
            #    time.sleep(5)
            lang_obj = self.db.get('res.lang')
            lang_id = lang_obj.search([('code', '=', lang)])
            mod_obj = self.db.get('ir.module.module')
            if lang_id:
                lang_obj.write(lang_id, {'translatable': True})
                mod_ids = mod_obj.search([('state', '=', 'installed')])
                mod_obj.button_update_translations(mod_ids, lang)

    @unittest.skipIf(skipMasterCreation, "Master dump creation desactivated")
    def test_03_dump_master(self):
        self.dump_db(master_dir, master_prefix_name)

    @unittest.skipIf(skipModuleUpdate, "update_server installation desactivated")
    def test_10_install_update_server(self):
        self.db.connect('admin')
        self.db.module('update_server').install().do()
        self.db.module('update_client').install().do()

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

    def test_99_add_shortcut(self):
        self.db.connect('admin')
        menu_to_add = ['sync_server.entity_menu', 'sync_server.sync_rule_menu', 'sync_server.message_rule_menu']
        for menu in menu_to_add:
            module, xml = menu.split('.')
            menu_id = self.db.get('ir.model.data').get_object_reference(module, xml)[1]
            menu_name = self.db.get('ir.ui.menu').name_get([menu_id])[0][1]
            try:
                self.db.get('ir.ui.view_sc').create({'res_id': menu_id, 'name': menu_name})
            except:
                raise

# Base for instances creation ('is not Synchro')
class client_creation(db_creation):
    def import_csv(self, filename):
        model = os.path.splitext(os.path.basename(filename))[0]
        if model in ('product.nomenclature', 'product.category', 'product.product'):
            req = self.db.get('res.request')
            nb = req.search([])
            wiz = self.db.get('import_data')
            f = open(filename, 'rb')
            rec_id = wiz.create({'object': model, 'file': base64.encodestring(f.read())})
            f.close()
            wiz.import_csv([rec_id], {})
            imported = False
            while not imported:
                time.sleep(5)
                imported = nb != req.search([])
            return
        with open(filename, 'rb') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')
            fields = False
            data = []
            for row in reader:
                if not fields:
                    fields = row
                else:
                    data.append(row)
            obj = self.db.get(model)
            if obj and fields and data:
                obj.import_data(fields, data)

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
        if not hasattr(config, 'sync_user_admin') or not config.sync_user_admin:
            Synchro.user(self.db.name).add(self.db.name).addGroups('Sync / User')
        self.db.connect('admin')

        oc = get_oc(self.db.name)
        entity_id = self.db.get('sync.client.entity').search([])
        data = {
            'name': self.db.name,
            'identifier': str(uuid.uuid1()),
        }
        data['oc'] = oc
        if entity_id:
            entity_data = self.db.get('sync.client.entity').read(entity_id[0])
            if entity_data['name'] != self.db.name:
                self.db.get('sync.client.entity').write(entity_id[0], data)
        else:
            self.db.get('sync.client.entity').create(data)
        wiz_data = {'email': config.default_email}
        wiz_data['oc'] = oc
        wizard = self.db.wizard('sync.client.register_entity', wiz_data)
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

    @unittest.skipIf(skipSync, "Synchronization desactivated")
    def test_50_synchronize(self):
        self.db.connect('admin')
        self.sync()

    def test_70_create_intermission(self):
        if isinstance(self, hqn_creation):
            return True

        partner = self.hq.db.get('res.partner')
        account = self.hq.db.get('account.account')
        partner.create({
            'name': self.db.name,
            'partner_type': 'intermission',
            'customer': False,
            'supplier': False,
            'property_account_payable':  account.search([('code','=','30020')])[0],
            'property_account_receivable': account.search([('code','=','12050')])[0],
            'city': 'XXX',
        })

    @unittest.skipIf(skipCreateUsers, "Create users desactivated")
    def test_70_create_users(self):
        if not hasattr(config, 'load_users_file') or not config.load_users_file:
            return

        is_hq = isinstance(self, hqn_creation)
        is_coordo = isinstance(self, coordon_creation)
        is_project = isinstance(self, projectn_creation)

        if is_hq or is_coordo or is_project:
            users = get_users_from_file(config.load_users_file);
            for u in users:
                if (is_hq and u['for_hq']) or (is_coordo and u['for_co']) or (is_project and u['for_pr']):
                    self.db.user(u['login']).add(u['passwd']).addGroups(*u['groups'])


    @unittest.skipIf(skipModuleData, "Data module installation desactivated")
    def test_90_install_post_data(self):
        self.db.connect('admin')
        if hasattr(config, 'load_data') and config.load_data:
            for filename in config.load_data:
                self.import_csv(filename)
        else:
            self.db.module('msf_sync_data_post_synchro').install().do().set_notinstalled()

    def search_account(self, code):
        account = self.db.get('account.account')
        ac_ids = account.search([('code', '=', code)])
        if ac_ids:
            return ac_ids[0]
        return False

    def test_91_configure_company_accounts(self):
        company_fields = {
            'salaries_default_account': '30100',
            'counterpart_hq_entries_default_account': '33010',
            'import_invoice_default_account': '12011',
            'intermission_default_counterpart': '14010',
            'ye_pl_cp_for_bs_debit_bal_account': '69001',
            'ye_pl_cp_for_bs_credit_bal_account': '79002',
            'ye_pl_pos_credit_account': '79003',
            'ye_pl_ne_credit_account': '50000',
            'ye_pl_pos_debit_account': '51000',
            'ye_pl_ne_debit_account': '69002',
            'cheque_debit_account_id': '10210',
            'cheque_credit_account_id': '10210',
            'bank_debit_account_id': '10200',
            'bank_credit_account_id': '10200',
            'cash_debit_account_id': '10100',
            'cash_credit_account_id': '10100',
        }
        for f in company_fields:
            company_fields[f] = self.search_account(company_fields[f])
        self.db.get('res.company').write([1], company_fields)

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
        if not fy_ids:
            create_fy_wiz = self.db.get('account.period.create')
            wiz_id = create_fy_wiz.create({'fiscalyear': 'current'})
            create_fy_wiz.account_period_create_periods([wiz_id])
            fy_ids = self.db.search_data('account.fiscalyear', [('date_start', '<=', today), ('date_stop', '>=', today)])

        assert len(fy_ids) > 0, "No fiscalyear found!"
        period_ids = self.db.search_data('account.period', [('fiscalyear_id', 'in', fy_ids), ('number', '<=', month), ('state', '=', 'created')])
        # change all period by draft state (should use action_set_state but openerplib doesn't give way to do this)
        # as it's to open period from created to draft state, it's not very important
        self.db.write('account.period', period_ids, {'state': 'draft'})

    def set_analytic_loss(self, db, code):
        db.connect('admin')
        ana_obj = db.get('account.analytic.account')
        ids = ana_obj.search([('code', '=', code)])
        if ids:
            ana_obj.write(ids[0], {'for_fx_gain_loss': True})

    def test_93_set_gain_loss(self):
        to_hq = False
        code = False
        if isinstance(self, projectn_creation):
            code = "HT%d%d1" % (self.parent.index, self.index)
        elif isinstance(self, coordon_creation):
            code = "HT%d01" % (self.index)
            if self.index == 1:
                to_hq = True
        if code:
            self.db.get('ir.config_parameter').set_param('INIT_CC_FX_GAIN', code)
            if to_hq:
                self.set_analytic_loss(self.hq.db, code)

    def test_95_create_registers(self):
        if isinstance(self, hqn_creation):
            return True

        reg = {'EUR': {}, 'CHF': {}}
        for j_type, account_code in [('bank', '10200'), ('cash', '10100'), ('cheque', '10210')]:
            account_id = self.db.get('account.account').search([('code', '=', account_code)])[0]
            for cur in ['EUR', 'CHF']:
                data = {
                    'name': '%s %s %s' % (j_type, self.db.name, cur),
                    'code': '%s%s%s' % (j_type, self.db.name[-2:], cur),
                    'type': j_type,
                    'currency': self.db.get('res.currency').search([('name', '=', cur)])[0],
                    'default_credit_account_id': account_id,
                    'default_debit_account_id': account_id,
                }
                get_ana = self.db.get('account.journal').onchange_type(False, j_type, False)
                data['analytic_journal_id'] = get_ana.get('value', {}).get('analytic_journal_id', False)
                if j_type == 'cheque':
                    if not reg[cur].get('bank'):
                        continue
                    data['bank_journal_id'] = reg[cur]['bank']

                reg[cur][j_type] = self.db.get('account.journal').create(data)

    def test_95_create_stock_cu(self):
        if isinstance(self, hqn_creation):
            return True

        stock_wiz = self.db.get('stock.location.configuration.wizard')
        w_id = stock_wiz.create({'location_usage': 'consumption_unit', 'location_type': 'internal', 'location_name': 'IntCU'})
        stock_wiz.confirm_creation(w_id)
        w_id = stock_wiz.create({'location_usage': 'consumption_unit', 'location_type': 'customer', 'location_name': 'ExtCU'})
        stock_wiz.confirm_creation(w_id)

    def test_99_add_shortcut(self):
        self.db.connect('admin')
        menu_to_add = ['sync_client.sync_wiz_menu', 'sync_client.sync_monitor_menu']
        for menu in menu_to_add:
            module, xml = menu.split('.')
            menu_id = self.db.get('ir.model.data').get_object_reference(module, xml)[1]
            menu_name = self.db.get('ir.ui.menu').name_get([menu_id])[0][1]
            try:
                self.db.get('ir.ui.view_sc').create({'res_id': menu_id, 'name': menu_name})
            except:
                raise

    @unittest.skipIf(skipSync, "Synchronization desactivated")
    def test_99_synchronize(self):
        self.db.connect('admin')
        self.sync()

# Replicable class to create hq n
class hqn_creation(client_creation, unittest.TestCase):
    name_format = "%(db)s_HQ%(ind)d"

    @unittest.skipIf(skipGroups, "Group creation desactivated")
    def test_30_make_groups_coordo(self):
        self.add_to_group('Coordinations of %s' % self.db.name, 'COORDINATIONS')
        self.add_to_group('OC_%02d' % self.index, 'OC')
        for i in range(1, coordo_count+1):
            self.add_to_group('HQ%s + Mission %s' % (self.index, i), 'HQ + MISSION')
        entities = Synchro.get('sync.server.entity')
        entity_ids = entities.search([('name','=',self.db.name)])
        entities.validate_action(entity_ids)

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
        if hasattr(config, 'load_hq_data') and config.load_hq_data:
            for filename in config.load_hq_data:
                self.import_csv(filename)
        else:
            self.db.module('msf_sync_data_hq').install().do().set_notinstalled()

        if self.db.get('ir.model').search([('model', '=', 'hr.payment.method')]):
            for x in ['ESP', 'CHQ', 'VIR']:
                self.db.get('hr.payment.method').create({'name': x})

        # duplicate as UniData
        if hq_count > 1:
            data = [
                'DORADIDA15T',
                'DINJCEFA1V-',
                'ADAPCABL1S-',
                'ADAPCABL2S-',
                'ADAPCART02-',
            ]
            prod = self.db.get('product.product')
            unidata_id = self.db.get('ir.model.data').get_object_reference('product_attributes', 'int_6')[1]
            msfid = 100
            for code in data:
                p_id = prod.search([('default_code', '=', code)])
                if p_id:
                    newcode = 'HQ%s%s' % (self.index, code)
                    copy_id = prod.copy(p_id[0], {'default_code': newcode, 'international_status': unidata_id, 'msfid': msfid})
                    prod.write([copy_id], {'name': newcode})
                msfid += 10

    def test_41_load_rates(self):
        cur_dir = os.path.dirname(os.path.realpath(__file__))

        cur_to_load = config.default_currency
        hq_name = self.db and self.db.name and re.findall(r'HQ[0-9]+', self.db.name)
        if hq_name and hasattr(config, 'currency_tree'):
            cur_to_load = config.currency_tree.get(hq_name[-1], config.default_currency)

        rate_file = os.path.join(cur_dir, 'data', '%s.txt' % cur_to_load)
        if os.path.isfile(rate_file):
            rate_obj = self.db.get('res.currency')
            fx_rate_obj = self.db.get('res.currency.rate')
            rate_ids = rate_obj.search([('active', 'in', ['t', 'f'])])
            rate_dict = {}
            for x in rate_obj.read(rate_ids, ['name']):
                rate_dict[x['name']] = x['id']
            fx_rate_obj.create({'currency_id': rate_dict[cur_to_load.upper()], 'rate': 1, 'name': '2016-01-01'})
            f = open(rate_file, 'r')
            date = False
            for data in f:
                data = data.rstrip()
                if data[0] != ' ':
                    date = data
                elif data[0] == ' ' and ':' in data:
                    cur, rate = data[1:].split(':')
                    if date and rate_dict.get(cur):
                        fx_rate_obj.create({'currency_id': rate_dict[cur], 'rate': rate, 'name': date})

    @unittest.skipIf(skipManualConfig, "Manual link on analytic account destination desactivated")
    def test_43_manual_link_on_analytic_account_destination(self):
        self.db.connect('admin')
        # new CoA (2014-02-20)
        link_ids = self.db.search_data('account.destination.link', [])
        if not link_ids:
            account_ids = self.db.search_data('account.account', [('type','!=','view'),('user_type.code','=','expense')])
            analytic_account_ids = self.db.search_data('account.analytic.account', [('name', 'in', ['Expatriates','National Staff','Operations','Support'])])
            self.db.write('account.analytic.account',  analytic_account_ids, {'destination_ids': [(6, 0, account_ids)]})


    @unittest.skipIf(skipLoadExtraFiles, "Load Extra Data Files desactivated")
    def test_46_load_extra_data_files(self):
        if not hasattr(config, 'load_extra_files') or not config.load_extra_files:
            return

        for filename in config.load_extra_files:
            self.import_csv(get_file_from_source(filename))

    @unittest.skipIf(skipLoadUACFile, "Load UAC File desactivated")
    def test_45_load_uac_file(self):
        if not hasattr(config, 'load_uac_file') or not config.load_uac_file:
            return

        self.db.connect('admin')

        f = open(get_file_from_source(config.load_uac_file))
        data = base64.encodestring(f.read())
        f.close()

        wiz = self.db.get('user.access.configurator')
        rec_id = wiz.create({'file_to_import_uac': data})
        try:
            wiz.do_process_uac([rec_id])
        except:
            pass
        user_ids = self.db.get('res.users').search([('id', '!=', 1)])
        if user_ids:
            self.db.get('res.users').write(user_ids, {'password': bcrypt.encrypt(config.admin_password)})

    def test_70_create_intersection(self):
        partner = self.db.get('res.partner')
        account = self.db.get('account.account')
        pricelist = self.db.get('product.pricelist')
        purch_eur = pricelist.search([('type', '=', 'purchase'), ('currency_id.name', '=', 'EUR')])
        sale_eur = pricelist.search([('type', '=', 'sale'), ('currency_id.name', '=', 'EUR')])
        for tc in test_cases:
            if (issubclass(tc, coordon_creation) or issubclass(tc, projectn_creation)) and tc.hq.index != self.index:
                if tc.db is None:
                    db_name = tc.name_format % tc.getNameFormat()
                else:
                    db_name = tc.db.name
                partner.create({
                    'name': db_name,
                    'partner_type': 'section',
                    'po_by_project': 'project',
                    'customer': True,
                    'supplier': True,
                    'property_account_payable':  account.search([('code','=','30010')])[0],
                    'property_account_receivable': account.search([('code','=','12010')])[0],
                    'city': 'XXX',
                    'property_product_pricelist_purchase': purch_eur[0],
                    'property_product_pricelist': sale_eur[0],
                })

    def test_99_create_esc(self):
        account = self.db.get('account.account')
        self.db.get('res.partner').create({
            'name': 'ESC',
            'partner_type': 'esc',
            'po_by_project': 'project',
            'supplier': True,
            'customer': False,
            'property_account_payable':  account.search([('code','=','30010')])[0],
            'property_account_receivable': account.search([('code','=','12050')])[0],
            'city': 'XXX',
        })


# Replicable class to create coordo n
class coordon_creation(client_creation):
    name_format = "%(db)s_HQ%(pind)dC%(ind)d"

    @unittest.skipIf(skipGroups, "Group creation desactivated")
    def test_30_make_groups_coordo(self):
        self.add_to_group('OC_%02d' % self.hq.index, 'OC')
        self.add_to_group('Coordinations of %s' % self.hq.db.name, 'COORDINATIONS')
        self.add_to_group('Mission %s-%s' % (self.hq.index, self.index), 'MISSION')
        self.add_to_group('HQ%s + Mission %s' % (self.hq.index, self.index), 'HQ + MISSION')
        entities = Synchro.get('sync.server.entity')
        entity_ids = entities.search([('name','=',self.db.name)])
        entities.validate_action(entity_ids)


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
        self.db.module('msf_sync_data_coordo').install().do().set_notinstalled()
        partner_obj = self.db.get('res.partner')
        p_ids = partner_obj.search([('name', '=', 'ESC'), ('active', '=', False)])
        if p_ids:
            partner_obj.write(p_ids, {'active': True})


# Replicable class to create project n
class projectn_creation(client_creation):
    name_format = "%(db)s_HQ%(ppind)dC%(pind)dP%(ind)d"

    @unittest.skipIf(skipGroups, "Group creation desactivated")
    def test_30_make_groups_coordo(self):
        self.add_to_group('OC_%02d' % self.hq.index, 'OC')
        self.add_to_group('Mission %s-%s' % (self.hq.index, self.parent.index), 'MISSION')
        self.add_to_group('HQ%s + Mission %s' % (self.hq.index, self.parent.index), 'HQ + MISSION')
        entities = Synchro.get('sync.server.entity')
        entity_ids = entities.search([('name','=',self.db.name)])
        entities.validate_action(entity_ids)

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
if not hasattr(config, 'instance_tree') or not config.instance_tree:
    config.instance_tree = {}
    for i in range(1, hq_count+1):
        config.instance_tree['HQ%d'%i] = {}
        for ci in range(1, coordo_count+1):
            config.instance_tree['HQ%d'%i]['C%d'%ci] = []
            for pi in range(1, project_count+1):
                config.instance_tree['HQ%d'%i]['C%d'%ci].append('P%d'%pi)
else:
    hq_count = len(config.instance_tree.keys())
    coordo_count = max([len(x.values()) for x in config.instance_tree.values()])

hq_index = 0
for hq, coordos in config.instance_tree.iteritems():
    hq_index += 1
    test_cases.append( type("HQ%d_creation" % hq_index, (hqn_creation,unittest.TestCase), {
        'prefix' : 'HQ%s'%hq_index,
        'index' : hq_index,
    }) )
    # Make testcase visible for importation
    globals()[test_cases[-1].__name__] = test_cases[-1]

    coordo_index = 0
    # Create Coordo classes
    for coordo in sorted(coordos.keys()):
        coordo_index += 1
        test_cases.append( type("HQ%d_C%d_creation" % (hq_index, coordo_index), (coordon_creation,unittest.TestCase), {
            'prefix' : 'C%s%s' % (hq_index, coordo_index),
            'index' : coordo_index,
            'parent' : globals()["HQ%d_creation" % hq_index],
        }) )
        test_cases[-1].hq = test_cases[-1].parent
        # Make testcase visible for importation
        globals()[test_cases[-1].__name__] = test_cases[-1]

        project_index = 0
        # Create Project classes
        for pi in coordos[coordo]:
            project_index += 1
            test_cases.append( type("HQ%d_C%d_P%d_creation" % (hq_index, coordo_index, project_index), (projectn_creation,unittest.TestCase), {
                'prefix' : 'P%s%s%s'%(hq_index, coordo_index, project_index),
                'index' : project_index,
                'parent' : globals()["HQ%d_C%d_creation" % (hq_index, coordo_index)],
            }) )
            test_cases[-1].hq = test_cases[-1].parent.parent
            # Make testcase visible for importation
            globals()[test_cases[-1].__name__] = test_cases[-1]


# Push last_sync test at last
test_cases.append(last_sync)

# activate inter partners
test_cases.append(activate_inter_partner)

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
