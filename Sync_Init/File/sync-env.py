# -*- coding: utf-8 -*-

## Postgres admin password
db_password = '@@ADMINDBPASS@@'
## admin password
admin_password = 'admin'
## User login & password
user_login = 'unifield'
user_password = 'unifield'

## Infos to connect to server (sync client side)
client_host = 'localhost' #'10.42.43.1'
client_port = @@XMLRPCPORT@@

## Infos to connect to server (sync server side)
server_host = 'localhost' #'10.42.43.1'
server_port = @@XMLRPCPORT@@
netrpc_port = @@NETRPCPORT@@

## Database format
prefix = "@@DBNAME@@"

## Other stuffs
default_email = 'null@msf.org'
company_name = 'Médecins Sans Frontières'
currency = 'base.EUR'

# WARNING:
# hq_count = h, coordo_count = c, project_count = p 
# will create
# h hq instance, 
# (c*h) coordo, 
# and (p*c*h) projects !
hq_count = 1
coordo_count = 1
project_count = 1

load_test = 1250
source_path = '/home/@@USERERP@@'
addons = ['unifield-wm', 'unifield-addons', 'unifield-server', 'unifield-web', 'sync_module_prod']
server_restart_cmd = '/etc/init.d/@@USERERP@@-server restart'
web_restart_cmd = '/etc/init.d/@@USERERP@@-web restart'
dump_dir = '/home/@@USERERP@@/exports'

