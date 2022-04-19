#!/bin/bash

if [ "$1" = "-h" ]; then
	echo "usage: $0 [server-branch] [web-branch]"
	exit 0
fi

set -e
SERVER_BRANCH=lp:~jfb-tempo-consulting/unifield-server/py3
CLIWEB_BRANCH=lp:~jfb-tempo-consulting/unifield-web/py3
PREREQ=/opt/prereq-py3.10-win-aio.qcow2
[ -n "$1" ] && SERVER_BRANCH=$1
[ -n "$2" ] && CLIWEB_BRANCH=$2

echo "Server branch: $SERVER_BRANCH"
echo "Web branch: $CLIWEB_BRANCH"

br=`basename $SERVER_BRANCH`

./package.py \
        --version uf24.0py3 \
        --win-image=$PREREQ \
        --server-branch=$SERVER_BRANCH \
        --client-web-branch=$CLIWEB_BRANCH \
        $@

