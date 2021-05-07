#!/bin/bash

ssh_user=tempo
ssh_host=win10-2
ssh_port=22
# Driver for mk-patch.py, which is run from INSIDE of the builder VM.

if [ -z "$1" ]; then
    echo "usage: $0 exe"
    exit 1
fi

exe=$1


ssh_args="-p $ssh_port $ssh_user@$ssh_host"
# Put the script and the two files on the VM
echo "Copying exe files over to the VM."
scp -P $ssh_port $exe $ssh_user@$ssh_host:

exe=`basename $exe`

ssh $ssh_args chmod +x $exe
ssh $ssh_args TZ="Europe/Paris" ./$exe /S

