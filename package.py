#!/usr/bin/env python
import re
import os
import sys
import optparse
import signal
import subprocess
import time


#----------------------------------------------------------
# Utils
#----------------------------------------------------------
join = os.path.join

def mkdir(d):
    if not os.path.isdir(d):
        os.makedirs(d)

def url2dir(n):
    return n.replace('/','_').replace(':','').replace('~','')

def system(l,chdir=None, exit_on_failure=True):
    print l
    if chdir:
        cwd = os.getcwd()
        os.chdir(chdir)
    if isinstance(l,list):
        rc=os.spawnvp(os.P_WAIT, l[0], l)
    elif isinstance(l,str):
        tmp=['sh','-c',l]
        rc=os.spawnvp(os.P_WAIT, tmp[0], tmp)
    if chdir:
        os.chdir(cwd)
    if exit_on_failure and rc != 0:
        print("Failed to execute command '%s'" % (l,))
        sys.exit(2)
    return rc

class chdir_context(object):
    def __init__(self, new_directory=None):
        self.new_directory = new_directory
        self.old_directory = None

    def __enter__(self):
        if self.new_directory:
            self.old_directory = os.getcwd()
            os.chdir(self.new_directory)

    def __exit__(self, *exc_info):
        if self.old_directory:
            os.chdir(self.old_directory)

def system_w_output(l, chdir=None):
    with chdir_context(chdir):
        process = subprocess.Popen(l, stdout=subprocess.PIPE)
        output, unused_err = process.communicate()
        retcode = process.poll()
        if retcode:
            raise subprocess.CalledProcessError(retcode, l[0], output=output)
        return output

#----------------------------------------------------------
# Stages
#----------------------------------------------------------

def init(o):
    for i in [o.repo, o.work, o.pkg, o.pub, join(o.pub,"src"), join(o.pub,"deb"), join(o.pub,"exe"), join(o.pub,"rpm")]:
        mkdir(i)
    if not os.path.isdir(join(o.repo,'.bzr')):
        system(['bzr','init-repo',o.repo])

def branch_or_update(b,d):
    if os.path.isdir(d):
        system(['bzr','pull','-d',d])
    else:
        system(['bzr','branch',b,d])

def branch_get_summary(prefix, d):
    branch_info = system_w_output(['bzr', 'info', '-q'], d)
    branch_location = re.findall('parent branch: (.*)$', branch_info, re.M)[0]
    branch_revno = system_w_output(['bzr', 'revno'], d)
    summary = "%s:\n    URL: %s\n    REV: %s" % (prefix, branch_location, branch_revno)
    return summary

def update(o):
    branch_or_update(o.server_branch,o.server_dir)
    if o.client_web_branch:
        branch_or_update(o.client_web_branch, o.client_web_dir)

def update_branch_summary(o):
    s = ['PACKAGING:']
    s.append(branch_get_summary('packging branch', '.'))
    s.append('SERVER:')
    s.append(branch_get_summary(o.server_branch,o.server_dir))
    if o.client_web_branch:
        s.append('WEB CLIENT:')
        s.append(branch_get_summary(o.client_web_branch, o.client_web_dir))
    open(os.path.join('windows', 'static', 'server-extra', 'PKGINFO'), 'w').write('\n'.join(s))

def rsync(o):
    system(["rsync","-a","--exclude",".bzr","--delete", "%s/"%o.server_dir, o.work])
    if o.client_web_branch:
        system(["rsync","-a","--exclude",".bzr", "%s/" % o.client_web_dir, o.work_client_web])

def version(o):
    open(join(o.work,'bin','release.py'),'a').write('version = "%s-%s"'%(o.version,o.timestamp))
    open(join(o.work_client_web,'openobject','release.py'), 'a').write('version = "%s-%s"'%(o.version,o.timestamp))

class KVM(object):
    def __init__(self, o, image, ssh_key=''):
        ip = '127.0.0.1'
        port = '10022'
        self.remoteip = str(ip)
        self.remoteport = str(port)
        self.o = o
        self.image = image
        self.ssh_key = ssh_key
        self.login = 'openerp'

    def timeout(self,signum,frame):
        print "vm timeout kill",self.pid
        os.kill(self.pid,15)

    def start(self):
        l="kvm -m 1G -net nic,model=rtl8139 -net user,hostfwd=tcp:127.0.0.1:10022-:22 -drive".split(" ")
        l.append('file=%s,snapshot=on'%self.image)
        l.append('-nographic')
        self.pid=os.spawnvp(os.P_NOWAIT, l[0], l)
        time.sleep(30)
        signal.alarm(5000)
        signal.signal(signal.SIGALRM, self.timeout)
        try:
            self.run()
        finally:
            signal.signal(signal.SIGALRM, signal.SIG_DFL)
            os.kill(self.pid,15)
            time.sleep(5)

    def ssh(self,cmd):
        l=['ssh','-o','UserKnownHostsFile=/dev/null','-o','StrictHostKeyChecking=no','-p',self.remoteport,'-i',self.ssh_key,'%s@%s'%(self.login,self.remoteip),cmd]
        system(l)
    def rsync(self,args,options='--delete --exclude .bzrignore'):
        cmd ='rsync -rtv -e "ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -p %s -i %s" %s %s' % (self.remoteport, self.ssh_key, options, args)
        system(cmd)
    def run(self):
        pass

class KVMWinBuildAllInOneExe(KVM):
    def run(self):
        self.login = 'Naresh'
        self.ssh("mkdir -p build")
        self.rsync('%s/ Naresh@%s:build/server/'% (self.o.work, self.remoteip))
        self.rsync('%s/ Naresh@%s:build/web/' % (self.o.work_client_web, self.remoteip))
        f = open('windows/Makefile.version','w')
        f.write('MAJOR_VERSION=%s\n' % (self.o.major,))
        f.write('MINOR_VERSION=%s\n' % (self.o.minor,))
        f.write('REVISION_VERSION=%s\n' % (1,))
        f.write('BUILD_VERSION=%s\n' % (self.o.timestamp,))
        f.close()
        self.rsync('windows/ Naresh@%s:build/windows/' % (self.remoteip,))
        # This one uses a let's encrypt cert, which WinXP cannot handle.
        self.ssh("PYTHONHTTPSVERIFY=0 /cygdrive/c/Python27/Scripts/pip --verbose --no-cache-dir install egenix-mx-base==3.2.9")
        self.ssh("/cygdrive/c/Python27/Scripts/pip --verbose --no-cache-dir install ./build/server")
        self.ssh("/cygdrive/c/Python27/Scripts/pip --verbose --no-cache-dir install ./build/web")
        self.ssh("PATH=/cygdrive/c/Python27:/cygdrive/c/Python27/Scripts:$PATH make -C build/windows allinone")
        # For an unknown reason it seems that files timestamp matters
        self.rsync('Naresh@%s:build/windows/files/ %s/'% (self.remoteip, self.o.pkg,) ,'')
        os.chmod(join(self.o.pkg, 'openerp-allinone-setup-%(major)s.%(minor)s-%(timestamp)s-r1.txt' % \
                                  dict([(x, getattr(self.o, x)) for x in ['major','minor','timestamp']])), 0644)
        print "KVMWinBuildExe.run(): done"

#----------------------------------------------------------
# Options and Main
#----------------------------------------------------------

def options():
    op = optparse.OptionParser()
    op.add_option("-b", "--build", default='msf', help="build directory (%default)", metavar="DIR")
    op.add_option("-v", "--version", default='', help="version (%default)")
    op.add_option("-t", "--timestamp", default=time.strftime("%Y%m%d-%H%M%S",time.gmtime()), help="timestamp (%default)")
    op.add_option("-s", "--server-branch", default='lp:~openerp/openobject-server/6.1', help="%default")
    op.add_option("-y", "--client-web-branch", default='lp:~openerp/openobject-client-web/6.0', help="%default")
    op.add_option("", "--win-image", default='prereq.qcow2', help="%default")
    op.add_option("", "--win-key", default='key', help="%default")
    (o, args) = op.parse_args()
    # derive other options
    o.repo = join(o.build, 'repo')
    o.pkg = join(o.build, 'pkg')
    o.pub = join(o.build, 'pub')
    if o.version == '':
        raise RuntimeError('version must be set')
    o.version_full = '%s-%s'%(o.version,o.timestamp)
    o.major, o.minor = o.version.split('.')
    o.work = join(o.build, 'openerp-%s'%o.version_full)
    o.work_client = join(o.build, 'openerp-client-%s'%o.version_full)
    o.work_client_web = join(o.build, 'openerp-client-web-%s'%o.version_full)
    o.server_dir = join(o.repo, url2dir(o.server_branch))
    o.client_web_dir = join(o.repo, url2dir(o.client_web_branch))
    return o

def main():
    o = options()
    init(o)
    update(o)
    update_branch_summary(o)
    rsync(o)
    version(o)
    if os.path.isfile(o.win_image):
        KVMWinBuildAllInOneExe(o, o.win_image, o.win_key).start()
    else:
        raise RuntimeError('file not found: %s' % o.win_image)
    return

if __name__ == '__main__':
    main()
