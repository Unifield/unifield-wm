#!/bin/bash

if [ "$1" = "-h" ]; then
	echo "usage: $0 [server-branch] [web-branch]"
	exit 0
fi

set -e
SERVER_BRANCH=lp:unifield-server/uf37
CLIWEB_BRANCH=lp:unifield-web/uf37
PREREQ=/home/jf/Virt/prereq-py3.10-win-aio.qcow2
PYPATH=../../WPy64-310111/python-3.10.11.amd64/
PGVER=14.18-1
BSDIFF=bsdiff4-1.2.1-cp310-cp310-win_amd64.whl
[ -n "$1" ] && SERVER_BRANCH=$1
[ -n "$2" ] && CLIWEB_BRANCH=$2

echo "Server branch: $SERVER_BRANCH"
echo "Web branch: $CLIWEB_BRANCH"

br=`basename $SERVER_BRANCH`

./package.py \
        --version UF37.0 \
        --win-image=$PREREQ \
        --server-branch=$SERVER_BRANCH \
        --client-web-branch=$CLIWEB_BRANCH \
        --pypath=$PYPATH \
        --pgver=$PGVER \
        --bsdiff=$BSDIFF \
        $@

