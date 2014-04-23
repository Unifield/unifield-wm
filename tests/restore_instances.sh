#!/bin/sh

for db in $*
do

	gunzip < "$db" | psql -d postgres >/dev/null

done
