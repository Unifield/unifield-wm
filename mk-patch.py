#!/usr/bin/env python

# This script is meant to run on Windows. It unpacks
# two AIOs and then calculates the patch between the two
# of them.

import sys
import zipfile
import time
import re
import filecmp
import os
import subprocess

if len(sys.argv) != 3:
    print('Expected 2 arguments: <from_exe> <to_exe>')
    sys.exit()
from_exe = sys.argv[1]
to_exe = sys.argv[2]

# Skip things that do not belong in patch files.
def should_skip(name):
    return (
        name.endswith('.pyc') or
        '__pychache__' in name or
        name in [
            # this will be added at the end of this script instead
            os.path.join('Server', 'release.py'),
            os.path.join('Server', 'unifield-version.txt'),
            # these are related to the AIO and should not go in the patch
            # TODO: except for the migration ....
            'Uninstall.exe',
            os.path.join('Web', 'Uninstall.exe'),
            # these config files on the end-user installs should never
            # be overwritten
            os.path.join('Server', 'openerp-server.conf'),
            os.path.join('Web', 'conf', 'openerp-web-oc.cfg'),
        ])

# Change the directory from the filesystem into a destination directory in
# the patchfile (this mapping was set by the implementation of
# updater.py)

def dirmap(directory):
    directory = directory.replace(sys.argv[2], '')
    if directory.startswith(os.path.sep):
        directory = directory[1:]
    return directory

# The plan:
#
# run the two AIO installers
#   move the old one to a different directory to compare
#   to the new one.
#
# for each file in the original distribution:
#   remember it's name
#   if not in new distribution:
#     add to delete list
#   else
#     if new distribution version is different:
#       add to patch file
# for each file in the new distribution:
#   if we did not already see it:
#     add to patch file

old = r'c:\Program Files (x86)\msf\Unifield-old'
new = r'c:\Program Files (x86)\msf\Unifield'

sys.stdout.flush()
cmd_call = [from_exe, '/S', r'/PGINSTDIR=c:\from_db']
print("Unpacking %s" % (' '.join(cmd_call),))
subprocess.call(cmd_call)

print("Stopping servers.")
sys.stdout.flush()
subprocess.call('net stop openerp-server-6.0 /y', shell=True)
subprocess.call('net stop openerp-web-6.0 /y', shell=True)

# it gets installed into new, so move it to old, so we can install
# to_exe into new
print("Moving to %s" % old)
sys.stdout.flush()
os.rename(new, old)

cmd_call = [to_exe, '/S', r'/PGINSTDIR=c:\to_db']
print("Unpacking: %s" % (' '.join(cmd_call), ))
sys.stdout.flush()
subprocess.call(cmd_call)

deleted = []
seen = {}
zf = zipfile.ZipFile('patch.zip', mode='w', compression=zipfile.ZIP_DEFLATED)

for (dirpath, dirnames, filenames) in os.walk(old):
    relpath = dirpath.replace(old, '')
    if len(relpath) > 0 and relpath[0] == os.path.sep:
        relpath = relpath[1:]
    if relpath == 'ServerLog':
        continue
    if relpath == 'pgsql':
        continue
    for f in filenames:
        oldf = os.path.join(dirpath, f)
        newf = os.path.join(new, relpath, f)
        dest = os.path.join(dirmap(relpath), f)
        if should_skip(dest):
            continue
        if not os.path.exists(newf):
            print("del %s" % dest)
            deleted.append(dest)
        elif not filecmp.cmp(oldf, newf, False):
            print("write mod %s" % dest)
            zf.write(newf, dest)
        seen[dest] = True

for (dirpath, dirnames, filenames) in os.walk(new):
    relpath = dirpath.replace(new, '')
    if len(relpath) > 0 and relpath[0] == os.path.sep:
        relpath = relpath[1:]
    if relpath == 'ServerLog':
        continue
    if relpath.startswith('pgsql'):
        continue
    for f in filenames:
        newf = os.path.join(new, relpath, f)
        dest = os.path.join(dirmap(relpath), f)
        if should_skip(dest) or dest in seen:
            continue
        print("write add %s" % dest)
        zf.write(newf, dest)

# special case for release.py: add the date onto the end of the
# given version
version = 'unknown'
with open(os.path.join(new, 'Server', 'release.py')) as f:
    lines = f.readlines()
out = []
for line in lines:
    if line.startswith('version = '):
        exec(line)
    else:
        out += line

if not re.match('.*-[0-9]{8}-[0-9]{6}$', version):
    version += time.strftime('-%Y%m%d-%H%M%S')
    print("Version inserted into the patch is: %s" % version)
else:
    print("Version in the source is already timestamped: %s" % version)

out += 'version = \'%s\'\n' % version
zf.writestr('Server/release.py', ''.join(out))

zf.writestr('delete.txt', '\n'.join(deleted))
zf.close()

print("Done. The resulting patch is:")
subprocess.call("dir patch.zip", shell=True)
