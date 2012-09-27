#!/usr/bin/env python
import glob
import os
import optparse
import signal
import shutil
import socket
import subprocess
import time
import xmlrpclib


#----------------------------------------------------------
# Utils
#----------------------------------------------------------
join = os.path.join

def mkdir(d):
    if not os.path.isdir(d):
        os.makedirs(d)

def url2dir(n):
    return n.replace('/','_').replace(':','').replace('~','')

def system(l,chdir=None):
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
    return rc

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
        #system(['bzr','pull','-d',d,'--overwrite'])
        system(['bzr','pull','-d',d])
    else:
        system(['bzr','branch',b,d])

def branch_revert_and_apply_patches(d, patches):
    system(['bzr', 'revert', '--no-backup'], d)
    for p in patches:
        system('patch -p0 < %s' % (p,), d)

def update(o):
    for addon_branch, addon_dir in zip(o.addons_branches, o.addons_dirs):
        branch_or_update(addon_branch,addon_dir)
    branch_or_update(o.server_branch,o.server_dir)
    branch_revert_and_apply_patches(o.server_dir, o.server_patches)
    if o.web_branch:
        branch_or_update(o.web_branch,o.web_dir)
        branch_revert_and_apply_patches(o.web_dir, o.web_patches)
    if o.client_web_branch:
        branch_or_update(o.client_web_branch, o.client_web_dir)
        branch_revert_and_apply_patches(o.client_web_dir, o.client_web_patches)

def rsync(o):
    exclude_rsync = [ '--exclude', '.bzr',
                    '--exclude', '.bzrignore',
                    '--exclude', '/__init__.py',
                    '--exclude', '/base',
                    '--exclude', '/base_quality_interrogation.py' ]

    system(["rsync","-a","--exclude",".bzr","--delete", "%s/"%o.server_dir, o.work])
    for addon_dir in o.addons_dirs:
        system(["rsync","-a"]+ exclude_rsync + ["%s/" % addon_dir, o.work_addons])
    #if o.web_branch:
    #    system(["rsync","-a","--exclude",".bzr", "%s/addons/"%o.web_dir, o.work_addons])
    if o.client_web_branch:
        system(["rsync","-a","--exclude",".bzr", "%s/" % o.client_web_dir, o.work_client_web])

def version(o):
    open(join(o.work,'bin','release.py'),'a').write('version = "%s-%s"'%(o.version,o.timestamp))
    open(join(o.work_client_web,'openobject','release.py'), 'a').write('version = "%s-%s"'%(o.version,o.timestamp))

def sdist(o):
    cmd=['python','setup.py', '--quiet', 'sdist', '-d','../pkg']
    system(cmd,o.work)
    system(cmd,o.work_client)

def bdist_rpm(o):
    cmd=['python2.6','setup.py', '--quiet', 'bdist_rpm', '-d','../pkg']
    system(cmd,o.work)
    shutil.rmtree(join(o.work,'dist'))

def debian(o):
    cmd=['sed','-i','1s/^.*$/openerp (%s-%s-1) testing; urgency=low/'%(o.version,o.timestamp),'debian/changelog']
    system(cmd,o.work)
    cmd=['dpkg-buildpackage','-rfakeroot']
    system(cmd,o.work)
    l = glob.glob(join(o.build,'openerp_*'))
    for i in l:
        shutil.move(i,o.pkg)

class KVM(object):
    def __init__(self, o, image, ssh_key='', ip=None, port=None):
        if ip is None:
            ip = '127.0.0.1'
        if port is None:
            port = '10022'
        self.remoteip = ip
        self.remoteport = port
        self.o = o
        self.image = image
        self.ssh_key = ssh_key
        self.login = 'openerp'

    def timeout(self,signum,frame):
        print "vm timeout kill",self.pid
        os.kill(self.pid,15)

    def start(self):
        l="kvm -net nic -net user,hostfwd=tcp:127.0.0.1:10022-:22,hostfwd=tcp:127.0.0.1:18069-:8069,hostfwd=tcp:127.0.0.1:15432-:5432 -drive".split(" ")
        #l.append('file=%s,if=virtio,index=0,boot=on,snapshot=on'%self.image)
        l.append('file=%s,snapshot=on'%self.image)
        #l.extend(['-vnc','127.0.0.1:1'])
        l.append('-nographic')
        print l
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

class KVMDebianTestTgz(KVM):
    def run(self):
        l = glob.glob(join(self.o.pkg,'openerp-%s.tar.gz'%self.o.version_full))
        self.rsync('%s openerp@127.0.0.1:src/'%l[0])
        script = """
            tar xzvf src/*.tar.gz
            cd openerp*
            sudo python setup.py install
            sudo su - postgres -c "createuser -s $USER"
            createdb t1
            openerp-server --stop-after-init -d t1 -i ` python -c "import os;print ','.join([i for i in os.listdir('openerp/addons') if i not in ['auth_openid','caldav','document_ftp']]),;" `
        """
        self.ssh(script)
        self.ssh('nohup openerp-server >/dev/null 2>&1 &')
        time.sleep(2)
        l = xmlrpclib.ServerProxy('http://127.0.0.1:18069/xmlrpc/object').execute('t1',1,'admin','ir.module.module','search',[('state','=','installed')])
        i = len(l)
        if i >= 190:
            print "Tgz install: ",i," module installed"
        else:
            raise Exception("Tgz install failed only %s installed"%i)
        time.sleep(2)

class KVMDebianTestDeb(KVM):
    def run(self):
        l = glob.glob(join(self.o.pkg,'*%s*.deb'%self.o.timestamp))
        self.rsync('%s openerp@127.0.0.1:deb/'%l[0])
        script = """
            sudo dpkg -i deb/*
            sudo su - postgres -c "createuser -s $USER"
            createdb t1
            openerp-server --stop-after-init -d t1 -i base
        """
        #` python -c "import os;print ','.join([i for i in os.listdir('/usr/share/pyshared/openerp/addons') if i not in ['auth_openid','caldav','document_ftp']]),;" `
        self.ssh(script)
        time.sleep(2)
        l = xmlrpclib.ServerProxy('http://127.0.0.1:18069/xmlrpc/object').execute('t1',1,'admin','ir.module.module','search',[('state','=','installed')])
        i = len(l)
        if i >= 1:
            print "Deb install: ",i," module installed"
        else:
            raise Exception("Tgz install failed only %s installed"%i)
        time.sleep(2)

class KVMWinBuildAllInOneExe(KVM):
    def run(self):
        self.login = 'Naresh'
        self.ssh("mkdir -p build")
        self.rsync('%s/ Naresh@%s:build/server/'% (self.o.work, self.remoteip))
        self.rsync('%s/ Naresh@%s:build/web/' % (self.o.work_client_web, self.remoteip))
        f = open('windows/Makefile.version','w')
        f.write('MAJOR_VERSION=%s\n' % (self.o.major,))
        f.write('MINOR_VERSION=%s\n' % (self.o.minor,))
        f.write('REVISION_VERSION=%s\n' % (1,)) # TODO: get real server revision
        f.write('BUILD_VERSION=%s\n' % (self.o.timestamp,))
        #f.write("VERSION=%s\n" % self.o.version_full)
        f.close()
        self.rsync('windows/ Naresh@%s:build/windows/' % (self.remoteip,))
        self.rsync('windows/wkhtmltopdf/ Naresh@%s:build/server/win32/wkhtmltopdf/' % (self.remoteip,))
        self.ssh("cd build/windows; ~/run make allinone;")
        # For an unknown fucking reason it seems that files timestamp matters
        self.rsync('Naresh@%s:build/windows/files/ %s/'% (self.remoteip, self.o.pkg,) ,'')
        print "KVMWinBuildExe.run(): done"

class KVMWinTestExe(KVM):
    def run(self):
        self.login = 'Naresh'
        setuppath = "%s/openerp-allinone-setup-%s.exe" % (self.o.pkg, self.o.version_full)
        setuplog = setuppath.replace('exe','log')
        self.rsync('"%s" Naresh@127.0.0.1:'%setuppath)
        self.ssh("./openerp-allinone-setup* /S")

        # NO Please run the PostgreSQL\bin\createdb from windows: if this doesnwork use a python script with psycopg using CREATE DATABASE
        ## Change postgres config so it accepts our connections.
        #self.rsync('windows/test/pg_hba.conf "Naresh@127.0.0.1:/cygdrive/c/Program\ Files/OpenERP\ %s/PostgreSQL/data/pg_hba.conf"'%self.o.version_full)
        #self.rsync('windows/test/postgresql.conf "Naresh@127.0.0.1:/cygdrive/c/Program\ Files/OpenERP\ %s/PostgreSQL/data/postgresql.conf"'%self.o.version_full)
        #self.ssh('net stop "PostgreSQL For OpenERP"')
        #self.ssh('net start "PostgreSQL For OpenERP"')
        #subprocess.call('createdb -e -h 127.0.0.1 -p 15432 -U openpg pack'.split(' '), env={'PGPASSWORD':'openpgpwd'})

        self.ssh('"/cygdrive/c/Program Files/OpenERP %s/server/openerp-server.exe" -d pack -i base,report_webkit --stop-after-init --log-level=test'%self.o.version_full)
        self.rsync('"Naresh@127.0.0.1:/cygdrive/c/Program Files/OpenERP %s/server/openerp-server.log" "%s.log"'%(self.o.version_full, setuplog))

class KVMWinBuildGtk(KVM):
    def run(self):
        self.login = 'Naresh'
        self.rsync('--exclude .bzr/ %s/ Naresh@127.0.0.1:/Desktop/client/'%self.o.client_dir)
        #self.ssh("cd /Desktop/client/;python setup.py py2exe;/cygdrive/c/cygwin/makensis setup.nsi;mv openerp-client-setup-* openerp-client-%s.exe"%self.o.version_full)
        self.ssh("./build.sh;cd /Desktop/client/;mv openerp-client-setup-* openerp-client-%s.exe"%self.o.version_full)
        self.rsync('Naresh@127.0.0.1:/Desktop/client/openerp-client-%s.exe %s/'%(self.o.version_full,self.o.pkg),'')
        system('chmod 0644 *',self.o.pkg)
        print "KVMWinBuildGtk.run(): done"

def publish_move(o,srcs,dest):
    for i in srcs:
        shutil.move(i,dest)
        # do the symlink
        bn = os.path.basename(i)
        latest = bn.replace(o.timestamp,'latest')
        latest_full = join(dest,latest)
        if bn != latest:
            if os.path.islink(latest_full):
                os.unlink(latest_full)
            os.symlink(bn,latest_full)

def publish(o):
    l = glob.glob(join(o.pkg,'*%s-1*.rpm'%o.timestamp.replace('-','_')))
    publish_move(o,l,join(o.pub,'rpm'))

    l = glob.glob(join(o.pkg,'*_*%s-1*'%o.timestamp))
    publish_move(o,l,join(o.pub,'deb'))
    system('dpkg-scanpackages . /dev/null | gzip -9c > Packages.gz',join(o.pub,'deb'))

    l = glob.glob(join(o.pkg,'*%s*.tar.gz'%o.timestamp))
    publish_move(o,l,join(o.pub,'src'))

    l = glob.glob(join(o.pkg,'*all*%s*.exe'%o.timestamp))
    publish_move(o,l,join(o.pub,'exe'))

    l = glob.glob(join(o.pkg,'*client*%s*.exe'%o.timestamp))
    publish_move(o,l,join(o.pub,'exe'))

def cleanup(o):
    shutil.rmtree(o.work)
    shutil.rmtree(o.work_client)

#----------------------------------------------------------
# Options and Main
#----------------------------------------------------------

def options():
    op = optparse.OptionParser()
    op.add_option("-b", "--build", default='.', help="build directory (%default)", metavar="DIR")
    op.add_option("-v", "--version", default='6.0', help="version (%default)")
    op.add_option("-t", "--timestamp", default=time.strftime("%Y%m%d-%H%M%S",time.gmtime()), help="timestamp (%default)")
    op.add_option("-a", "--addons-branch", default='lp:~openerp/openobject-addons/6.1', help="%default")
    op.add_option("-s", "--server-branch", default='lp:~openerp/openobject-server/6.1', help="%default")
    op.add_option("-w", "--web-branch", default='lp:~openerp/openerp-web/6.1', help="%default")
    op.add_option("-y", "--client-web-branch", default='lp:~openerp/openobject-client-web/6.0', help="%default")
    op.add_option("-c", "--client-branch", default='lp:~openerp/openobject-client/6.1', help="%default")
    op.add_option("", "--vm-debian-image", default='/home/odoo/vm/debian6/debian6.vmdk', help="%default")
    op.add_option("", "--vm-debian-ssh-key", default='/home/odoo/vm/debian6/debian6_id_rsa', help="%default")
    op.add_option("", "--vm-winxp-image", default='/home/odoo/vm/winxp26/winxp26.vdi', help="%default")
    op.add_option("", "--vm-winxp-ssh-key", default='/home/odoo/vm/winxp26/id_rsa', help="%default")
    op.add_option("", "--vm-winxp-port", default=10022, help="%default"),
    op.add_option("", "--vm-winxp-host", default='127.0.0.1', help="%default"),
    op.add_option("", "--build-only-gtk", default=False, action='store_true', help="%default")
    op.add_option("", "--build-only-allinone", default=False, action='store_true', help="%default")
    (o, args) = op.parse_args()
    # derive other options
    o.repo = join(o.build, 'repo')
    o.pkg = join(o.build, 'pkg')
    o.pub = join(o.build, 'pub')
    o.version_full = '%s-%s'%(o.version,o.timestamp)
    o.major, o.minor = o.version.split('.')
    o.work = join(o.build, 'openerp-%s'%o.version_full)
    o.work_client = join(o.build, 'openerp-client-%s'%o.version_full)
    o.work_addons = join(o.work, 'bin', 'addons')
    o.work_client_web = join(o.build, 'openerp-client-web-%s'%o.version_full)
    o.addons_branches = o.addons_branch.split(',')
    o.addons_dirs = [ join(o.repo, url2dir(addon_branch)) for addon_branch in o.addons_branches ]
    o.server_dir = join(o.repo, url2dir(o.server_branch))
    o.web_dir = join(o.repo, url2dir(o.web_branch))
    o.client_web_dir = join(o.repo, url2dir(o.client_web_branch))
    o.client_dir = join(o.repo, url2dir(o.client_branch))

    patches_dir = os.path.join(os.getcwd(), 'msf_patches')
    def patches_list(patch_list):
        return [ os.path.join(patches_dir, p) for p in patch_list ]
    o.web_patches = []
    o.server_patches = patches_list([
        'win32_server60_logout.patch',
        'win32_server60_python26.patch',
        'win32_server60_lxml_external_entities.patch',
        'all_server60_fix_test_disable_conffile_param.patch',
        'win32_server60_fix_dbrestore.patch',
    ])
    o.client_patches = patches_list([
        'win32_gtk60_python26.patch'
    ])
    o.client_web_patches = patches_list([
        'win32_web60_conffile.patch',
        'win32_web60_logout.patch',
        'win32_web60_python26.patch'
    ])
    return o

def main():
    o = options()
    init(o)
    update(o)  # update disabled since not bzr+ssh:// access
    rsync(o)
    version(o)
    if os.path.isfile(o.vm_winxp_image):
        KVMWinBuildAllInOneExe(o, o.vm_winxp_image, o.vm_winxp_ssh_key, ip=o.vm_winxp_host, port=o.vm_winxp_port).start()
    return
#    to_build = ['winexe', 'wintest', 'wingtk', 'source', 'debtest', 'rpm', 'deb']
#    if o.build_only_gtk:
#        to_build = ['wingtk']
#    if o.build_only_allinone:
#        to_build = ['winexe']
#    # exe
#    if os.path.isfile(o.vm_winxp_image):
#        if 'winexe' in to_build:
#            KVMWinBuildExe(o, o.vm_winxp_image, o.vm_winxp_ssh_key).start()
#        if 'wintest' in to_build:
#            KVMWinTestExe(o, o.vm_winxp_image, o.vm_winxp_ssh_key).start()
#        if 'wingtk' in to_build:
#            KVMWinBuildGtk(o, o.vm_winxp_image, o.vm_winxp_ssh_key).start()
#    # tgz
#    if 'source' in to_build:
#        sdist(o)
#    if os.path.isfile(o.vm_debian_image):
#        if 'debtest' in to_build:
#            KVMDebianTestTgz(o, o.vm_debian_image, o.vm_debian_ssh_key).start()
#    # rpm
#    if 'rpm' in to_build:
#        bdist_rpm(o)
#    # deb
#    if 'deb' in to_build:
#        debian(o)
#    if os.path.isfile(o.vm_debian_image):
#        if 'debtest' in to_build:
#            KVMDebianTestDeb(o, o.vm_debian_image, o.vm_debian_ssh_key).start()
#    # publish
    publish(o)
    cleanup(o)

if __name__ == '__main__':
    main()
