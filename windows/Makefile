include Makefile.version

WEB_CLIENT_DIRECTORY=../web
GTK_CLIENT_DIRECTORY=../client
SERVER_DIRECTORY=../server
FILES_DIRECTORY=files

LAUNCH_PY2EXE=/cygdrive/c/Python26/python.exe setup.py py2exe

#MAKENSIS_ARGUMENTS=/DMAJOR_VERSION=$(MAJOR_VERSION) /DMINOR_VERSION=$(MINOR_VERSION) /DREVISION_VERSION=$(REVISION_VERSION) 

MAKENSIS_ARGUMENTS=/DMAJOR_VERSION=$(MAJOR_VERSION) /DMINOR_VERSION=$(MINOR_VERSION) /DREVISION_VERSION=$(REVISION_VERSION) /DBUILD_VERSION=$(BUILD_VERSION)

LAUNCH_MAKENSIS=makensis $(MAKENSIS_ARGUMENTS) setup.nsi

default: allinone

clean: client_clean server_clean web_clean
	rm -rf $(FILES_DIRECTORY)/*.exe
	rm -rf *.exe

client_clean:
	rm -rf $(GTK_CLIENT_DIRECTORY)/dist 
	rm -rf $(GTK_CLIENT_DIRECTORY)/build
	rm -rf $(GTK_CLIENT_DIRECTORY)/*.exe
	rm -rf $(GTK_CLIENT_DIRECTORY)/.cyg*
	rm -rf $(GTK_CLIENT_DIRECTORY)/openerp-client

client: client_clean
	(cd $(GTK_CLIENT_DIRECTORY) && $(LAUNCH_PY2EXE))
	(cd $(GTK_CLIENT_DIRECTORY) && $(LAUNCH_MAKENSIS))
	cp $(GTK_CLIENT_DIRECTORY)/openerp-*.exe $(FILES_DIRECTORY)/openerp-client-setup-$(MAJOR_VERSION).$(MINOR_VERSION)-$(BUILD_VERSION)-r$(REVISION_VERSION).exe

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

web:	web_clean
	(cd $(WEB_CLIENT_DIRECTORY)/win32 && $(LAUNCH_PY2EXE))
	(cd $(WEB_CLIENT_DIRECTORY) && $(LAUNCH_PY2EXE))
	(cd $(WEB_CLIENT_DIRECTORY) && $(LAUNCH_MAKENSIS))
	cp $(WEB_CLIENT_DIRECTORY)/openerp-*.exe $(FILES_DIRECTORY)/openerp-web-setup-$(MAJOR_VERSION).$(MINOR_VERSION)-$(BUILD_VERSION)-r$(REVISION_VERSION).exe

standalone:	client server web

allinone:	standalone
	$(LAUNCH_MAKENSIS)
	cp ./openerp-*.exe $(FILES_DIRECTORY)/openerp-allinone-setup-$(MAJOR_VERSION).$(MINOR_VERSION)-$(BUILD_VERSION)-r$(REVISION_VERSION).exe

