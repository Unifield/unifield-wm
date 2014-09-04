#!/bin/bash

HDIR=/datas/progs/MSF/packaging
#SSH_AUTH_SOCK=
#SSH_AGENT_PID=

CLIENT_BRANCH=lp:openobject-client/6.0
ADDONS_BRANCH=lp:unifield-addons,lp:unifield-wm,lp:~unifield-team/unifield-wm/sync_module_prod
SERVER_BRANCH=lp:~unifield-team/unifield-server/sync-odoo-task-9530
CLIWEB_BRANCH=lp:unifield-web

./package61_msf.py --vm-winxp-image=${HDIR}/winxp26.qcow2 \
        --vm-winxp-ssh-key=${HDIR}/.ssh/id_rsa \
        --build msf \
        --version 6.0dbpwd \
        --client-branch=$CLIENT_BRANCH \
        --addons-branch=$ADDONS_BRANCH \
        --server-branch=$SERVER_BRANCH \
        --client-web-branch=$CLIWEB_BRANCH \
        $@
        
