#!/bin/bash

if [ "$1" = "-h" ]; then
	echo "usage: $0 [server-branch] [web-branch]"
	exit 0
fi

set -e
SERVER_BRANCH=lp:unifield-server/trunk
CLIWEB_BRANCH=lp:unifield-web/trunk
[ -n "$1" ] && SERVER_BRANCH=$1
[ -n "$2" ] && CLIWEB_BRANCH=$2

echo "Server branch: $SERVER_BRANCH"
echo "Web branch: $CLIWEB_BRANCH"

br=`basename $SERVER_BRANCH`

./package.py \
        --version uf6.0-$br \
        --server-branch=$SERVER_BRANCH \
        --client-web-branch=$CLIWEB_BRANCH \
        $@

