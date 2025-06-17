#!/bin/bash

if [ "$1" = "-h" ]; then
	echo "usage: $0 [server-branch] [web-branch]"
	exit 0
fi

set -e
SERVER_BRANCH=lp:unifield-server
CLIWEB_BRANCH=lp:unifield-web
PREREQ=/home/jf/Virt/prereq-py3.12-win-aio.qcow2
PYPATH=../../python-3.13.5/
PGVER=14.18-1
[ -n "$1" ] && SERVER_BRANCH=$1
[ -n "$2" ] && CLIWEB_BRANCH=$2

echo "Server branch: $SERVER_BRANCH"
echo "Web branch: $CLIWEB_BRANCH"

br=`basename $SERVER_BRANCH`

./package.py \
        --version UF38.0dev \
        --win-image=$PREREQ \
        --server-branch=$SERVER_BRANCH \
        --client-web-branch=$CLIWEB_BRANCH \
        --pypath=$PYPATH \
        --pgver=$PGVER \
        $@

