# -*- coding: utf-8 -*-

## Postgres admin password
db_password = 'admin'
## admin password
admin_password = 'admin'
## User login & password
user_login = 'unifield'
user_password = 'unifield'

## Infos to connect to server (sync client side)
client_host = 'localhost' #'10.42.43.1'
client_port = 8069

## Infos to connect to server (sync server side)
server_host = 'localhost' #'10.42.43.1'
server_port = 8069
netrpc_port = 8070

## Database format
prefix = "SPRINT5"

## Other stuffs
default_email = 'null@msf.org'
company_name = 'Médecins Sans Frontières'
currency = 'chf' # either 'chf' or 'eur' (field.selection in the setup currency wizard)
lang = False # fr_MF or es_MF
sync_user_admin = False
hq_count = 1
coordo_count = 1
project_count = 1
# or describe the instances with instance_tree
"""
instance_tree = {
    'HQ1': {
        'C1': ['P1', 'P2'],
        'C2': ['P1'],
    },
    'HQ2': {
        'C1': [],
    },
}
"""
load_test = 1250
dump_dir = '/tmp/db_dump_%s' % (prefix,)

source_path = ''
addons = ['unifield-wm', 'unifield-addons', 'unifield-server', 'unifield-web', 'sync_module_prod']
server_restart_cmd = ''
web_restart_cmd = ''

# uncomment the next 3 parameters to load UserRights
#load_uac_file = 'data/uac.xml'
#load_users_file = 'data/unifield_users.csv'
#load_extra_files = [
#    'data/extra/ir.actions.act_window.csv',
#    'data/extra/ir.model.access.csv',
#    'data/extra/ir.rule.csv',
#    'data/extra/msf_field_access_rights.field_access_rule.csv',
#    'data/extra/msf_field_access_rights.field_access_rule_line.csv',
#    'data/extra/msf_button_access_rights.button_access_rule.csv',
#]

# if empty or not defined module msf_sync_data_hq is installed
#load_hq_data = [
#    'data/master_hq/account.analytic.account.csv',
#    'data/master_hq/account.account.csv',
#    'data/master_hq/2/account.analytic.account.csv',
#    'data/master_hq/product.nomenclature.csv',
#    'data/master_hq/product.category.csv',
#    'data/master_hq/product.product.csv',
#]

# if empty or not defined module msf_sync_data_post_synchro is installed
#load_data = [
#    'data/master/account.analytic.journal.csv',
#    'data/master/account.journal.csv',
#]
