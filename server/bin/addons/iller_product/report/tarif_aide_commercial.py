# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution	
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more detaila
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from report import report_sxw
from osv import osv
import pooler

class tarif_aide_commercial(report_sxw.rml_parse):

        def __init__(self, cr, uid, name, context):
            super(tarif_aide_commercial, self).__init__(cr, uid, name, context)
            self.localcontext.update({
                'liste': self._affi_tarif
            })

        def _affi_tarif(self):
            tarif = self.localcontext.get('data',{}).get('form',{}).get('liste',[])
            return tarif 

report_sxw.report_sxw('report.tarif.aide.commercial','product.pricelist','addons/iller_product/report/tarif_aide_commercial.rml',parser=tarif_aide_commercial)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
