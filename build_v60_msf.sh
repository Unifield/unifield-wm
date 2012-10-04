#!/bin/bash

HDIR=/home/odoo/vm/winxp26_for_60/
#SSH_AUTH_SOCK=
#SSH_AGENT_PID=

ADDONS_BRANCH=lp:~unifield-team/unifield-addons/sprint5,lp:~unifield-team/unifield-wm/sprint5,lp:~unifield-team/unifield-wm/sync_module_prod
SERVER_BRANCH=lp:unifield-server/sprint5
#SERVER_BRANCH=lp:~unifield-team/unifield-server/restart-and-update-cto
CLIWEB_BRANCH=lp:~unifield-team/unifield-web/sprint5

# For sprint5 RC3
ADDONS_BRANCH=lp:~unifield-team/unifield-addons/aio-dsp5rc3,lp:~unifield-team/unifield-wm/aio-dsp5rc3,lp:~unifield-team/unifield-wm/sync_module_prod
SERVER_BRANCH=lp:~unifield-team/unifield-server/aio-dsp5rc3
CLIWEB_BRANCH=lp:~unifield-team/unifield-web/aio-dsp5rc3

./package61_msf.py --vm-winxp-image=${HDIR}/winxp26.qcow2 \
        --vm-winxp-ssh-key=${HDIR}/id_rsa \
        --build msf \
        --version 6.0 \
        --addons-branch=$ADDONS_BRANCH \
        --server-branch=$SERVER_BRANCH \
        --client-web-branch=$CLIWEB_BRANCH \
        $@

chmod 0644 ./msf/pkg/openerp-allinone-setup-6.0-*.txt
