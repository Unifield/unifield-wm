#! /bin/bash

# directory to store home directory (do NOT add / at the end)
TARGET_HOME_DIR="/home/SyncEnv"

# Directory to store RB ports, no trailing slash
BRANCHES="${TARGET_HOME_DIR}/BranchesList"

# 3 ranges of 1000 tcp ports should be reserved to manage 999 RB
# netstat is not used anymore
# files in $BRANCHES are greped to find unused port
NETRPC_INTV=53
XMLRP_INTV=54
WEB_INTV=55
# Nb of tries to found a free port
MAXTRIES=200

# admin password to manage db from the web interface
ADMINDBPASS="4unifield"

BRANCH_DEFAULT_SERVER="lp:unifield-server"
BRANCH_DEFAULT_ADDONS="lp:unifield-addons"
BRANCH_DEFAULT_WEB="lp:unifield-web"
BRANCH_DEFAULT_WM="lp:unifield-wm"
BRANCH_DEFAULT_SYNC="lp:~unifield-team/unifield-wm/sync_module_prod"
BRANCH_DEFAULT_ENV="lp:~unifield-team/unifield-wm/sync-env"

APACHE_PREFIX="xxx_syncenv"
APACHE_SITE_AVAILABLE="/etc/apache2/sites-available/syncenv"
BZR_TYPE=branch
#BZR_TYPE=checkout --lightweight

# @ linux user creation copy some files / dir (used by bzr and homere import)
FROM_DIR_TO_COPY="/opt/tools/runbot"
HOME_TO_COPY="${FROM_DIR_TO_COPY}/.ssh/ ${FROM_DIR_TO_COPY}/.bazaar/ ${FROM_DIR_TO_COPY}/common/.bzr ${FROM_DIR_TO_COPY}/tmp/"



REV="$1"
TAG=""
[ -z "$REV" ] && echo "Please specify revision: dsp-utp141 for example, optionally followed by a bzr tag" && exit 1
[ -n "$2" ] && TAG="-r $2 "
[ ! -d ${BRANCHES} ] && mkdir -m 700 -p $BRANCHES
BRANCHE_INFO="${BRANCHES}/${REV}"

if [ -f "${BRANCHE_INFO}" ]; then
    . "$BRANCHE_INFO"
    correct=skip
else
    correct=no
fi

while ! [ $correct == "y" ]
do
    echo "To get a specific tag or revno use the following notation: '-r revno lp:your_branch'"
    if ! [ "$correct" == "skip" ]; then
        echo -n "Enter server branch [${TAG}${BRANCH_DEFAULT_SERVER}]: "; read server
        [ -z "$server" ] && server="${TAG}${BRANCH_DEFAULT_SERVER}"
        echo -n "Enter addons branch [${TAG}${BRANCH_DEFAULT_ADDONS}]: "; read addons
        [ -z "$addons" ] && addons="${TAG}$BRANCH_DEFAULT_ADDONS"
        echo -n "Enter web branch [${TAG}$BRANCH_DEFAULT_WEB]: "; read web
        [ -z "$web" ] && web="${TAG}$BRANCH_DEFAULT_WEB"
        echo -n "Enter wm branch [${TAG}$BRANCH_DEFAULT_WM]: "; read wm
        [ -z "$wm" ] && wm="${TAG}$BRANCH_DEFAULT_WM"
        echo -n "Enter sync branch [${TAG}$BRANCH_DEFAULT_SYNC]: "; read sync
        [ -z "$sync" ] && sync="${TAG}$BRANCH_DEFAULT_SYNC"
        echo -n "Enter env branch [$BRANCH_DEFAULT_ENV]: "; read env
        [ -z "$env" ] && env=$BRANCH_DEFAULT_ENV
    fi
    echo "Please check the branches:"
    echo "+ Unifield Server: $server"
    echo "+ Unifield Addons: $addons"
    echo "+ Unifield Web: $web"
    echo "+ Unifield WM: $wm"
    echo "+ Unifield Sync: $sync"
    echo "+ Unifield Sync Env: $env"
    echo -n "=> Is it correct? [Y] "; read correct
    [ -z "$correct" ] && correct=y
done

FOUND=0
# TODO LOCK FILE
if [[ -n ${NETRPCPORT} ]]; then
    echo "Netrpcport ${NETRPCPORT} defined in $BRANCHE_INFO"
    let FOUND=$MAXTRIES+1

while [[ ${FOUND} -lt ${MAXTRIES} ]]; do
    NETRPCPORT=`shuf -i ${NETRPC_INTV}000-${NETRPC_INTV}999 -n 1`
    echo $NETRPCSTRING ${FOUND} ${MAXTRIES}
    let FOUND=${FOUND}+1
    if ! grep -xq "NETRPCPORT=${NETRPCPORT}" $BRANCHES; then
        let FOUND=MAXTRIES+1
    fi
done

if [[ ${FOUND} -eq ${MAXTRIES} ]]; then
   echo "Can't find a free port after ${MAXTRIES} tries ! Script Aborted"
   echo "If you feel lucky you can restart the script"
   exit 0
fi

echo "NETRPCPORT=${NETRPCPORT}" > $BRANCHE_INFO
echo "server=\"$server\"" >> $BRANCHE_INFO
echo "addons=\"$addons\"" >> $BRANCHE_INFO
echo "web=\"$web\"" >> $BRANCHE_INFO
echo "wm=\"$wm\"" >> $BRANCHE_INFO
echo "sync=\"$sync\"" >> $BRANCHE_INFO
echo "env=\"$env\"" >> $BRANCHE_INFO
let XMLRPCPORT=${XMLRP_INTV}${NETRPCPORT:2}
let WEBPORT=${WEB_INTV}${NETRPCPORT:2}

#echo "netrpc: ${NETRPCPORT}, xmlrpc: ${XMLRPCPORT}, web: ${WEBPORT}"

URL="http://$REV.dsp.uf3.unifield.org:$WEBPORT"

USERERP=${REV}
USERERP_HOME="${TARGET_HOME_DIR}/${REV}"
APACHEPORT="80"
APACHEHOST=${REV}
DBNAME="${REV}"

user_creation=0
check_init() {
    if [ -d ${USERERP_HOME} ]; then
        read -n 1 -p "Home dir exists, enter return to bypass user creation, or enter any non white space char to abort " user_creation
        if [ -n "$user_creation" ]; then
            echo ""
            echo "${USERERP_HOME} exists ! Aborting ..."
            exit 1
        else
            user_creation=1
        fi
    fi
    if [ ! -d ${TARGET_HOME_DIR} ]; then
        mkdir -m 755 -p ${TARGET_HOME_DIR}
    fi
    if [ ! -d ${APACHE_SITE_AVAILABLE} ]; then
        mkdir -m 755 -p ${APACHE_SITE_AVAILABLE}
    fi
}
create_file() {
sed -e "s#@@USERERP@@#${USERERP}#g" \
    -e "s#@@USERERP_HOME@@#${USERERP_HOME}#g" \
    -e "s#@@DBNAME@@#${DBNAME}#g" \
    -e "s#@@XMLRPCPORT@@#${XMLRPCPORT}#g" \
    -e "s#@@NETRPCPORT@@#${NETRPCPORT}#g" \
    -e "s#@@ADMINDBPASS@@#${ADMINDBPASS}#g" \
    -e "s#@@APACHEPORT@@#${APACHEPORT}#g" \
    -e "s#@@APACHEHOST@@#${APACHEHOST}#g" \
    -e "s#@@WEBPORT@@#${WEBPORT}#g" $1  > $2
}

config_file() {
    create_file ./File/openerp-server-initscript  /etc/init.d/${USERERP}-server
    create_file ./File/openerp-web-initscript /etc/init.d/${USERERP}-web
    create_file ./File/openerprc ${USERERP_HOME}/etc/openerprc
    create_file ./File/openerp-web.cfg ${USERERP_HOME}/etc/openerp-web.cfg
    create_file ./File/apache.conf ${APACHE_SITE_AVAILABLE}/${USERERP}
    create_file ./File/sync-env.py ${USERERP_HOME}/sync_env_script/config.py

    ln -sv "${APACHE_SITE_AVAILABLE}/${USERERP}" "/etc/apache2/sites-enabled/${APACHE_PREFIX}-${USERERP}"
    chown ${USERERP}.${USERERP} ${USERERP_HOME}/etc/openerp-web.cfg ${USERERP_HOME}/etc/openerprc ${USERERP_HOME}/sync_env_script/config.py
    update-rc.d ${USERERP}-web defaults
    update-rc.d ${USERERP}-server defaults
    chmod +x /etc/init.d/${USERERP}-web /etc/init.d/${USERERP}-server
}

init_user() {
    if [ ${user_creation} -eq 0 ]; then
        useradd -s /bin/bash -d ${USERERP_HOME} -m ${USERERP}
        for to_copy in ${HOME_TO_COPY}; do
            cp -a ${to_copy}/ ${USERERP_HOME}
        done
    fi
    su - postgres -c -- "createuser -S -R -d ${USERERP}"
    chown -R ${USERERP}.${USERERP} ${USERERP_HOME}
    su - ${USERERP} <<EOF

bzr ${BZR_TYPE} ${wm:=${BRANCH_DEFAULT_WM}} unifield-wm
bzr ${BZR_TYPE} ${addons:=${BRANCH_DEFAULT_ADDONS}} unifield-addons
bzr ${BZR_TYPE} ${web:=${BRANCH_DEFAULT_WEB}} unifield-web
bzr ${BZR_TYPE} ${server:=${BRANCH_DEFAULT_SERVER}} unifield-server
bzr ${BZR_TYPE} ${sync:=${BRANCH_DEFAULT_SYNC}} sync_module_prod
bzr ${BZR_TYPE} ${env:=${BRANCH_DEFAULT_ENV}} sync_env_script

mkdir etc log exports
echo Configure http://${REV}.dsp.uf3.unifield.org/
EOF
}

restart_servers() {
    echo "Apache: conf and reload"
    apache2ctl -t && /etc/init.d/apache2 reload || exit 2
    /etc/init.d/${USERERP}-server start
    /etc/init.d/${USERERP}-web start
}

check_init
init_user
config_file
restart_servers

echo "Net-RPC port: $NETRPCPORT"
echo "XML-RPC port: $XMLRPCPORT"
echo "HTML port: $WEBPORT"
echo "URL: $URL"
echo
echo "Please run ./mkdb.py as user $USERERP to finish:"
echo "su - $USERERP"
echo "cd ~/sync_env_script"
echo "./mkdb.py"
