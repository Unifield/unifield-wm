from osv import osv
from osv import fields

class kpi_refresh(osv.osv_memory):
    _name = 'kpi.refresh'
    _description = 'Shared library for KPI database refresh'

    def truncate_tables(self, cr, uid):
        cr.execute('''truncate table kpi_purchase_order''')
        cr.execute('''truncate table kpi_purchase_order_line''')
        cr.execute('''truncate table kpi_res_partner''')
        cr.execute('''truncate table kpi_stock_move''')
        cr.execute('''truncate table kpi_stock_picking''')
        cr.execute('''truncate table kpi_product_product''')
        cr.execute('''truncate table kpi_product_template''')
        cr.execute('''truncate table kpi_product_nomenclature''')

        cr.execute('''truncate table po_flat''')
        cr.execute('''truncate table stock_move_flat''')
        cr.execute('''truncate table product_flat''')

        cr.execute('''truncate table dimension_8b''')
        cr.execute('''truncate table dimension_3_base''')
        cr.execute('''truncate table dimension_3a''')
        cr.execute('''truncate table dimension_6a''')


        cr.execute('''truncate table supply_kpi_summary''')
        return True

    def refresh_data(self, cr, uid):

        cr.execute('''insert into kpi_purchase_order select * from purchase_order''')
        cr.execute('''insert into kpi_purchase_order_line select * from purchase_order_line''')
        cr.execute('''insert into kpi_res_partner select * from res_partner''')
        cr.execute('''insert into kpi_stock_move select * from stock_move''')
        cr.execute('''insert into kpi_stock_picking select * from stock_picking''')
        cr.execute('''insert into kpi_product_product select * from product_product''')
        cr.execute('''insert into kpi_product_template select * from product_template''')
        cr.execute('''insert into kpi_product_nomenclature select * from product_nomenclature''')

        cr.execute('''insert into po_flat select * from po_flat_vw''')
        cr.execute('''insert into stock_move_flat select * from stock_move_flat_vw''')
        cr.execute('''insert into product_flat select * from product_flat_vw''')

        # dimension_3a. columns need to be named because openerp creates tables with random column order
        cr.execute('''insert into dimension_3_base select * from dimension_3_base_vw''')
        cr.execute('''  insert into dimension_3a(
                            create_uid, create_date, write_date,
                            write_uid, pct_ontime, po_id,
                            pol_id, sp_id, sm_id,
                            delivery_requested_date, sp_expect_date, sm_actual_receipt_date,
                            categ, order_type, priority,
                            partner_type, name, zone,
                            state, default_code, pn_main_type,
                            pn_group, pn_family, pn_root,
                            cnt
                        )
                        select
                            1 as create_uid, current_date as create_date, current_date as write_date,
                            1 as write_uid, pct_ontime, po_id,
                            pol_id, sp_id, sm_id,
                            delivery_requested_date, sp_expect_date, sm_actual_receipt_date,
                            categ, order_type, priority,
                            partner_type, name, zone,
                            state, default_code, pn_main_type,
                            pn_group, pn_family, pn_root,
                            cnt
                        from dimension_3a_vw''')

        cr.execute('''insert into dimension_8b select * from dimension_8b_vw''')
        cr.execute('''insert into dimension_6a select * from dimension_6a_vw''')


        cr.execute('''insert into supply_kpi_summary(create_uid,create_date,write_date,write_uid)
                      select distinct 1 as create_uid,current_date as create_date,current_date as write_date,1 as write_uid''')
        cr.execute('''update supply_kpi_summary set dim_3a = (select sum(pct_ontime) from dimension_3a),
                                                    dim_6a = (select sum(value) from dimension_6a),
                                                    dim_6a_currency = (select distinct currency_code from dimension_6a),
                                                    dim_8b = (select sum(cnt) from dimension_8b)''')

        return True

kpi_refresh()