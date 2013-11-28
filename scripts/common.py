from sys import stdout, stderr, exit

from xmlrpclib import Fault
import openerplib103 as openerplib

from tests.openerplib import db

import config
import os
from bzrlib.workingtree import WorkingTree
from bzrlib.branch import BzrBranch


__all__ = ['server', 'client', 'db_instance', 'Synchro', 'HQ', 'Coordo', 'Project', 'Project2', 'check_lp_update', 'get_revno_from_path']

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

class db_instance(object):
    instance = None

    def __init__(self, server, name, synchro):
        self.server, self.name, self.synchro = server, name, synchro

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

Synchro = db_instance(
    server=server,
    name="%s_SYNC_SERVER" % (config.prefix),
    synchro=None,
)

hq_name = "%s_HQ_01" % (config.prefix)
HQ = db_instance(
    server=client,
    name=hq_name,
    synchro={
        'protocol' : 'netrpc',
        'host' : config.server_host,
        'port' : config.netrpc_port,
        'database' : Synchro.name,
        'login' : hq_name,
        'password' : hq_name,
    }
)

coordo_name = "%s_COORDO_01" % (config.prefix)
Coordo = db_instance(
    server=client,
    name=coordo_name,
    synchro={
        'protocol' : 'netrpc',
        'host' : config.server_host,
        'port' : config.netrpc_port,
        'database' : Synchro.name,
        'login' : coordo_name,
        'password' : coordo_name,
    }
)

project_name = "%s_PROJECT_01" % (config.prefix)
Project = db_instance(
    server=client,
    name=project_name,
    synchro={
        'protocol' : 'netrpc',
        'host' : config.server_host,
        'port' : config.netrpc_port,
        'database' : Synchro.name,
        'login' : project_name,
        'password' : project_name,
    }
)

project2_name = "%s_PROJECT_02" % (config.prefix)
Project2 = db_instance(
    server=client,
    name=project2_name,
    synchro={
        'protocol' : 'netrpc',
        'host' : config.server_host,
        'port' : config.netrpc_port,
        'database' : Synchro.name,
        'login' : project2_name,
        'password' : project2_name,
    }
)

def get_lp_branch(wk):
    if isinstance(wk.branch, BzrBranch):
        parent = wk.branch.get_parent()
        if parent is None:
            parent = wk.branch.get_bound_location()
    else:
        parent = wk.branch.bzrdir.root_transport.base
    return parent

def get_revno_from_path(path):
    if os.path.islink(path):
        path = os.path.realpath(path)
    wt = WorkingTree.open(path)
    lr = wt.last_revision()
    try:
        revno = wt.branch.revision_id_to_dotted_revno(lr)[0]
    except:
        revno = False
    rev = wt.branch.repository.get_revision(lr)
    return {'revno': revno, 'lastmsg': rev.get_summary(), 'lpurl': get_lp_branch(wt)}

def check_lp_update(update=False):
    to_update = []
    for ad in config.addons:
        src_path = os.path.join(config.source_path, ad)
        info = get_revno_from_path(src_path)

        br = BzrBranch.open(info['lpurl'])
        lr = br.last_revision()
        revno = br.revision_id_to_dotted_revno(lr)[0]

        if revno > info['revno']:
            to_update.append(ad)
            if update:
                wt = WorkingTree.open(src_path)
                wt.pull(br)
    return to_update
