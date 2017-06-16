#!/bin/bash

SERVER_BRANCH=lp:unifield-server/trunk
CLIWEB_BRANCH=lp:unifield-web/trunk
[ -n "$1" ] && SERVER_BRANCH=$1
[ -n "$2" ] && CLIWEB_BRANCH=$2

br=`basename $SERVER_BRANCH`

./package.py \
        --version uf6.0-$br \
        --server-branch=$SERVER_BRANCH \
        --client-web-branch=$CLIWEB_BRANCH \
        $@

