#!/usr/bin/env python
# -*- coding: utf8 -*-
from unifield_test import UnifieldTest

class LoadMasterTest(UnifieldTest):

    def test_010_load(self):
        master = [
            '010_accounts.yml',
            '020_partners.yml',
            '030_journals.yml',
            '040_analytic.yml',
            '045_distibution.yml',
            '050_product_nomenclatures.yml',
            '060_product_categories.yml',
            '070_products.yml',
            '080_locations.yml',
        ]
        for d in master:
            self.hq1.get('load_yml_file').load(d)
        self.synchronize(self.hq1)
        self.synchronize(self.c1)
        self.synchronize(self.p1)
        for inst in (self.c1, self.p1): 
            inst.get('load_yml_file').load('045_distibution.yml')
            partners_ids = inst.get('res.partner').search([('active', '=', False)])
            if partners_ids:
                inst.get('res.partner').write(partners_ids, {'active': True})
            inst.get('load_yml_file').load('070_products.yml')
            inst.get('load_yml_file').load('080_locations.yml')

def get_test_class():
    '''Return the class to use for tests'''
    return LoadMasterTest

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
