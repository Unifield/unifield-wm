include Makefile.version

WEB_CLIENT_DIRECTORY=../web
SERVER_DIRECTORY=../server
FILES_DIRECTORY=files

LAUNCH_PY2EXE=python -B setup.py py2exe

MAKENSIS_ARGUMENTS=/DMAJOR_VERSION=$(MAJOR_VERSION) /DMINOR_VERSION=$(MINOR_VERSION) /DREVISION_VERSION=$(REVISION_VERSION) /DBUILD_VERSION=$(BUILD_VERSION)

LAUNCH_MAKENSIS=$(HOME)/nsis-3.01/makensis.exe $(MAKENSIS_ARGUMENTS) setup.nsi

default: allinone

clean: server_clean web_clean
	rm -rf $(FILES_DIRECTORY)/*.exe
	rm -rf *.exe

server_clean:
	rm -rf $(SERVER_DIRECTORY)/dist 
	rm -rf $(SERVER_DIRECTORY)/build
	rm -rf $(SERVER_DIRECTORY)/win32/dist 
	rm -rf $(SERVER_DIRECTORY)/win32/build
	rm -rf $(SERVER_DIRECTORY)/*.exe
	rm -rf $(SERVER_DIRECTORY)/.cyg*

server: server_clean
	(cd $(SERVER_DIRECTORY)/win32 && $(LAUNCH_PY2EXE))
	(cd $(SERVER_DIRECTORY) && $(LAUNCH_PY2EXE))
	(cd $(SERVER_DIRECTORY) && $(LAUNCH_MAKENSIS))
	cp $(SERVER_DIRECTORY)/openerp-*.exe $(FILES_DIRECTORY)/openerp-server-setup-$(MAJOR_VERSION).$(MINOR_VERSION)-$(BUILD_VERSION)-r$(REVISION_VERSION).exe

web_clean:
	rm -rf $(WEB_CLIENT_DIRECTORY)/dist 
	rm -rf $(WEB_CLIENT_DIRECTORY)/build
	rm -rf $(WEB_CLIENT_DIRECTORY)/win32/dist 
	rm -rf $(WEB_CLIENT_DIRECTORY)/win32/build
	rm -rf $(WEB_CLIENT_DIRECTORY)/*.exe
	rm -rf $(WEB_CLIENT_DIRECTORY)/.cyg*

web: web_clean
	(cd $(WEB_CLIENT_DIRECTORY)/win32 && $(LAUNCH_PY2EXE))
	(cd $(WEB_CLIENT_DIRECTORY) && $(LAUNCH_PY2EXE))
	(cd $(WEB_CLIENT_DIRECTORY) && $(LAUNCH_MAKENSIS))
	cp $(WEB_CLIENT_DIRECTORY)/openerp-*.exe $(FILES_DIRECTORY)/openerp-web-setup-$(MAJOR_VERSION).$(MINOR_VERSION)-$(BUILD_VERSION)-r$(REVISION_VERSION).exe

standalone:	server web

PG_VER=9.6.3-2
# Only update this on major versions, i.e. 9.x.y -> 10.x
PG_DIR=pgsql-9
PG_ZIP=postgresql-$(PG_VER)-windows-binaries.zip

$(PG_ZIP):
	wget https://get.enterprisedb.com/postgresql/$(PG_ZIP)

# Extract the minimal Postgres install from the distribution zip file
$(PG_DIR): $(PG_ZIP)
	unzip $(PG_ZIP) pgsql/bin/ pgsql/lib/ pgsql/share/ -d $(PG_DIR)
	mv $(PG_DIR)/pgsql/* $(PG_DIR)
	rmdir $(PG_DIR)/pgsql

allinone: standalone $(PG_DIR)
	$(LAUNCH_MAKENSIS)
	cp ./openerp-*.exe $(FILES_DIRECTORY)/openerp-allinone-setup-$(MAJOR_VERSION).$(MINOR_VERSION)-$(BUILD_VERSION)-r$(REVISION_VERSION).exe
	cp ./static/server-extra/PKGINFO $(FILES_DIRECTORY)/openerp-allinone-setup-$(MAJOR_VERSION).$(MINOR_VERSION)-$(BUILD_VERSION)-r$(REVISION_VERSION).txt

