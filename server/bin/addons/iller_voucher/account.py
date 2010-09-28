#!/usr/bin/env python
# -*- coding: UTF8 -*-

from osv import osv
from osv import fields


class account_move_line(osv.osv):
    '''
        Ajout du champ 'Code du partenaire' sur les lignes d'écriture
    '''
    _name = 'account.move.line'
    _inherit = 'account.move.line'

    _columns = {
        'partner_code': fields.related('partner_id', 'ref', 
                                       string='Code partenaire',
                                       type='char', store=True, size=64),
    }

account_move_line()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

