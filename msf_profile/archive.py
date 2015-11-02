# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2011 MSF, TeMPO consulting
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from osv import osv
from osv import fields
import base64
from tools.translate import _
import os
import tools
import time
import tempfile
import zipfile


class msf_archive(osv.osv):
    _name = 'msf.archive'
    _order = 'id desc'

    _columns = {
        'name': fields.datetime('Archive Generation Date', required=True),
        'maxdate': fields.date('Archive records older than', required=True),
        'data': fields.binary('Archive'),
    }

    _defaults = {
        'name': lambda *a: time.strftime('%Y-%m-%d %H:%M:%S'),
    }

    def archive(self, cr, uid, date):
        condition = {'date': date}
        if self.pool.get('sync.server.entity'):
            cr.execute('select min(last_sequence) from sync_server_entity')
            condition['min_seq'] = cr.fetchone()[0]
            to_archive = [
                (
                    'sync_server_entity_rel',
                    """
                        left join sync_server_update on sync_server_entity_rel.update_id = sync_server_update.id
                        left join sync_server_sync_rule r on r.id = sync_server_update.rule_id
                        where
                        r.is_master= 'f' and
                        sync_server_update.create_date < '%(date)s' and
                        sync_server_update.sequence < %(min_seq)d

                    """
                ),
                (
                    'sync_server_update',
                    """
                        left join sync_server_sync_rule r on r.id = sync_server_update.rule_id
                        where
                        r.is_master= 'f' and
                        sync_server_update.create_date < '%(date)s' and
                        sync_server_update.sequence < %(min_seq)d
                    """

                ),
            ]
        else:
            to_archive = [
                # table, sql condition
                (
                    'sync_client_update_received',
                    "where create_date < '%(date)s' and run='t'",
                ),
                (
                    'sync_client_update_to_send',
                    "where create_date < '%(date)s' and sent='t'",
                )
            ]

        if os.name == 'nt' and not os.environ.get('PGPASSWORD', ''):
            os.environ['PGPASSWORD'] = tools.config['db_password']

        tmpdir = tempfile.mkdtemp(prefix='/home/jf/Unifield/tmp')
        to_zip = []
        for arch in to_archive:
            schema_file = os.path.join(tmpdir, '%s.schema'%arch[0])
            cmd = ['pg_dump', '--format=p', '-s', '-t', arch[0], '-f', schema_file]
            if tools.config['db_user']:
                cmd.append('--username=' + tools.config['db_user'])
            if tools.config['db_host']:
                cmd.append('--host=' + tools.config['db_host'])
            if tools.config['db_port']:
                cmd.append('--port=' + str(tools.config['db_port']))
            cmd.append(cr.dbname)
            tools.exec_pg_command(*tuple(cmd))
            data_file = os.path.join(tmpdir,"%s.data" % arch[0])
            f = open(data_file, "wb")
            query = "select "+arch[0]+".* from "+arch[0]+" "+arch[1]%condition
            cr.copy_expert("copy ("+query+") to STDOUT WITH CSV HEADER", f)
            f.close()
            to_zip += [schema_file, data_file]
        if os.name == 'nt':
            os.environ['PGPASSWORD'] = ''
        archive_name = tempfile.TemporaryFile(mode='w+b')
        archive_zip = zipfile.ZipFile(archive_name, 'w', zipfile.ZIP_DEFLATED)
        for z in to_zip:
            archive_zip.write(z, os.path.basename(z))
        archive_zip.close()
        archive_name.seek(0)
        self.create(cr, uid, {
            'maxdate': date,
            'data': archive_name.read(),
        })
        archive_name.close()
        for arch in to_archive:
            query = "delete from "+arch[0]+ " "+arch[1]%condition
            cr.execute(query)
        return True

    def get_content(self, cr, uid, ids, context=None):
        name = self.read(cr, uid, ids[0], ['name'])['name']
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'msf.archive.content',
            'datas': {'ids': [ids[0]], 'target_filename': name}
        }

msf_archive()
