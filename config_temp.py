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

hq_count = 2
coordo_count = 2
project_count = 2

load_test = 1250
dump_dir = '/tmp/db_dump_%s' % (prefix,)

source_path = ''
addons = ['unifield-wm', 'unifield-addons', 'unifield-server', 'unifield-web', 'sync_module_prod']
server_restart_cmd = ''
web_restart_cmd = ''
