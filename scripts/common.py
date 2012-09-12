from sys import stdout, stderr, exit

from xmlrpclib import Fault
import openerplib

from tests.openerplib import db

import config

server, client = None, None

stdout.write("Establishing connections to the server... ")
stdout.flush();
try:
    server = openerplib.get_connection(hostname=config.server_host, port=config.server_port)
    server.get_service('db').list()
except:
    stdout.write("failed!\n")
    stderr.write("Unable to connect to OpenERP Sync Server at %s:%s\n" % (config.server_host, config.server_port,))
    exit(1)
try:
    client = openerplib.get_connection(hostname=config.client_host, port=config.client_port)
    client.get_service('db').list()
except:
    stdout.write("failed!\n")
    stderr.write("Unable to connect to OpenERP Sync Client at %s:%s\n" % (config.client_host, config.client_port,))
    exit(1)
stdout.write("done.\n")

def sync(test, db):
    if not db.get('sync.client.entity').sync():
        test.failed('Synchronization process of database "%s" failed!' % (db.db_name,))
        monitor = db.get('sync.monitor')
        ids = monitor.search([], 0, 1, '"end" desc')
        test.traceback = monitor.read(ids, ['error'])[0]['error']
        return False
    else:
        return True

class db_instance(type):
    instance = None

    def connect(cls, login=None, password=None):
        #stderr.write("\n!! Initialization required "+cls.name+" !!\n")
        u = login if login else config.user_login
        p = password if password else (config.admin_password if login == 'admin' else config.user_password)
        cls.instance = db(cls.server, cls.name, user=u, password=p)
        try:
            if hasattr(cls, 'synchro') and cls.synchro:
                synchro_serv = cls.instance.get('sync.client.sync_server_connection')
                ids = synchro_serv.search([])
                if ids: synchro_serv.write(ids, cls.synchro)
                else: ids = [synchro_serv.create(cls.synchro)]
                synchro_serv.connect(ids)
        except:
            pass
        return cls

    def __getattr__(cls, attr):
        if not cls.instance: raise AttributeError("Class %s is not connected!" % (cls.name,))
        real_attr = getattr(cls.instance, attr)
        return real_attr

class Synchro:
    __metaclass__ = db_instance

    server = server
    name = "%s_%s_SYNCHRO" % (config.version, config.prefix)
    shortname = "%s_SYNCHRO" % (config.prefix)

    def __init__(self):
        raise Exception, 'This class must not be instanced'

class HQ:
    __metaclass__ = db_instance

    server = client
    name = "%s_%s_HQ" % (config.version, config.prefix)
    shortname = "%s_HQ" % (config.prefix)
    synchro = {
        'protocol' : 'netrpc',
        'host' : config.server_host,
        'port' : config.netrpc_port,
        'database' : Synchro.name,
        'login' : name,
        'password' : name,
    }

    def __init__(self):
        raise Exception, 'This class must not be instanced'

class Coordo:
    __metaclass__ = db_instance

    server = client
    name = "%s_%s_COORDO" % (config.version, config.prefix)
    shortname = "%s_COORDO" % (config.prefix)
    synchro = {
        'protocol' : 'netrpc',
        'host' : config.server_host,
        'port' : config.netrpc_port,
        'database' : Synchro.name,
        'login' : name,
        'password' : name,
    }

    server = client
    def __init__(self):
        raise Exception, 'This class must not be instanced'

class Project:
    __metaclass__ = db_instance

    server = client
    name = "%s_%s_PROJECT" % (config.version, config.prefix)
    shortname = "%s_PROJECT" % (config.prefix)
    synchro = {
        'protocol' : 'netrpc',
        'host' : config.server_host,
        'port' : config.netrpc_port,
        'database' : Synchro.name,
        'login' : name,
        'password' : name,
    }

    server = client
    def __init__(self):
        raise Exception, 'This class must not be instanced'

class Project2:
    __metaclass__ = db_instance

    server = client
    name = "%s_%s_PROJECT2" % (config.version, config.prefix)
    shortname = "%s_PROJECT2" % (config.prefix)
    synchro = {
        'protocol' : 'netrpc',
        'host' : config.server_host,
        #'port' : config.server_port, ## XMLRPC port
        'port' : config.netrpc_port,
        'database' : Synchro.name,
        'login' : name,
        'password' : name,
    }

    server = client
    def __init__(self):
        raise Exception, 'This class must not be instanced'

