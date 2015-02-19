# -*- coding: utf-8 -*-

from osv import osv
from osv import fields
from osv import orm
from tools.translate import _
import sql_db
import logging

import psycopg2
import psycopg2.extras
import decimal

class ir_actions_server(osv.osv):
    _inherit ='ir.actions.server'
    _name = 'ir.actions.server'

    _columns = {
        'empty_ids': fields.boolean('Do not required selection of records'),
    }

    def run(self, cr, uid, ids, context=None):
        # ack to allow click on the action without any selected record
        if context is None:
            context = {}
        if not context.get('active_id'):
            context['active_id'] = 1
        return super(ir_actions_server, self).run(cr, uid, ids, context)
ir_actions_server()


class instance():
    def __init__(self, name, db=False, level=False, parent=False):
        self.name = name
        self.level = level
        if not db:
            db = name
        self.db = db
        self.parent = parent
        self.children_name = []
        self.all_parents = []
        while parent:
            parent.children_name.append(self.name)
            self.all_parents.append(parent)
            parent = parent.parent
        db_conn = psycopg2.connect("%sdbname=%s" % (sql_db._dsn, db))
        self.cr = db_conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        self.target_cc = []

    def __del__(self):
        self.cr.close()

class msf_instance(osv.osv):
    _name = 'msf.instance'
    _inherit = 'msf.instance'
    _columns = {
        'dbname': fields.char('DB Name', size=64),
    }
msf_instance()

class account_period(osv.osv):
    _name = 'account.period'
    _inherit = 'account.period'
    _columns = {
        'comparison_done': fields.boolean('Comparison done')
    }
account_period()

class sync_compare(osv.osv):
    _name = 'sync.compare'
    _logger = logging.getLogger('sync.compare')
    _columns = {
        'object': fields.char('Object', size=256, readonly=1),
        'from_instance': fields.char('From instance', size=256, readonly=1),
        'to_instance': fields.char('To instance', size=256, readonly=1),
        'xmlid': fields.char('Xmlid', size=512, readonly=1),
        'object_info': fields.char('Line info', size=512, readonly=1),
        'error': fields.text('Error', readonly=1),
        'ack': fields.boolean('Ack'),
        'note': fields.text('Note'),
        'type': fields.selection([('mismatch', 'Mismatch'), ('not_sync', 'Not Sync')], 'Type', readonly=1)
    }

    def compare(self, cr, uid, periods_name):
        instances = self.init_db(cr, uid)
        self.gl_balance(cr, uid, instances, periods_name)
        self.start_compare_aji(cr, uid, instances, periods_name)
        self.start_compare_ji(cr, uid, instances, periods_name)
        p_obj = self.pool.get('account.period')
        p_ids = p_obj.search(cr, uid, [('name', 'in', periods_name)])
        p_obj.write(cr, uid, p_ids, {'comparison_done': 1})
        return True

    def init_db(self, cr, uid, context=None):
        instances = {}
        inst_obj = self.pool.get('msf.instance')
        for level in ['section', 'coordo', 'project']:
            ids = inst_obj.search(cr, uid, [('level', '=', level)])
            for inst in inst_obj.browse(cr, uid, ids):
                parent = False
                if inst.parent_id:
                    parent = instances[inst.parent_id.name]
                if not inst.dbname:
                    self._logger.warn('DB %s ignored' % inst.name)
                else:
                    instances[inst.name] = instance(inst.name, db=inst.dbname, level=level, parent=parent)
        self._set_target_cc(cr, uid, instances)
        return instances

    def _set_target_cc(self, cr, uid, instances):
        inst = instances.values()[0]
        inst.cr.execute('''select cc.code as cc_name, instance.name as instance_name from
account_target_costcenter t
inner join msf_instance instance on instance.id = t.instance_id
inner join account_analytic_account cc on cc.id = t.cost_center_id
where t.is_target = 't' ''')
        for t in inst.cr.fetchall():
            if t['instance_name'] not in instances:
                self._logger.warn("Instance unknown %s" % t['instance_name'])
            else:
                instances[t['instance_name']].target_cc.append(t['cc_name'])

    def get_all_mission_closed_period(self, cr, uid, instances=False, context=None):
        if not instances:
            instances = self.init_db(cr, uid, context)
        closed_period = []
        for inst in instances.values():
            closed = []
            add_sql = ''
            if inst.db == cr.dbname:
                add_sql = " and COALESCE(comparison_done, 'f') = 'f' "

            inst.cr.execute("select name from account_period where state in ('mission-closed','done')"+add_sql)
            for cl in inst.cr.fetchall():
                closed.append(cl['name'])
            closed_period.append(closed)
        return list(set.intersection(*[set(x) for x in closed_period]))

    def _get_filter_closed_period(self, cr, uid, instances, periods_name):
        inst = instances.values()[0]
        inst.cr.execute("select date_stop, date_start from account_period where state in ('mission-closed', 'done') and name in %s", (tuple(periods_name),))
        if not inst.cr.rowcount:
            raise osv.except_osv(_('Error!'), 'No period closed')
        sql_add = []
        for p in inst.cr.fetchall():
            sql_add.append(" l.date >= '%s' and l.date <= '%s' " % (p['date_start'], p['date_stop']))

        return ' OR '.join(sql_add)

    def is_diff(self, a, b):
        if a != b:
            if a is None and not b:
                return False
            if b is None and not a:
                return False
            if isinstance(a, (float, decimal.Decimal)) and isinstance(b, (float, decimal.Decimal)) and abs(b-a) < 0.001:
                return False
            return True
        return False

    def start_compare_aji(self, cr, uid, instances, periods_name):
        sql_date = self._get_filter_closed_period(cr, uid, instances, periods_name)
        query_aji = """select
d.name as xmlid, fund.code as funding_pool, l.amount, l.amount_currency, l.correction_date, l.code, cc.code as cost_center, curr.name as currency, l.date, dest.code as destination, l.document_date, acc.code as gl_account, l.is_reallocated, l.is_reversal, journal.name as journal, l.name, l.ref, l.source_date, l.entry_sequence
from account_analytic_line l
inner join account_analytic_account fund on fund.id = l.account_id
inner join account_analytic_account cc on cc.id = l.cost_center_id
inner join res_currency curr on curr.id = l.currency_id
inner join account_analytic_account dest on dest.id = l.destination_id
inner join account_account acc on acc.id = l.general_account_id
inner join account_analytic_journal journal on journal.id = l.journal_id
inner join ir_model_data d on d.model = 'account.analytic.line' and d.res_id = l.id
where
cc.code in %s and
imported_commitment = 'f' and
fund.category = 'FUNDING' and
( """ + sql_date + """ ) """

        for level in instances.values():
            target_aji = {}
            # Get the AJIs targeted to the instance
            if level.target_cc:
                level.cr.execute(query_aji, (tuple(level.target_cc), ))
                for al in level.cr.fetchall():
                    target_aji[al['xmlid']] = al
            # Compare those AJIs, with parent levels
            for parent in level.all_parents:
                self.compare_aji(cr, uid, level, target_aji, parent, "up", query_aji)

            # Get AJIs targeted to other instances
            for instance in instances.values():
                if instance != level and instance.target_cc:
                    other_aji = {}
                    level.cr.execute(query_aji, (tuple(instance.target_cc), ))
                    for al in level.cr.fetchall():
                        other_aji[al['xmlid']] = al
                    if other_aji:
                        self.compare_aji(cr, uid, level, other_aji, instance, "cross", query_aji)

    def compare_aji(self, cr, uid, from_instance, list_aji, to_instance, sync_type, query_aji):
        tmp = list_aji.copy()
        if sync_type == 'cross':
            target_cc = tuple(to_instance.target_cc)
            target_str = 'target %s' % to_instance.name
            query = query_aji + ' and d.name in %s '
            to_instance.cr.execute(query,(target_cc, tuple(list_aji.keys())))
        else:
            target_cc = tuple(from_instance.target_cc)
            target_str = 'target %s' % from_instance.name
            query = query_aji
            to_instance.cr.execute(query,(target_cc, ))

        self._logger.info("Compare from %s to %s (%d/%d) %s" % (from_instance.name, to_instance.name, len(list_aji), to_instance.cr.rowcount, target_str ))
        for aji in to_instance.cr.fetchall():
            xmlid = aji['xmlid']
            if sync_type == 'up' and xmlid not in tmp:
                self.create_aji_error(cr, uid, aji, from_instance.name, to_instance.name, 'not_sync', 'Object exists in %s not in %s' % (to_instance.name, from_instance.name))
                continue
            differ = []
            for key, value in aji.iteritems():
                if self.is_diff(tmp[xmlid][key],value):
                    differ.append('%s : (%s)%s != (%s)%s' % (key, from_instance.name, tmp[xmlid][key], to_instance.name, value))
            if differ:
                self.create_aji_error(cr, uid, aji, from_instance.name, to_instance.name, 'mismatch', "Values mismatch:\n %s" % "\n ".join(differ))
            del(tmp[xmlid])
        for xmlid in tmp:
            self.create_aji_error(cr, uid, tmp[xmlid], from_instance.name, to_instance.name, 'not_sync', 'Object exists in %s not in %s' % (from_instance.name, to_instance.name))

        return True

    def create_aji_error(self, cr, uid, aji, from_inst, to_inst, type, error):
        self.create(cr, uid, {
            'object': 'account.analytic.line',
            'from_instance': from_inst,
            'to_instance': to_inst,
            'xmlid': aji['xmlid'],
            'object_info': '%s (%s / %s / %s)' % (aji['entry_sequence'], aji['destination'], aji['cost_center'], aji['funding_pool']),
            'error': error,
            'type': type,
        })

    def start_compare_ji(self, cr, uid, instances, periods_name):
        query = """select
d.name as xmlid, move.name as move_name, account.code, l.accrual, l.blocked, l.cheque_number, l.corrected, l.credit, l.credit_currency, currency.name as cur, date_created, date_maturity, l.debit, l.debit_currency, l.document_date, l.have_an_historic, l.is_addendum_line, l.is_transfer_with_change, l.is_write_off, journal.code, l.name, l.partner_txt, period.name as period_name, reconcile.name as reconcile, partial_reconcile.name as partial_rec, l.ref, l.reversal, l.source_date, l.reference, l.state, l.transfer_amount
from account_move_line l
inner join account_move move on move.id = l.move_id
inner join account_journal journal on journal.id = l.journal_id
inner join res_currency currency on currency.id = l.currency_id
inner join account_account account on l.account_id = account.id
inner join ir_model_data d on d.model = 'account.move.line' and d.res_id = l.id
inner join account_period period on period.id = l.period_id
inner join msf_instance instance on l.instance_id = instance.id
left join account_move_reconcile reconcile on reconcile.id = l.reconcile_id
left join account_move_reconcile partial_reconcile on partial_reconcile.id = l.reconcile_partial_id
where
  instance.name = %s
  and period.name in ("""+','.join(["'%s'"%x for x in periods_name])+""")
"""
        for level_1 in [x for x in instances.values() if x != 'section']:
            level_1.cr.execute(query, (level_1.name, ))
            aml_proj = {}
            for a in level_1.cr.fetchall():
                aml_proj[a['xmlid']] = a

            for db in level_1.all_parents:
                tmp = aml_proj.copy()

                db.cr.execute(query, (level_1.name, ))
                for a in db.cr.fetchall():
                    xmlid = a['xmlid']
                    if xmlid not in aml_proj:
                        self.create_ji_error(cr, uid, a, level_1.name, db.name, 'not_sync', 'Object exists in %s not in %s' % (db.name, level_1.name))
                    else:
                        differ = []
                        for key, value in a.iteritems():
                            if self.is_diff(tmp[xmlid][key],value):
                                differ.append('%s : (%s)%s != (%s)%s' % (key, level_1.name, tmp[xmlid][key], db.name, value))
                        if differ:
                            self.create_ji_error(cr, uid, a, level_1.name, db.name, 'mismatch', "Values mismatch:\n %s" % "\n ".join(differ))
                        del(tmp[xmlid])

                for xmlid in tmp:
                    self.create_ji_error(cr, uid, tmp[xmlid], level_1.name, db.name, 'not_sync', 'Object exists in %s not in %s' % (level_1.name, db.name))


    def create_ji_error(self, cr, uid, ji, from_inst, to_inst, type, error):
        self.create(cr, uid, {
            'object': 'account.move.line',
            'from_instance': from_inst,
            'to_instance': to_inst,
            'xmlid': ji['xmlid'],
            'object_info': ji['move_name'],
            'error': error,
            'type': type
        })


    def display_start_wizard(self, cr, uid, ids, context=None):
        wiz_obj = self.pool.get('sync.compare.start_comparison')
        inst_obj = self.pool.get('msf.instance')
        inst_ids = inst_obj.search(cr, uid, [], context=context)
        data = []
        for inst in inst_obj.browse(cr, uid, inst_ids, context=context):
            data.append((0, 0, {'instance_id': inst.id, 'dbname': inst.dbname or inst.name}))
        wiz_id = wiz_obj.create(cr, uid, {'instance_ids': data}, context=context)
        return {
            'type': 'ir.actions.act_window',
            'name': 'Finance Instances comparison',
            'res_model': 'sync.compare.start_comparison',
            'res_id': wiz_id,
            'context': context,
            'target': 'new',
            'view_mode': 'form',
            'view_type': 'form',
        }

    def gl_balance(self, cr, uid, instances, periods_name):
        query_balance = """
select account.code as account_code, period.name as period, instance.name as instance, sum(credit) as credit, sum(debit) as debit
from
    account_move_line l, account_period period, msf_instance instance, account_account account
where
    l.instance_id = instance.id and
    period.id = l.period_id and
    l.account_id = account.id and
    period.name in %s and
    instance.name in %s
group by account.code, period.name, instance.name
order by instance.name, period.name, account.code::int
"""
        gl_obj = self.pool.get('account.gl_balance')
        gl_line_obj = self.pool.get('account.gl_balance.line')
        cache = {}
        for inst in instances.values():
            inst.cr.execute(query_balance, (tuple(periods_name), tuple(inst.children_name+[inst.name])))
            for l in inst.cr.fetchall():
                key = (l['account_code'], l['period'], l['instance'])
                if key not in cache:
                    cache[key] = gl_obj.create(cr, uid, {'account_code': l['account_code'], 'period': l['period'], 'instance': l['instance']})
                line = {
                    'debit': l['debit'],
                    'credit': l['credit'],
                    'on_instance': inst.name,
                    'gl_balance_id': cache[key],
                }
                gl_line_obj.create(cr, uid, line)

        account_ids = self.pool.get('account.account').search(cr, uid, [('type', '=', 'view')], order='level desc')
        for account in self.pool.get('account.account').browse(cr, uid, account_ids):
            child_ids = [x.code for x in account.child_parent_ids]
            sql = """select sum(l.debit), sum(l.credit), l.on_instance, b.period, b.instance from account_gl_balance_line l, account_gl_balance b 
where l.gl_balance_id = b.id and
b.account_code in %s 
group by l.on_instance, b.period, b.instance
"""
            cache = {}
            cr.execute(sql, (tuple(child_ids), ))
            for consolidate in cr.fetchall():
                key = (account.code, consolidate[3], consolidate[4])
                if key not in cache:
                    cache[key] = gl_obj.create(cr, uid, {'account_code': account.code, 'period': consolidate[3], 'instance': consolidate[4]})
                line = {
                    'debit': consolidate[0],
                    'credit': consolidate[1],
                    'on_instance': consolidate[2],
                    'gl_balance_id': cache[key],
                }
                gl_line_obj.create(cr, uid, line)
        cr.execute('update account_gl_balance gl set level=a.level, parent_left=a.parent_left from account_account a where a.code = gl.account_code')

sync_compare()

class account_gl_balance(osv.osv):
    _name = 'account.gl_balance'
    _rec_name = 'account_code'
    _columns = {
        'account_code': fields.char('Code', size=64),
        'period': fields.char('Period', size=64),
        'instance': fields.char('Instance', size=64),
        'line_ids': fields.one2many('account.gl_balance.line', 'gl_balance_id', 'Lines'),
        'level': fields.integer('Level'),
        'parent_left': fields.integer('Order')
    }

account_gl_balance()

class account_gl_balance_line(osv.osv):
    _name = 'account.gl_balance.line'
    _rec_name = 'on_instance'
    _columns = {
        'credit': fields.float('Credit'),
        'debit': fields.float('Debit'),
        'on_instance': fields.char('Balance on instance', size=64),
        'gl_balance_id': fields.many2one('account.gl_balance', 'Parent'),
    }
account_gl_balance_line()

