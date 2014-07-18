from osv import osv
from osv import fields

class kpi_refresh(osv.osv_memory):
    _name = 'kpi.refresh'
    _description = 'Shared library for KPI database refresh'
     
    def truncate_tables(self,cr,uid):
        print 'truncate tables'
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
        print 'tables truncated'
        return True
    
    
    def refresh_data(self,cr,uid):
        print 'refreshing data'
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
        cr.execute('''insert into dimension_3_base select * from dimension_3_base_vw''')
        cr.execute('''insert into dimension_3a select * from dimension_3a_vw''')
        cr.execute('''insert into dimension_8b select * from dimension_8b_vw''')
        print 'data refreshed'
        return True
        
kpi_refresh()