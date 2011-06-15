#!/usr/bin/env python
#-*- encoding:utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution    
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    Tempo Consulting (<http://www.tempo-consulting.fr/>).
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

from report import report_sxw
from osv import osv
import time
import locale

from datetime import date, datetime, timedelta

class edition_article(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(edition_article, self).__init__(cr, uid, name, context)
        self.total_categ = {}
        self.localcontext.update({
            'getLines': self.get_lines,
            'time': time,
            'locale': locale,
        })

    def get_lines(self):
        res_ids = self.pool.get('stats.edition.article').search(self.cr, self.uid, [])

        res = self.pool.get('stats.edition.article').read(self.cr, self.uid, res_ids, [])

        return res

report_sxw.report_sxw('report.edition.article', 'stats.edition.article', 'addons/iller_stats/report/edition_article.rml', parser=edition_article)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
