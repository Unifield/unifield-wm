include Makefile.version

WEB_DIRECTORY=../web
SERVER_DIRECTORY=../server
#PY_DIRECTORY=../../WPy64-3940/python-3.9.4.amd64/
#BSDIFF=bsdiff4-1.2.1-cp39-cp39-win_amd64.whl

#PY_DIRECTORY=../../WPy64-31020/python-3.10.2.amd64/
#BSDIFF=bsdiff4-1.2.1-cp310-cp310-win_amd64.whl
#PYyaml=PyYAML-5.4.1-cp310-cp310-win_amd64.whl

#PY_DIRECTORY=../../WPy64-38100/python-3.8.10.amd64/
#BSDIFF=bsdiff4-1.2.1-cp38-cp38-win_amd64.whl


#PY_DIRECTORY=../../WPy64-310111/python-3.10.11.amd64/

#PY_DIRECTORY=../../python-3.13.3/
PY_WIN_DIR := $(subst \\,/,$(PY_DIRECTORY))
BSDIFF=bsdiff4-1.2.1-cp310-cp310-win_amd64.whl
# to change in windows/setup.nsi

FILES_DIRECTORY=files

# https://www.enterprisedb.com/download-postgresql-binaries
#PG_VER=14.16-1
PG_ZIP=postgresql-$(PG_VER)-windows-x64-binaries.zip

# vebose mode: /V4
MAKENSIS_ARGUMENTS=/DMAJOR_VERSION=$(MAJOR_VERSION) /DMINOR_VERSION=$(MINOR_VERSION) /DPY_DIR=$(PY_WIN_DIR) /DREVISION_VERSION=$(REVISION_VERSION) /DBUILD_VERSION=$(BUILD_VERSION) /DPG_VER=$(PG_VER) /X"SetCompressor /SOLID lzma"
#MAKENSIS_ARGUMENTS=/DMAJOR_VERSION=$(MAJOR_VERSION) /DMINOR_VERSION=$(MINOR_VERSION) /DREVISION_VERSION=$(REVISION_VERSION) /DBUILD_VERSION=$(BUILD_VERSION) /DPG_VER=$(PG_VER) /X"SetCompressor /SOLID zlib"

LAUNCH_MAKENSIS=$(HOME)/nsis-3.06.1/makensis.exe $(MAKENSIS_ARGUMENTS) setup.nsi

default: allinone

server:
	$(PY_DIRECTORY)python.exe -m pip install -U pip
	$(PY_DIRECTORY)python.exe -m pip install wheel
	$(PY_DIRECTORY)python.exe -m pip install $(BSDIFF)
	#$(PY_DIRECTORY)python.exe -m pip install $(PYyaml)
#	$(PY_DIRECTORY)python.exe -m pip install cffi-1.14.5-cp310-cp310-win_amd64.whl
	$(PY_DIRECTORY)python.exe -m pip install -r $(SERVER_DIRECTORY)/requirements.txt

web:
	$(PY_DIRECTORY)python.exe -m pip install $(BSDIFF)
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

