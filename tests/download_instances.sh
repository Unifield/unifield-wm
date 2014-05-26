#!/bin/sh

user=$1

[ -z "$user" ] && echo "missing: user" && exit 1

databases=`ssh root@uf0003.unifield.org \
	su -l -c "'psql -l -P format=unaligned'" $user | \
	awk -F '|' "(\\\$2 == \"$user\") {print \\\$1}"`

out="databases_${user}"
drop_script="$out/drop_instances.sh"
mkdir -p $out
echo "#!/bin/sh" > "$drop_script"
chmod +x "$drop_script"

for db in $databases
do

	ssh root@uf0003.unifield.org \
		su -l -c "'pg_dump -COx $db | gzip'" $user \
		> "$out/${db}.dump.gz"

	echo "dropdb \"$db\"" >> "$drop_script"

done
