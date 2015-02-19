#-*- encoding:utf-8 -*-

from osv import osv

class sync_compare_open_update_received(osv.osv_memory):
    _name = "sync.compare.open_update_received"

    def open(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        obj = self.pool.get('sync.compare')
        xmlid = []
        for comp in obj.read(cr, uid, context.get('active_ids'), ['xmlid']):
            xmlid.append(comp['xmlid'])
        print str(xmlid)
        return {
            'type': 'ir.actions.act_url',
            'target': 'new',
            'url': "http://127.1.1.1:7080/openerp/tree/open?id=1&domain=[]&model=sync.client.update_received"
        }
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'sync.client.update_received',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'domain': [('sdref', 'in', xmlid)],
        }

sync_compare_open_update_received()
