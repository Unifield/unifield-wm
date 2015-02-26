#-*- encoding:utf-8 -*-

from osv import osv
from osv import fields

class sync_compare_msf_instance(osv.osv_memory):
    _name = 'sync.compare.msf.instance'
    _columns = {
        'instance_id': fields.many2one('msf.instance', 'Instance', required=1, readonly=1),
        'dbname': fields.char('DB Name', size=64),
        'comparison_id': fields.many2one('sync.compare.start_comparison', required=1)
    }
sync_compare_msf_instance()

class sync_compare_start_comparison(osv.osv_memory):
    _name = 'sync.compare.start_comparison'
    _description = 'Finance Instances comparison'
    _columns = {
        'instance_ids': fields.one2many('sync.compare.msf.instance', 'comparison_id', 'Instances'),
        'prefix': fields.char('DB prefix', size=126),
        'delete': fields.boolean('Delete previous comparison'),
    }

    def start(self, cr, uid, ids, context=None):
        wiz = self.browse(cr, uid, ids[0])
        inst_obj = self.pool.get('msf.instance')
        prefix = wiz.prefix or ''
        if wiz.delete:
            for obj in ('account.gl_balance.line', 'account.gl_balance', 'sync.compare'):
                ids_to_del = self.pool.get(obj).search(cr, uid, [], context=context)
                if ids_to_del:
                    self.pool.get(obj).unlink(cr, uid, ids_to_del, context=context)
            period_obj = self.pool.get('account.period')
            p_ids = period_obj.search(cr, uid, [('comparison_done', '=', 't')], context=context)
            if p_ids:
                period_obj.write(cr, uid, p_ids, {'comparison_done': False}, context=context)
            cr.commit()
        for inst in wiz.instance_ids:
            inst_obj.write(cr, uid, inst.instance_id.id, {'dbname': '%s%s' % (prefix, inst.dbname)})
        missions = self.pool.get('sync.compare').get_all_mission_closed_period(cr, uid)
        if not missions:
            raise osv.except_osv('Error', "No period closed on all instances or closed period already checked.")
        self.pool.get('sync.compare').compare(cr, uid, missions)
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'res.request',
            'view_mode': 'tree,form',
            'view_type': 'form',
        }
        #return {'type': 'ir.actions.act_window_close'}

sync_compare_start_comparison()
