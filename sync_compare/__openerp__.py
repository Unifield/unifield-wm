# -*- coding: utf-8 -*-

{
    'name': 'Synchronization Utility',
    'version': '0.1',
    'category': 'Tools',
    'description': """\
Synchronization Engine: compare finance data
""",
    'author': 'TeMPO Consulting, MSF',
    'website': '',
    'depends': ['sync_client', 'msf_instance'],
    'init_xml': [],
    'data': [
      'sync_compare_view.xml',
      'wizard/start_comparison_view.xml',
      'sync_compare_wizard.xml',
      'sync_compare_report.xml',
    ],
    'demo_xml': [
    ],
    'test':[
    ],
    'installable': True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
