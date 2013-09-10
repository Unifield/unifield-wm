#!/usr/bin/env python
#-*- encoding:utf-8 -*-
###########################################################################
#    This program is free software: you can redistribute it and/or modify #
#    it under the terms of the GNU General Public License as published by #
#    the Free Software Foundation, either version 3 of the License, or    #
#    (at your option) any later version.                                  #
#                                                                         #
#    This program is distributed in the hope that it will be useful,      #
#    but WITHOUT ANY WARRANTY; without even the implied warranty of       #
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the        #
#    GNU General Public License for more details.                         #
#                                                                         #
#    You should have received a copy of the GNU General Public License    #
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.#
#                                                                         #
#    Author : Bruno GUIDOU                                                #
#    Company: TeMPO Consulting <http://www.tempo-consulting.fr>           #
#    Version: 1.0                                                         #
#    Date: 14/12/2009 17:56                                               #
#    Description: This file allows you to connect with XML-RPC on the     #
#                 OpenERP server                                          #
###########################################################################

import xmlrpclib


# Un appel a la signature suivante:
# Object.execute(dbname, uid, pwd, model, action, *args)
# avec:
#   - model, le modele sur lequel s'efectue l'action, ex: 'product.product'
#   - action, une action parmi: 'create', 'search', 'read', 'write', 'unlink'
#   - args, depend de l'action
# Soit les appels possibles:
#   create: Object.execute(dbname, uid, pwd, model, 'create', data), data = {'name': 'Bruno Guidou','lang': 'fr_FR'}
#   search: Object.execute(dbname, uid, pwd, model, 'search', args), args = [('vat', '=', 'ZZZZZZ')]
#   read: Object.execute(dbname, uid, pwd, model, 'read', ids, fields), fields = ['name', 'active', 'vat', 'ref'] et ids : list of id
#   write: Object.execute(dbname, uid, pwd, model, 'write', ids, values), values = {'vat': 'ZZ1ZZZ'} et ids : list of id
#   unlink: Object.execute(dbname, uid, pwd, model, 'unlink', *args), ids : list of id


class ERPProxy(object):
    def __init__(self, username='', pwd='', dbname='', host='localhost', port='8069'):
        self.user = username
        self.pwd = pwd
        self.dbname = dbname
        self.host = host
        self.port = port
        self.proxy_url = 'http://' + host + ':' + port + '/xmlrpc'

    def setup(self):
        self.setup_uid()
        self.setup_object()
        self.setup_wizard()
        
    def setup_uid(self):
        Common = xmlrpclib.ServerProxy (self.proxy_url + '/common')
        self.uid = Common.login(self.dbname, self.user, self.pwd)

    def setup_object(self):
        try:
            self.Object = xmlrpclib.ServerProxy(self.proxy_url + '/object')
        except Exception, e:
            print e

    def setup_wizard(self):
        """
        Permet d'accéder à l'interface Wizard d'OpenERP
        """
        try:
            self.Wizard = xmlrpclib.ServerProxy(self.proxy_url + '/wizard')
        except Exception, e:
            print e

    def create(self, model, data):
        """
        data = {'name': 'Bruno Guidou','lang': 'fr_FR'}
        """
        object_id = self.Object.execute(self.dbname, self.uid, self.pwd, model, 'create', data)
        return object_id

    def search(self, model, *args):
        """
        args = [('vat', '=', 'ZZZZZZ')]
        """
        object_ids = self.Object.execute(self.dbname, self.uid, self.pwd, model, 'search', *args)
        return object_ids
        
    def read(self, model, ids, fields):
        """
        fields = ['name', 'active', 'vat', 'ref'] and ids : list of id
        """
        object_ids = self.Object.execute(self.dbname, self.uid, self.pwd, model, 'read', ids, fields)
        return object_ids

    def write(self, model, ids, values):
        """
        values = {'vat': 'ZZ1ZZZ'} and ids : list of id
        """
        object_ids = self.Object.execute(self.dbname, self.uid, self.pwd, model, 'write', ids, values)
        return object_ids

    def call_method(self, model, name, *args):
        """
        name = 'method_name' and args : list of args
        """
        object_ids = self.Object.execute(self.dbname, self.uid, self.pwd, model, name, *args)
        return object_ids

    def unlink(self, model, *args):
        """
        ids : list of id
        """
        object_ids = self.Object.execute(self.dbname, self.uid, self.pwd, model, 'unlink', *args)
        return object_ids

    def create_wizard(self, model):
        """
        model = 'nom du wizard'
        """
        wizard_id = self.Wizard.create(self.dbname, self.uid, self.pwd, model)
        return wizard_id

    def appel_wizard(self, model, id, data, state, context):
        """
        Étape du wizard
        data = {'model': model, 'form': form, 'id': id, 'report_type': 'pdf', 'ids': ids}
        state = 'end' (par exemple)
        context = {'lang': 'fr_FR', 'client': 'web'}
        """
        if not 'model' in data:
            data.update({'model': model})
        if not 'id' in data:
            data.update({'id': id})
        if not 'ids' in data:
            data.update({'ids': [id]})
        if not 'report_type' in data:
            data.update({'report_type': 'pdf'})
        wizard_id = self.Wizard.execute(self.dbname, self.uid, self.pwd, id, data, state, context)


