#!/usr/bin/env python
# -*- coding: utf-8 -*-

from report import report_sxw
import csv
import pooler
import tempfile


class export_gl_coa(report_sxw.report_sxw):
    def create(self, cr, uid, ids, data, context=None):
        pool = pooler.get_pool(cr.dbname)
        period_obj = pool.get('account.period')
        instance_obj = pool.get('msf.instance')
        gl_balance_obj = pool.get('account.gl_balance')

        instance_ids = instance_obj.search(cr, uid, [('dbname', '!=', False), ('level', '!=', 'section')])
        instances = instance_obj.browse(cr, uid, instance_ids)
        instances_name = []
        parent_instances = {}
        for inst in instances:
            instances_name.append(inst.name)
            parent_instances[inst.name] = []
            parent = inst.parent_id
            while parent:
                parent_instances[inst.name].append(parent.name)
                parent = parent.parent_id

        outfile = tempfile.TemporaryFile('w+')
        writer = csv.writer(outfile, quotechar='"', delimiter=',')

        period_ids = period_obj.search(cr, uid, [('comparison_done', '=', True)])
        for period in period_obj.browse(cr, uid, period_ids):
            writer.writerow([period.name])
            for inst_name in instances_name:
                to_write = ['', '%s balance'%inst_name, 'G/L Account', '%s debit'%inst_name, '%s credit'%inst_name]
                for p in parent_instances[inst_name]:
                    to_write += ['%s debit'%p, '%s credit'%p]
                writer.writerow(to_write)
                gl_b_ids = gl_balance_obj.search(cr, uid, [('instance', '=', inst_name), ('period', '=', period.name)], order='parent_left')

                for gl_b in gl_balance_obj.browse(cr, uid, gl_b_ids):
                    diff = False
                    to_write = ['', '', gl_b.account_code]
                    write_by_instance = {}
                    for line in gl_b.line_ids:
                        write_by_instance[line.on_instance] = [line.debit, line.credit]

                    to_write += write_by_instance[inst_name]
                    for p in parent_instances[inst_name]:
                        if p not in write_by_instance:
                            write_by_instance[p] = [0, 0]
                        if write_by_instance[p] != to_write[-2:]:
                            diff = True
                        to_write += write_by_instance[p]

                        if diff:
                            to_write.append('*')

                    writer.writerow(to_write)

        outfile.seek(0)
        out = outfile.read()
        outfile.close()
        return (out, 'csv')

export_gl_coa('report.export_gl_coa', 'sync.compare')
