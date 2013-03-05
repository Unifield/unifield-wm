#!/bin/bash

HDIR=/home/odoo/vm/winxp26_for_60/
#SSH_AUTH_SOCK=
#SSH_AGENT_PID=

# For pilot
SERVER_BRANCH=lp:unifield-server/pilot
ADDONS_BRANCH=lp:unifield-addons,lp:unifield-wm/pilot,lp:unifield-wm/pilot
CLIWEB_BRANCH=lp:unifield-web/pilot

# For pilot + integrated patch + AIO-45
SERVER_BRANCH=lp:~unifield-team/unifield-server/server_aio_45
CLIWEB_BRANCH=lp:~unifield-team/unifield-web/web_aio_45

./package61_msf.py --vm-winxp-image=${HDIR}/winxp26.qcow2 \
        --vm-winxp-ssh-key=${HDIR}/id_rsa \
        --build msf \
        --version 6.0 \
        --addons-branch=$ADDONS_BRANCH \
        --server-branch=$SERVER_BRANCH \
        --client-web-branch=$CLIWEB_BRANCH \
        $@

