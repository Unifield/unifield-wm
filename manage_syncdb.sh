#!/usr/bin/env bash
#
# manage_syncdb.sh
#
# Synchronization databases management
#

#####
## VARIABLES
###

PROGRAM=`basename $0`
VERSION="0.0.0"
configdir=`dirname $0`
config="${configdir}/`basename ${PROGRAM} .sh`rc"
current="$PWD"

#####
## FUNCTIONS
###

# display this program's usage
usage() {
  cat << EOF
usage: $PROGRAM [dbname] [command] [branch]

This script helps to manage synchro databases.

COMMANDS:
backup      backup all databases prefixed by <dbname>_
restore     restore all databases prefixed by <dbname>_ with a '.dump' suffix
drop        drop all databases prefixed by <dbname>_
start       launch a openerp server (need a config file '${config}')
stop        stop a openerp server
<dbname>    prefix of database to use
extract     do a drop, restore and start for the given dbname (after an \
archive extraction, for an example)
<branch>    path to the WM branch to use (only useful for start command)
EOF
}

# display an error
error() {
  echo -e "$1"
}

# display an error and quit
error_and_exit() {
  error "$1"
  exit 1
}

# check if configuration file exists
check_config() {
  if ! [ -f "${config}" ] ; then
    error_and_exit "Configuration file not found: $config."
  fi
}

# check if some db with this prefix exists
check_db() {
db_exists=`psql -l|grep "$1_*"|wc -l`
if [ $db_exists -eq 0 ] ; then
  error_and_exit "No database with '$1' prefix found!"
fi
}

# backup all DB that have a prefix "${dbname}_"
backup() {
  check_db "$1"
  for db in `psql template1 -t -c "SELECT datname from pg_database where datname ilike '${1}_%';"`; do
    dumpfile="${db}.dump"
    if [ -a "$dumpfile" ] ; then
      error_and_exit "$dumpfile already exists! Aborted."
    fi
    echo -e -n "Saving '$db' to $dumpfile: "
    pg_dump -Fc $db > $dumpfile
    echo "DONE."
  done
}

# restore all .dump file that have a prefix with "${dbname}_"
restore() {
  for file in `ls ${1}_*`; do
    # do not make process on directories
    if [ -f $file ] ; then
      db=`basename $file .dump`
      exists=`psql template1 -t -c "SELECT COUNT(datname) from pg_database WHERE datname = '$db'"`
      if [ $exists == 1 ] ; then
        echo -n "$db exists. Deleting: "
        dropdb $db || error_and_exit "An error occured @DB deletion: $db"
        echo "DONE."
      fi
      echo -e -n "Restoring $db: "
      createdb $db && pg_restore -d $db $file >/dev/null 2>&1
      echo "DONE."
    fi
  done
}

# drop all DB that begins with the given prefix + _ char
drop() {
  check_db "$1"
  for db in `psql template1 -t -c "SELECT datname from pg_database where datname ilike '${1}_%';"`; do
    echo -n "Deleting $db: "
    dropdb $db || error_and_exit "An error occured @DB deletion: $db"
    echo "DONE."
  done
}

# start a unifield server on free ports (between 8100 and 8200)
start_serv() {
  # check if configuration is here and right completed
  check_config
  source "$config"
  for var in server addons web sync ; do
    if [ -z ${!var} ] ; then
      error_and_exit "Variable not found in configuration file ($config): ${var}."
    fi
    # check directories existence
    if ! [ -d ${!var} ] ; then
      error_and_exit "Directory not found (${var} variable in $config file): ${!var}"
    fi
  done
  # check branch existence
  if ! [ -d "$2" ] ; then
    error_and_exit "Directory not found: $2"
  fi
  # search free ports
  echo -n "Searching free ports to launch server: "
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
  echo "DONE."
  # Prepare files and directories
  pidfile="${configdir}/tmp/$1.pid"
  logfile="${configdir}/tmp/$1.log"
  if [ -a "${configdir}/tmp" ] ; then
    if ! [ -d "${configdir}/tmp" ] ; then
      error_and_exit "Directory ${configdir}/tmp not found! Is that a file?"
    fi
  else
    echo -n "Creating ${configdir}/tmp directory: "
    mkdir ${configdir}/tmp
    echo "DONE."
  fi
  touch ${logfile}
  echo -n "Launching openerp-server: "
  LANG=C start-stop-daemon --start --pidfile ${pidfile} \
  --background --make-pidfile --exec ${server}/bin/openerp-server.py -- \
  --addons-path=${addons},${wm},${sync} --additional-xml --without-demo=all \
  --logfile=${logfile} \
  --no-xmlrpcs --no-xmlrpc --netrpc-port=${NETRPCPORT}
  # Wait 15 second before launching MKDB script
  sleep 15s
  echo "DONE."
  echo -e "Ports used:\nxmlrpc: ${XMLRPCPORT}\nnetrpc: ${NETRPCPORT}"
  echo "You can launch a web server using this command:"
  echo "${web}/openerp-web.py --openerp-port=${NETRPCPORT}"
}

stop_serv() {
  pidfile="${configdir}/tmp/$1.pid"
  logfile="${configdir}/tmp/$1.log"
  if ! [ -a "$pidfile" ] ; then
    error_and_exit "PID file $pidfile not found!\nThis probably means that no server is working."
  fi
  echo "Stopping server for $1"
  start-stop-daemon --stop --quiet --pidfile $pidfile --oknodo
  # Delete some files (PID and log)
  rm -f $pidfile $logfile
}

#####
## TESTS
###

# We need 2 params at least
if [ $# -lt 2 ] ; then
  error "Need at least 2 parameters."
  usage
  exit 1
fi

prefix=$1
command=$2
branch=$3

if [ -z "$branch" ] ; then
  check_config
  source "$config"
  if [ -z ${wm} ] ; then
    error_and_exit "Variable not found in configuration file ($config): wm."
  fi

  branch="${wm}"
fi

#####
## MAIN
###

# Check command
case $command in 
  backup)
  backup "$prefix"
  ;;
  restore)
  restore "$prefix"
  ;;
  drop)
  drop "$prefix"
  ;;
  start)
  start_serv "$prefix" "$branch"
  ;;
  stop)
  stop_serv "$prefix"
  ;;
  extract)
  drop "$prefix" && restore "$prefix" && start_serv "$prefix" "$branch"
  ;;
  help)
  usage
  ;;
  *)
  error "Command $command not found!"
  usage
  exit 1
  ;;
esac

exit 0
