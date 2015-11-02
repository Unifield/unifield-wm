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


import base64
from tools.translate import _
import os
from report import report_sxw
import pooler


class msf_archive_content(report_sxw.report_sxw):
    def create(self, cr, uid, ids, data, context=None):
        archive = pooler.get_pool(cr.dbname).get('msf.archive')
        d = archive.read(cr, uid, ids[0], ['data'], context=context)
        return (d['data'], 'zip')

msf_archive_content('report.msf.archive.content', 'msf.archive', False, parser=False)

