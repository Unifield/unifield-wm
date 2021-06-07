include Makefile.version

WEB_DIRECTORY=../web
SERVER_DIRECTORY=../server
PY_DIRECTORY=../../WPy64-3940/python-3.9.4.amd64/
FILES_DIRECTORY=files

PG_VER=9.6.10-1
PG_ZIP=postgresql-$(PG_VER)-windows-binaries.zip

# vebose mode: /V4
MAKENSIS_ARGUMENTS=/DMAJOR_VERSION=$(MAJOR_VERSION) /DMINOR_VERSION=$(MINOR_VERSION) /DREVISION_VERSION=$(REVISION_VERSION) /DBUILD_VERSION=$(BUILD_VERSION) /DPG_VER=$(PG_VER) /X"SetCompressor /FINAL lzma"

LAUNCH_PY2EXE=python -B setup.py py2exe
LAUNCH_MAKENSIS=$(HOME)/nsis-3.06.1/Bin/makensis.exe $(MAKENSIS_ARGUMENTS) setup.nsi

default: allinone

server:
	$(PY_DIRECTORY)python.exe -m pip install -U pip
	$(PY_DIRECTORY)python.exe -m pip install bsdiff4-1.2.1-cp39-cp39-win_amd64.whl
	$(PY_DIRECTORY)python.exe -m pip install -r $(SERVER_DIRECTORY)/requirements.txt

web:
	$(PY_DIRECTORY)python.exe -m pip install bsdiff4-1.2.1-cp39-cp39-win_amd64.whl
	$(PY_DIRECTORY)python.exe -m pip install -r $(WEB_DIRECTORY)/requirements.txt

standalone:	server web

$(PG_ZIP):
	test -f $(PG_ZIP) || wget https://get.enterprisedb.com/postgresql/$(PG_ZIP)

# Extract the minimal Postgres install from the distribution zip file
pgsql: $(PG_ZIP)
	unzip $(PG_ZIP) pgsql/bin/* pgsql/lib/* pgsql/share/*
# the origin.txt file serves two purposes: to show where the files
# came from, and to workaround a bug in NSIS that it cannot scan a
# directory with only subdirs in it (it needs a file)
	echo $(PG_ZIP) > pgsql/origin.txt

allinone: standalone pgsql
	$(LAUNCH_MAKENSIS)
	cp ./openerp-*.exe $(FILES_DIRECTORY)/openerp-allinone-setup-$(MAJOR_VERSION).$(MINOR_VERSION)-$(BUILD_VERSION)-r$(REVISION_VERSION).exe
	cp ./static/server-extra/PKGINFO $(FILES_DIRECTORY)/openerp-allinone-setup-$(MAJOR_VERSION).$(MINOR_VERSION)-$(BUILD_VERSION)-r$(REVISION_VERSION).txt

