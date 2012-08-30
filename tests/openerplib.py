from os import path
from time import sleep
import re

import csv

from xmlrpclib import Fault
openerplib = __import__('openerplib')

import config

try:
    import ipdb as pdb
except:
    import pdb

class db(object):
    def __init__(self, server, db_name, user=None, password=None, server_password=None):
        self.server = server
        try:
            self.server_password = config.db_password
        except:
            self.server_password = None
        finally:
            if server_password: self.server_password = server_password
        self.db_name = db_name
        self.service = server.get_service('db')
        if user: self.connect(user, password)

    def exec_workflow(self, model, method, ids):
        return self.server.get_service('object').exec_workflow(
            self.server.database, self.server.user_id, self.server.password,
            model, method, ids)

    def connect(self, login, password):
        self.server = openerplib.get_connection(hostname=self.server.connector.hostname, port=self.server.connector.port, database=self.db_name, login=login, password=password)
        return self

    def create_db(self, password, demo=False, lang='en_US', wait=False):
        if not self.server_password: raise Exception, "The server password is needed for this operation"
        self.id = self.service.create(self.server_password, self.db_name, demo, 'en_US', password)
        if wait: self.wait()
        return self

    create = create_db

    def wait(self):
        if not self.server_password: raise Exception, "The server password is needed for this operation"
        while True:
            try:
                running = self.service.get_progress(self.server_password, self.id)
                if not running: break
                sleep(1)
            except:
                break
        return self

    def drop(self):
        if not self.server_password: raise Exception, "The server password is needed for this operation"
        ## TODO does'n handle database current access prevent dropping
        #self.service.drop(self.server_password, self.db_name)
        if self.db_name in self.service.list():
            self.service.drop(self.server_password, self.db_name)
        return self

    def get(self, model):
        return self.server.get_model(model)

    def wizard(self, model, data):
        return wizard(self, model, data)

    def ref(self, xml_id, index=0):
        return ref(xml_id).get(self)

    def module(self, name, index=0):
        return module(self, name, index)

    def action_done(self, action_id):
        proxy = self.get('ir.actions.todo')
        ids = proxy.search([('action_id', '=', action_id)])
        if ids: proxy.write(ids, {'state' : 'done'})

    def user(self, login):
        return user(self, login)

    def group(self, name):
        return group(self, name)

    def search_data(self, model, data, domain=None, action=None, active='active', pdb=False):
        if isinstance(data, dict):
            searchDomain = [(field,'=',value) for (field,value) in data.items() if value]
        elif isinstance(data, (list,tuple)):
            searchDomain = list(data)
        else:
            raise NotImplementedError("Cannot transform %s (of type %s) to a domain (list)" % (data, type(data).__name__))
        if domain:
            searchDomain += list(domain)
        if active == 'unactive': searchDomain.append(('active','=',0))
        elif active == 'both': searchDomain.extend(['|',('active','=',0),('active','=',1)])
        elif not active == 'active': raise Exception, "'active' prameter must be one of these: active, unactive or both"
        proxy = self.get(model)
        ids = proxy.search(searchDomain)
        if not ids and pdb:
            pdb.set_trace()
        if action == 'unlink': return proxy.unlink(ids) if ids else True
        elif action == 'test': return bool(ids)
        else: return ids
        
   
    test = lambda self, model, data, **o: self.search_data(model, data, action='test', **o)
    clean = lambda self, model, data, **o: self.search_data(model, data, action='unlink', **o)
 
    def write(self, model, ids_or_domain, data):
        if all([isinstance(x, (tuple, list)) for x in ids_or_domain]):
            ids = self.get(model).search(ids_or_domain)
        elif isinstance(ids_or_domain, dict):
            ids = self.search_data(model, ids_or_domain)
        else:
            ids = ids_or_domain
        if ids and not self.get(model).write(ids, data):
            return 0
        return len(ids)

    def activate(self, model, domain, state=1):
        proxy = self.get(model)
        search_domain = [('active','=',1-state)] + domain
        ids = proxy.search(search_domain)
        proxy.write(ids, {'active':state})
        return len(ids)

    def desactivate(self, model, domain):
        return self.activate(model, domain, 0)

    def load_datas(self, filepath):
        datas = []
        if path.isfile(filepath):
            if filepath[-4:] == '.csv':
                ch = csv.reader(open(filepath, 'rb'), quotechar='"', delimiter=',')
                fields = ch.next()
                datetime_re = re.compile(r"^\d\d\d\d-\d\d-\d\d( \d\d:\d\d:\d\d)?$")
                for values in ch:
                    evaluated_values = []
                    for v in values:
                        try:
                            if datetime_re.match(v): raise Exception
                            evaluated_values += [eval(v)]
                        except:
                            evaluated_values += [eval('"""'+v+'"""')]
                    datas.append(dict(zip(fields, evaluated_values)))
            elif filepath[-4:] == '.xml':
                raise Exception, 'While importing XML file: Not yet implemented'
            else:
                raise Exception, 'Cannot import file "%s": unrecognized file type!' % (filepath,)
        else:
            raise IOError, 'Can\'t access to file "%s", check read permission!' % (filepath,)
        return datas

    def Import(self, model, datas, mode='init'):
        if type(datas) == dict:
            fields = datas.keys()
            datas = [datas.values()]
        elif not type(datas) == list:
            raise Exception, 'Cannot import data: datas must be a list of dict!'
        else:
            fields = []
            for i in datas:
                fields = set(list(fields) + i.keys())
            fields = list(fields)
            old_datas = datas
            datas = []
            for i in old_datas:
                datas.append([i.get(field, None) for field in fields])
        for data in datas:
            for i, v in enumerate(data):
                data[i] = str(data[i])
                #if v == None: data[i] = False
                #elif type(v) == bool: data[i] = 1 if v else 0
        if 'reconcile note' in fields: ipdb.set_trace()
        result, rows, warning_msg, dummy = self.get(model).import_data(fields, datas, mode)
        if result == -1:
            raise Exception, "Unable to import data: "+str(warning_msg)
        return self

class ref(object):
    def __init__(self, xml_id, index=0):
        self.xml_id = xml_id
        self.index = 0

    def get(self, db, refetch=False):
        try:
            if refetch: raise AttributeError
            return self.value
        except AttributeError:
            module, xml_id = self.xml_id.split('.')
            model, i = db.get('ir.model.data').get_object_reference(module, xml_id)
            self.value = db.get(model).read([i], ['id'])[0]
            return self.value['id']

class wizard(object):
    def __init__(self, db, model, data):
        for k, v in data.items():
            if isinstance(v, ref):
                data[k] = v.get(db)
        self.proxy = db.get(model)
        self.id = self.proxy.create(data)

    def __getattr__(self, attr):
        real_attr = getattr(self.proxy, attr)
        def foo(*args):
            return real_attr([self.id], *args)
        return foo

    def data(self, *attrs):
        data = self.proxy.read([self.id], attrs)
        if len(attrs) == 1: return data[0][attrs[0]]
        else: return data[0]

class module(object):
    def __init__(self, db, name, index=0):
        self.db = db
        self.module_proxy = db.get('ir.module.module')
        if name == 'all':
            name = 'base'
        self.ids = self.module_proxy.search([('name','=',name)])
        if not self.ids:
            raise Exception, "Unable to find module %s!" % (name,)

    def remove(self):
        self.expect = 'uninstalled'
        self.module_proxy.button_uninstall(self.ids)
        return self

    uninstall = remove

    def install(self):
        self.expect = 'installed'
        self.module_proxy.button_install(self.ids)
        return self

    def upgrade(self):
        self.expect = 'installed'
        self.module_proxy.button_upgrade(self.ids)
        return self

    def do(self):
        self.db.get('base.module.upgrade').upgrade_module([])
        if self.module_proxy.search([('id','in',self.ids),('state','=',self.expect)], 0, False, False, True) == len(self.ids):
            raise Exception, "Modules modifications not applied"
        return self

class user(object):
    def __init__(self, db, login):
        self.db = db
        self.users = db.get('res.users')
        self.login = login
        try: self.id = self.users.search([('login','=',login)])[0]
        except: self.id = None

    def delGroups(self, *groups):
        if not self.id: raise Exception, 'Cannot remove groups to unknown user: '+self.login
        group_ids = [i.id if type(i) == group else group(self.db, i).id for i in groups]
        if None in group_ids: raise Exception, 'Cannot find some groups in this list: '+', '.join(groups)
        group_changes = [(3,i,) for i in group_ids]
        self.users.write([self.id],{'groups_id':group_changes})
        return self

    def addGroups(self, *groups):
        if not self.id: raise Exception, 'Cannot add groups to unknown user: '+self.login
        group_ids = [i.id if type(i) == group else group(self.db, i).id for i in groups]
        if None in group_ids: raise Exception, 'Cannot find some groups in this list: '+', '.join(groups)
        group_changes = [(4,i,) for i in group_ids]
        self.users.write([self.id],{'groups_id':group_changes})
        return self

    def add(self, password, name=None):
        if not self.id:
            self.id = self.users.create({'login':self.login,'name':(name or self.login),'password':password,})
        return self

    def exists(self):
        return bool(self.id)

class group(object):
    def __init__(self, db, name):
        self.db = db
        self.groups = db.get('res.groups')
        self.name = name
        try: self.id = self.groups.search([('name','=',name)])[0]
        except: self.id = None

    def delUsers(self, *users):
        if not self.id: self.add()
        user_ids = [i.id if type(i) == user else user(self.db, i).id for i in users]
        if None in user_ids: raise Exception, 'Cannot find some users in this list: '+', '.join(users)
        user_changes = [(3,i,) for i in user_ids]
        self.groups.write([self.id],{'users':user_changes})
        return self

    def addUsers(self, *users):
        if not self.id: self.add()
        user_ids = [i.id if type(i) == user else user(self.db, i).id for i in users]
        if None in user_ids: raise Exception, 'Cannot find some users in this list: '+', '.join(users)
        user_changes = [(4,i,) for i in user_ids]
        self.groups.write([self.id],{'users':user_changes})
        return self

    def add(self):
        if not self.id:
            self.id = self.groups.create({'name':self.name,})
        return self

    def exists(self):
        return bool(self.id)

