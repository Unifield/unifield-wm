from osv import osv
from osv import fields


class kpi_refresh(osv.osv_memory):
    _name = 'kpi.refresh'
    _description = 'Shared library for KPI database refresh'

    def truncate_tables(self, cr, uid):

        cr.execute('''drop table if exists kpi_purchase_order cascade;''')
        cr.execute('''drop table if exists kpi_purchase_order_line cascade;''')
        cr.execute('''drop table if exists kpi_res_partner cascade;''')
        cr.execute('''drop table if exists kpi_stock_move cascade;''')
        cr.execute('''drop table if exists kpi_stock_picking cascade;''')
        cr.execute('''drop table if exists kpi_product_product cascade;''')
        cr.execute('''drop table if exists kpi_product_template cascade;''')
        cr.execute('''drop table if exists kpi_product_nomenclature cascade;''')
        cr.execute('''drop table if exists po_flat cascade;''')
        cr.execute('''drop table if exists stock_move_flat cascade;''')
        cr.execute('''drop table if exists product_flat cascade;''')
        cr.execute('''drop table if exists dimension_8b cascade;''')
        cr.execute('''drop table if exists dimension_3_base cascade;''')
        cr.execute('''drop table if exists dimension_6a cascade;''')
        cr.execute('''drop view if exists dimension_8b_vw cascade;''')
        cr.execute('''drop view if exists dimension_3_base_vw cascade;''')
        cr.execute('''drop view if exists dimension_3a_vw cascade;''')
        cr.execute('''drop view if exists po_flat_vw cascade;''')
        cr.execute('''drop view if exists stock_move_flat_vw cascade;''')
        cr.execute('''drop view if exists product_flat_vw cascade;''')

        cr.execute('''truncate table supply_kpi_summary''')
        cr.execute('''truncate table dimension_3a''')
        cr.commit()

        print "Tables dropped and truncated"

        cr.execute('''create table kpi_purchase_order as select * from purchase_order limit 0;''')
        cr.execute('''create table kpi_purchase_order_line as select * from purchase_order_line limit 0;''')
        cr.execute('''create table kpi_res_partner as select * from res_partner limit 0;''')
        cr.execute('''create table kpi_stock_move as select * from stock_move limit 0;''')
        cr.execute('''create table kpi_stock_picking as select * from stock_picking limit 0;''')
        cr.execute('''create table kpi_product_product as select * from product_product limit 0;''')
        cr.execute('''create table kpi_product_template as select * from product_template limit 0;''')
        cr.execute('''create table kpi_product_nomenclature as select * from product_nomenclature limit 0;''')
        cr.commit()
        cr.execute('''create view po_flat_vw as
            select 	po.id as po_id,
                    po.date_order,
                    po.date_approve,
                    po.date_confirm,
                    po.arrival_date,
                    po.receipt_date,
                    po.delivery_requested_date,
                    po.name as po_name,
                    po.categ,
                    po.order_type,
                    po.priority,
                    po.shipment_date,
                    po.amount_total,
                    po.partner_type,
                    po.partner_id,
                    po.state,
                    date_part('week',po.create_date) as po_created_week,
                    date_part('month',po.create_date) as po_created_month,
                    date_part('year',po.create_date) as po_created_year,
                    pol.id as pol_id,
                    pol.product_id,
                    pol.is_line_split,
                    pol.from_fo,
                    pol.name as pol_name,
                    pol.original_purchase_line_id
            from kpi_purchase_order po,
                 kpi_purchase_order_line pol
            where pol.order_id = po.id
            and po.state in ('done','closed');''')

        cr.execute('''create view stock_move_flat_vw as
              select sp.id as sp_id,
                 sm.id as sm_id,
               srt.name as "reason_type",
                 sp.purchase_id,
                 sp.create_date as "sp_create_date",
                 sp.delivered,
                 sp.min_date as "sp_expect_date",
                 sp.partner_id,
                 sm.line_number,
                 sm.product_id,
                 sm.date_expected,
                 sm.name,
                 sm.product_qty,
                 sm.state,
                 sm.expired_date,
                 sm.date as "sm_actual_receipt_date"
            from kpi_stock_picking sp,
                 kpi_stock_move sm,
                 stock_reason_type srt
            where sm.picking_id = sp.id
            and sm.reason_type_id = srt.id
            and sm.state in ('done','confirmed');''')

        cr.execute('''create view product_flat_vw as
            select pp.id,
                 pp.default_code,
                 pp.name_template,
                 pp.product_tmpl_id,
                 pt.standard_price as "cost_price",
                 pp.currency_id,
                 rc.name as "currency_code",
                 pn0.name as "pn_main_type",
                 pn1.name as "pn_group",
                 pn2.name as "pn_family",
                 pn3.name as "pn_root",
                 pt.nomen_manda_0,
                 pt.nomen_manda_1,
                 pt.nomen_manda_2,
                 pt.nomen_manda_3
            from kpi_product_product pp,
                 kpi_product_template pt,
                 kpi_product_nomenclature pn0,
                 kpi_product_nomenclature pn1,
                 kpi_product_nomenclature pn2,
                 kpi_product_nomenclature pn3,
                 res_currency rc
            where pp.product_tmpl_id = pt.id
              and pn0.id = pt.nomen_manda_0
              and pn1.id = pt.nomen_manda_1
              and pn2.id = pt.nomen_manda_2
              and pn3.id = pt.nomen_manda_3
              and rc.id = pp.currency_id;''')
        cr.commit()
        cr.execute('''create table po_flat as select * from po_flat_vw limit 0;''')
        cr.execute('''create table stock_move_flat as select * from stock_move_flat_vw limit 0;''')
        cr.execute('''create table product_flat as select * from product_flat_vw limit 0;''')
        cr.commit()
        cr.execute('''create view dimension_3_base_vw as
            select pf.po_id,
                   pf.pol_id,
                   sp.sp_id,
                   sp.sm_id,
                   pf.delivery_requested_date::date,    -- remove any timestamps
                   sp.sp_expect_date::date,
                   sp.sm_actual_receipt_date::date,
                   pf.categ,
                   pf.order_type,
                   pf.priority,
                   pf.partner_type,
                   rp.name,
                   rp.zone,
                   pf.state,
                   prd.default_code,
                   prd.pn_main_type,
                   prd.pn_group,
                   prd.pn_family,
                   prd.pn_root,
                   count(*) as cnt
            from po_flat pf
            left join stock_move_flat sp on sp.purchase_id = pf.po_id
            left join kpi_res_partner rp on rp.id = pf.partner_id
            left join product_flat prd on pf.product_id = prd.id
            group by pf.po_id, pf.pol_id, sp.sp_id, sp.sm_id,
                     pf.delivery_requested_date, sp.sp_expect_date, sp.sm_actual_receipt_date, pf.categ, pf.order_type,
                     pf.priority, pf.partner_type,rp.name, rp.zone, pf.state, prd.default_code, prd.pn_main_type,
                     prd.pn_group, prd.pn_family, prd.pn_root
             order by rp.name, pf.partner_type, rp.zone;''')
        cr.commit()
        cr.execute('''create table dimension_3_base as select * from dimension_3_base_vw limit 0;''')
        cr.commit()
        cr.execute('''create view dimension_3a_vw as
            select ontime.cnt as "ontime",
                   (select sum(cnt) from dimension_3_base) as "totlines",
                   (ontime.cnt/(select sum(cnt) from dimension_3_base)* 100) as pct_ontime,
                   ontime.*
            from dimension_3_base ontime
            where ontime.sm_actual_receipt_date is not null
            and ontime.sm_actual_receipt_date <= ontime.delivery_requested_date;''')
        cr.commit()
        #cr.execute('''create table dimension_3a as select * from dimension_3a_vw limit 0;''')
        #cr.commit()
        #cr.execute('''ALTER TABLE dimension_3a ADD dim_3a_id SERIAL;''')
        #cr.commit()
        #cr.execute('''ALTER TABLE dimension_3a ADD CONSTRAINT dim_3a_id_key PRIMARY KEY (dim_3a_id);''')
        #cr.execute('''CREATE INDEX dimension_3a_index ON dimension_3a (sm_id, name, priority);''')
        #cr.commit()
        cr.execute('''create view dimension_6a_vw as
              select  sm.sm_id as sm_id,
                      prd.id as prd_id,
                      sm.reason_type,
                      sm.product_qty,
                      prd.cost_price,
                      (sm.product_qty * prd.cost_price) as "value",
                      prd.currency_code,
                      prd.name_template,
                      prd.default_code,
                      prd.pn_main_type,
                      prd.pn_group,
                      prd.pn_family,
                      prd.pn_root,
                      date_part('month',sm.sp_create_date) as sm_created_month,
                      date_part('year',sm.sp_create_date) as sm_created_year
              from stock_move_flat sm,
                   product_flat prd
              where sm.product_id = prd.id
              and sm.reason_type in ('Loss','Scrap','Sample','Expiry','Damage');''')
        cr.commit()
        cr.execute('''create table dimension_6a as select * from dimension_6a_vw limit 0;''')
        cr.commit()
        cr.execute('''create view dimension_8b_vw as
            select pf.categ,
                   pf.order_type,
                   pf.priority,
                   pf.partner_type,
                     pf.partner_id,
                     rp.name,
                     pf.state,
                     pf.po_created_week,
                     pf.po_created_month,
                     pf.po_created_year,
                     count(*) as cnt
                from po_flat pf
                left join kpi_res_partner rp on rp.id = pf.partner_id
                where pf.state in ('confirmed','done') -- also need 'in exception'
                group by pf.categ, pf.state, pf.order_type, pf.priority,
                         pf.partner_type, pf.partner_id, rp.name, pf.state, pf.po_created_week,
                         pf.po_created_month, pf.po_created_year;''')
        cr.commit()
        cr.execute('''create table dimension_8b as select * from dimension_8b_vw;''')
        cr.commit()
        print "tables recreated"
        return True

    def refresh_data(self, cr, uid):

        print "KPI Group 1"

        cr.execute('''insert into kpi_purchase_order select * from purchase_order''')
        cr.execute('''insert into kpi_purchase_order_line select * from purchase_order_line''')
        cr.execute('''insert into kpi_res_partner select * from res_partner''')
        cr.execute('''insert into kpi_stock_move select * from stock_move''')
        cr.execute('''insert into kpi_stock_picking select * from stock_picking''')
        cr.execute('''insert into kpi_product_product select * from product_product''')
        cr.execute('''insert into kpi_product_template select * from product_template''')
        cr.execute('''insert into kpi_product_nomenclature select * from product_nomenclature''')
        cr.commit()
        print "KPI Group 2"
        cr.execute('''insert into po_flat select * from po_flat_vw''')
        cr.commit()
        cr.execute('''insert into stock_move_flat select * from stock_move_flat_vw''')
        cr.commit()
        cr.execute('''insert into product_flat select * from product_flat_vw''')
        cr.commit()

        print "KPI Group 3"
        # dimension_3a. columns need to be named because openerp creates tables with random column order
        cr.execute('''insert into dimension_3_base select * from dimension_3_base_vw''')
        cr.commit()
        cr.execute('''  insert into dimension_3a(
                            /*create_uid, create_date, write_date,*/
                            /*write_uid, */pct_ontime, po_id,
                            pol_id, sp_id, sm_id,
                            delivery_requested_date, sp_expect_date, sm_actual_receipt_date,
                            categ, order_type, priority,
                            partner_type, name, zone,
                            state, default_code, pn_main_type,
                            pn_group, pn_family, pn_root,
                            cnt
                        )
                        select
                            /*1 as create_uid, current_date as create_date, current_date as write_date,*/
                            /*1 as write_uid, */pct_ontime, po_id,
                            pol_id, sp_id, sm_id,
                            delivery_requested_date, sp_expect_date, sm_actual_receipt_date,
                            categ, order_type, priority,
                            partner_type, name, zone,
                            state, default_code, pn_main_type,
                            pn_group, pn_family, pn_root,
                            cnt
                        from dimension_3a_vw''')
        cr.commit()
        print "KPI Group 4"
        cr.execute('''insert into dimension_8b select * from dimension_8b_vw''')
        cr.commit()
        cr.execute('''insert into dimension_6a select * from dimension_6a_vw''')
        cr.commit()

        print "KPI Group 5"
        cr.execute('''insert into supply_kpi_summary(create_uid,create_date,write_date,write_uid)
                      select distinct 1 as create_uid,current_date as create_date,current_date as write_date,1 as write_uid''')
        cr.commit()

        cr.execute('''update supply_kpi_summary set dim_3a = (select sum(pct_ontime) from dimension_3a),
                                                    dim_6a = (select sum(value) from dimension_6a),
                                                    dim_6a_currency = (select distinct currency_code from dimension_6a),
                                                    dim_8b = (select sum(cnt) from dimension_8b)''')
        cr.commit()

        return True

kpi_refresh()