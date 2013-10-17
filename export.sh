#!/usr/bin/env bash
#
# export.sh
#
# Create a synchronization environment and create an archive from it

PROGRAM=`basename $0`
VERSION="0.0.0"
current_dir="$PWD"

#####
## Variables
###

# configuration files
configfile="exportrc"
mkdb_configfile="config.py"
mkdb_tmp_configfile="config_temp.py"

# official launchpad branches
branch_server="lp:unifield-server"
branch_addons="lp:unifield-addons"
branch_web="lp:unifield-web"
branch_wm="lp:unifield-wm"
branch_sync="lp:unifield-wm/sync_module_prod"

# temporary directory in which we will work
tmpdir="${HOME}/tmp"

# default HQ/PROJECT/COORDO counts
hq_count=1
coordo_count=2
project_count=3

# some dates
today=`date +'%Y-%m-%d'`
fdoy="`date +'%Y'`-01-01" # first day of year

#####
## FUNCTIONS
###

error_and_exit() {
  echo -e $1
  exit 1
}

check_cmd_presence() {
  cmd_path=`which $1`
  if [ -z $cmd_path ]; then
    error_and_exit "$1 is missing.\nInstall it: sudo apt-get update && sudo apt-get install $2"
  fi
  echo "$1: installed."
}

stop_server() {
  start-stop-daemon --stop --quiet --pidfile $1 --oknodo
}

stop_server_and_exit() {
  stop_server "$1" && exit 1
}

pre_process_db() {
  ## Open all periods
  echo "$1: preprocessing..."
  echo -e -n "\tOpen all periods as today($today): "
  psql "$1" -t -c "UPDATE account_period SET state = 'draft' WHERE id IN (SELECT id FROM account_period WHERE date_start <= '$today' ORDER BY number);"
  ## Update all general accounts
  echo -e -n "\tSet all general accounts to $fdoy: "
  psql "$1" -t -c "UPDATE account_account SET activation_date = '$fdoy';"
  ## Update all analytic accounts
  echo -e -n "\tSet all analytic accounts to $fdoy: "
  psql "$1" -t -c "UPDATE account_analytic_account SET date_start = '$fdoy';"
  echo "$1: preprocessing done."
}

#####
## TESTS
###

# Configuration file exists and is readable
if ! [ -r $configfile ] ; then
  error_and_exit "${configfile}: missing"
fi
# Load configuration file
source $configfile
echo "${configfile}: imported"

# Check configuration file for MKDB script
if ! [ -a $mkdb_configfile ] ; then
  if ! [ -a $mkdb_tmp_configfile ] ; then
    error_and_exit "${mkdb_tmp_configfile}: missing"
  fi
  # create mkdb configuration file
  cp ${mkdb_tmp_configfile} ${mkdb_configfile}
fi

# Check some programs presence
# pip
# bzr
# start-stop-daemon
# tar
# xz
# perl
# psql
# netstat
for cmd in "pip@pip" "bzr@bzr" "start-stop-daemon@dpkg" "tar@tar" "xz@xz-utils" "perl@perl-base" "psql@postgresql-client-common" "netstat@net-tools"; do
  cmdname=`echo $cmd|cut -d '@' -f 1`
  pkgname=`echo $cmd|cut -d '@' -f 2`
  check_cmd_presence $cmdname $pkgname
done

# openerp-client-lib 1.0.1 presence
openerp_clientlib=`pip search openerp-client-lib|grep INSTALLED|cut -d ':' -f 2|tr -d ' '`
if ! [ "${openerp_clientlib}" == "1.0.1" ] ; then
  error_and_exit "openerp-client-lib 1.0.1 missing.\nInstall it: sudo pip install openerp-client-lib==1.0.1"
fi
echo "openerp-client-lib 1.0.1: installed."

# tmp directory presence. If not create it.
if [ -a "$tmpdir" ] ; then
  if ! [ -d "$tmpdir" ] ; then
    error_and_exit "$tmpdir exists but is not a directory. Change tmpdir variable."
  fi
else
  mkdir "$tmpdir" || exit 1
fi
echo "Temp. dir: $tmpdir"

#####
## MAIN
###

## Fetch all branches (either from local or from remote)
for branch in "web@${branch_web}@${web}" "server@${branch_server}@${server}" "addons@${branch_addons}@${addons}" "wm@${branch_wm}@${wm}" "sync@${branch_sync}@${sync}"; do
  # prepare the transaction
  copy=`echo $branch|cut -d '@' -f 1`
  remote=`echo $branch|cut -d '@' -f 2`
  inlocal=`echo $branch|cut -d '@' -f 3`
  origin="$inlocal"
  if ! [ -d "$inlocal" ]; then
    origin="$remote"
  fi
  # Check if destination directory exists
  # if not: fetch branch content either from local or from remote (regarding local existence)
  if ! [ -d "${tmpdir}/${copy}" ]; then
    echo -n "Fetching '$copy' from '$origin': "
    bzr checkout -q --lightweight "$origin" "${tmpdir}/${copy}"
    echo "DONE."
  # if exists: update branch
  else
    cd ${tmpdir}/${copy}
    echo -n "Updating '$copy': "
    bzr pull -q
    cd $current_dir
    echo "DONE."
  fi
done

## Check which port to use
read XMLRPCPORT NETRPCPORT WEBPORT <<<`netstat -anltp 2> /dev/null | perl -e '%port = ();
($min, $max) = (8100, 8200);
while(<>) {
  $port{$&} = 1 if m/:\K\d+\b/ and $& >= $min and $& <= $max;
}
for my $i ($min..$max) {
  if( not exists $port{$i} and
    not exists $port{$i+1} and
    not exists $port{$i+2}) {
    print join(" ", $i, $i+1, $i+2);
    last;
  }
}'`
echo "xmlrpc port: ${XMLRPCPORT}"
echo "netrpc port: ${NETRPCPORT}"
echo "web port: ${WEBPORT}"

## Check that db is available
db_exists=`psql -l|grep "${dbname}_*"|wc -l`
while [ $db_exists -ne 0 ] ; do
  dbname="${dbname}_1"
  db_exists=`psql -l|grep "${dbname}_*"|wc -l`
done
echo "database: ${dbname}"

## Change MKDB configuration file 'prefix' variable
sed -i "s#\(prefix =\).*#\1 '${dbname}'#g" ${mkdb_configfile}
## Same thing with different ports for server and web
sed -i "s#\(client_port =\).*#\1 ${XMLRPCPORT}#g" ${mkdb_configfile}
sed -i "s#\(server_port =\).*#\1 ${XMLRPCPORT}#g" ${mkdb_configfile}
sed -i "s#\(netrpc_port =\).*#\1 ${NETRPCPORT}#g" ${mkdb_configfile}
## Set HQ to 1, COORDO to 2 and PROJECT to 3
sed -i "s#\(hq_count =\).*#\1 ${hq_count}#g" ${mkdb_configfile}
sed -i "s#\(coordo_count =\).*#\1 ${coordo_count}#g" ${mkdb_configfile}
sed -i "s#\(project_count =\).*#\1 ${project_count}#g" ${mkdb_configfile}

## Launch server
pidfile="${tmpdir}/${dbname}.pid"
echo -n "Launching openerp-server: "
start-stop-daemon --start --quiet --pidfile ${pidfile} \
  --background --make-pidfile --exec ${tmpdir}/server/bin/openerp-server.py -- \
  --no-xmlrpcs --netrpc-port=${NETRPCPORT} --xmlrpc-port=${XMLRPCPORT} \
  --addons-path=${tmpdir}/addons,${tmpdir}/wm,${tmpdir}/sync
# Wait 15 second before launching MKDB script
sleep 15s
echo "DONE."

## Launch MKDB script
cd ${current_dir} && ./mkdb.py || stop_server_and_exit ${pidfile}

## Stop server
stop_server ${pidfile}

## Save databases
# create a list file containing all files to save
list="${tmpdir}/${dbname}.list"
if ! [ -a "$list" ] ; then
  touch $list
else
  echo "" > $list
fi
# update each DB, save it in a dump file, add it to a list to save and drop DB
for db in `psql template1 -t -c "SELECT datname from pg_database where datname ilike '${dbname}_%';"`; do
  pre_process_db "$db"
  # save DB
  dumpfile="${db}.dump"
  if [ -a "$dumpfile" ] ; then
    error_and_exit "$dumpfile already exists! Aborted."
  fi
  echo -e -n "Saving '$db' to $dumpfile: "
  pg_dump -Fc $db > $dumpfile
  echo "$dumpfile" >> ${list}
  dropdb $db
  echo "DONE."
done

## Add some file into list file to archive
echo "manage_syncdb.sh" >> ${list}
echo "manage_syncdbrc" >> ${list}

## Create archive
echo -n "Creating archive: "
archive="`date +'%Y%m%d'`_${dbname}.tar.xz"
tar cfJ $archive `cat $list|tr -s '\n' ' '` || error_and_exit "An error occured to create archive: $archive."
echo "$archive DONE."

## Delete all DB dumps
rm -f *.dump

########################
## WORK IN PROGRESS
#####

## TODO: Update CSV files in sync_module_prod for data to be correct

##############

exit 0
