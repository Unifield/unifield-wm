#####################################################################################
#
# Copyright (c) 2004-TODAY OpenERP S.A. (http://www.openerp.com) All Rights Reserved.
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 3
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#####################################################################################

# TODO: Avoid to uninstall the database
# TODO: We can update the server or the clients without to uninstall the all-in-one

!include 'MUI2.nsh'
!include 'FileFunc.nsh'
!include 'LogicLib.nsh'
!include 'Sections.nsh'
!include 'LogicLib.nsh'
!include 'contrib.nsh'

!macro IfKeyExists ROOT MAIN_KEY KEY
    # This macro comes from http://nsis.sourceforge.net/Check_for_a_Registry_Key
    Push $R0
    Push $R1
    Push $R2

    # XXX bug if ${ROOT}, ${MAIN_KEY} or ${KEY} use $R0 or $R1

    StrCpy $R1 "0" # loop index
    StrCpy $R2 "0" # not found

    ${Do}
        EnumRegKey $R0 ${ROOT} "${MAIN_KEY}" "$R1"
        ${If} $R0 == "${KEY}"
            StrCpy $R2 "1" # found
            ${Break}
        ${EndIf}
        IntOp $R1 $R1 + 1
    ${LoopWhile} $R0 != ""

    ClearErrors

    Exch 2
    Pop $R0
    Pop $R1
    Exch $R2
!macroend

!define PUBLISHER 'OpenERP S.A.'

!ifndef MAJOR_VERSION
    !define MAJOR_VERSION '6'
!endif

!ifndef MINOR_VERSION
    !define MINOR_VERSION '0'
!endif

!ifndef REVISION_VERSION
    !define REVISION_VERSION '0'
!endif
!ifndef BUILD_VERSION
    !define VERSION "${MAJOR_VERSION}.${MINOR_VERSION}-r${REVISION_VERSION}"
!else
    !define VERSION "${MAJOR_VERSION}.${MINOR_VERSION}-${BUILD_VERSION}-r${REVISION_VERSION}"
!endif
!define PRODUCT_NAME "OpenERP"
!define DISPLAY_NAME "${PRODUCT_NAME} ${MAJOR_VERSION}.${MINOR_VERSION}"

!define REGISTRY_ROOT HKLM
!define UNINSTALL_BASE_REGISTRY_KEY "Software\Microsoft\Windows\CurrentVersion\Uninstall"
!define UNINSTALL_REGISTRY_KEY "${UNINSTALL_BASE_REGISTRY_KEY}\${DISPLAY_NAME}"

!define UNINSTALL_REGISTRY_KEY_SERVER "${UNINSTALL_BASE_REGISTRY_KEY}\OpenERP Server ${MAJOR_VERSION}.${MINOR_VERSION}"
!define UNINSTALL_REGISTRY_KEY_WEB_CLIENT "${UNINSTALL_BASE_REGISTRY_KEY}\OpenERP Web Client ${MAJOR_VERSION}.${MINOR_VERSION}"

!define REGISTRY_KEY "Software\${DISPLAY_NAME}"

!define DEFAULT_POSTGRESQL_INSTPATH 'D:\MSF data\Unifield\PostgreSQL'
!define DEFAULT_POSTGRESQL_HOSTNAME 'localhost'
!define DEFAULT_POSTGRESQL_PORT 5432
!define DEFAULT_POSTGRESQL_USERNAME 'openpg'
!define DEFAULT_POSTGRESQL_PASSWORD 'openpgpwd'

!define PGVERSION '8.4.16-1'

!define DEFAULT_OPENERP_DROP_PWD 'admin'
!define DEFAULT_OPENERP_BKP_PWD 'admin'
!define DEFAULT_OPENERP_RESTORE_PWD 'admin'

Name '${DISPLAY_NAME}'
Caption "${PRODUCT_NAME} ${VERSION} Setup"
OutFile "openerp-allinone-setup-${VERSION}.exe"
#SetCompressor /final /solid lzma
#SetCompress auto
ShowInstDetails show

XPStyle on

InstallDir "$PROGRAMFILES\msf\Unifield"
InstallDirRegKey HKCU "${REGISTRY_KEY}" ""

BrandingText '${PRODUCT_NAME} ${VERSION}'

RequestExecutionLevel admin

#VIAddVersionKey "ProductName" "${PRODUCT_NAME}"
#VIAddVersionKey "CompanyName" "${PUBLISHER}"
#VIAddVersionKey "FileDescription" "Installer of ${DISPLAY_NAME}"
#VIAddVersionKey "LegalCopyright" "${PUBLISHER}"
#VIAddVersionKey "LegalTrademark" "OpenERP is a trademark of ${PUBLISHER}"
#VIAddVersionKey "FileVersion" "${MAJOR_VERSION}.${MINOR_VERSION}.${REVISION_VERSION}"
#VIProductVersion "${MAJOR_VERSION}.${MINOR_VERSION}.${REVISION_VERSION}"

!insertmacro GetParameters
!insertmacro GetOptions

Var Option_AllInOne
Var HasPostgreSQL
Var cmdLineParams

Var CmdLPostgreSQLInstPath
Var TextPostgreSQLInstPath
Var TextPostgreSQLHostname
Var TextPostgreSQLPort
Var TextPostgreSQLUsername
Var TextPostgreSQLPassword

Var TextOPENERPDROPPWD
Var TextOPENERPBKPPWD
Var TextOPENERPRESTOREPWD

Var HWNDPostgreSQLInstancesList
Var HWNDPostgreSQLInstPath
Var HWNDPostgreSQLInstPath_Btn
Var HWNDPostgreSQLTestConn_Btn

Var HWNDPostgreSQLHostname
Var HWNDPostgreSQLPort
Var HWNDPostgreSQLUsername
Var HWNDPostgreSQLPassword

Var HWNDOpenERPDropPwd
Var HWNDOpenERPBkpPwd
Var HWNDOpenERPRestorePwd

!define STATIC_PATH "static"
!define PIXMAPS_PATH "${STATIC_PATH}\pixmaps"
!define POSTGRESQL_EXE "${STATIC_PATH}\postgresql-${PGVERSION}-windows.exe"

!define OPENERP_SERVER_SETUP 'openerp-server-setup-${VERSION}.exe'
!define OPENERP_WEB_SETUP 'openerp-web-setup-${VERSION}.exe'

!define OPENERP_SERVER_EXTRA "${STATIC_PATH}\server-extra"

!define MUI_ABORTWARNING
!define MUI_ICON "${PIXMAPS_PATH}\openerp-icon.ico"

!define MUI_WELCOMEFINISHPAGE_BITMAP "${PIXMAPS_PATH}\openerp-intro.bmp"
!define MUI_UNWELCOMEFINISHPAGE_BITMAP "${PIXMAPS_PATH}\openerp-intro.bmp"
!define MUI_HEADERIMAGE
!define MUI_HEADERIMAGE_BITMAP "${PIXMAPS_PATH}\openerp-slogan.bmp"
!define MUI_HEADERIMAGE_BITMAP_NOSTRETCH
!define MUI_HEADER_TRANSPARENT_TEXT ""

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "${STATIC_PATH}\doc\LICENSE"
!define MUI_COMPONENTSPAGE_SMALLDESC
!define MUI_PAGE_CUSTOMFUNCTION_LEAVE ComponentLeave
!insertmacro MUI_PAGE_COMPONENTS
!insertmacro MUI_PAGE_DIRECTORY
Page Custom DBPasswordPage LeaveDBPasswordPage
Page Custom ShowPostgreSQL LeavePostgreSQL
!insertmacro MUI_PAGE_INSTFILES

!define MUI_FINISHPAGE_NOAUTOCLOSE
!define MUI_FINISHPAGE_RUN
!define MUI_FINISHPAGE_RUN_CHECKED
!define MUI_FINISHPAGE_RUN_TEXT "$(DESC_FinishPageText)"
!define MUI_FINISHPAGE_RUN_FUNCTION "LaunchLink"
!define MUI_FINISHPAGE_LINK $(DESC_FinishPage_Link)
!define MUI_FINISHPAGE_LINK_LOCATION "http://www.openerp.com/contact"
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_WELCOME
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_UNPAGE_FINISH

!insertmacro MUI_LANGUAGE "English"
!insertmacro MUI_LANGUAGE "French"
!insertmacro MUI_RESERVEFILE_LANGDLL

; English
LangString MSG_ConnectionOK ${LANG_ENGLISH} "Connection successful!"
LangString MSG_ConnectionFAILED ${LANG_ENGLISH} "Connection failed!"
LangString DESC_TestConnection ${LANG_ENGLISH} "Test connection"
LangString DESC_OpenERP_Server ${LANG_ENGLISH} "Install the OpenERP Server with all the OpenERP standard modules."
LangString DESC_OpenERP_Web_Client ${LANG_ENGLISH} "Install the OpenERP Web Client if you want to access the OpenERP Server with your internet browser."
LangString DESC_PostgreSQL ${LANG_ENGLISH} "Install the PostgreSQL RDBMS used by OpenERP."
LangString DESC_FinishPage_Link ${LANG_ENGLISH} "Contact OpenERP for Partnership and/or Support"
LangString DESC_AtLeastOneComponent ${LANG_ENGLISH} "You have to choose at least one component"
LangString DESC_CanNotInstallPostgreSQL ${LANG_ENGLISH} "You can not install the PostgreSQL database without the OpenERP Server"
LangString WARNING_InstallUnderServerDirectory ${LANG_ENGLISH} "You can not install PostgreSQL under same directory as OpenERP server"
LangString WARNING_InstallPathEmpty ${LANG_ENGLISH} "The installation path for PostgreSQL Server is empty"
LangString WARNING_HostNameIsEmpty ${LANG_ENGLISH} "The hostname for the connection to the PostgreSQL Server is empty"
LangString WARNING_UserNameIsEmpty ${LANG_ENGLISH} "The username for the connection to the PostgreSQL Server is empty"
LangString WARNING_PasswordIsEmpty ${LANG_ENGLISH} "The password for the connection to the PostgreSQL Server is empty"
LangString WARNING_PortIsWrong ${LANG_ENGLISH} "The port for the connexion to the PostgreSQL Server is wrong (default: 5432)"
LangString DESC_PostgreSQLNewInstall ${LANG_ENGLISH} "New installation"
LangString DESC_PostgreSQLPage ${LANG_ENGLISH} "Configure the information for the PostgreSQL connection"
LangString DESC_PostgreSQL_Hostname ${LANG_ENGLISH} "Hostname"
LangString DESC_PostgreSQL_Port ${LANG_ENGLISH} "Port"
LangString DESC_PostgreSQL_Username ${LANG_ENGLISH} "Username"
LangString DESC_PostgreSQL_Password ${LANG_ENGLISH} "Password"
LangString DESC_PostgreSQL_InstPath ${LANG_ENGLISH} "Installation path"
LangString Profile_AllInOne ${LANG_ENGLISH} "All In One"
LangString Profile_Server ${LANG_ENGLISH} "Server only"
LangString Profile_Web_Client ${LANG_ENGLISH} "Web environment"
LangString TITLE_OpenERP_Server ${LANG_ENGLISH} "OpenERP Server"
LangString TITLE_OpenERP_Web_Client ${LANG_ENGLISH} "OpenERP Web Client"
LangString TITLE_PostgreSQL ${LANG_ENGLISH} "PostgreSQL Database"
LangString DESC_FinishPageText ${LANG_ENGLISH} "Connect to OpenERP Web"
LangString DESC_OPENERPPage ${LANG_ENGLISH} "Configure the passwords for DB drop,backup and create from openerp"
LangString DESC_OPENERP_DROP_PWD ${LANG_ENGLISH} "Password to drop DB"
LangString DESC_OPENERP_BKP_PWD ${LANG_ENGLISH} "Password to backup DB"
LangString DESC_OPENERP_RESTORE_PWD ${LANG_ENGLISH} "Password to restore DB"
LangString WARNING_OPENERP_DROP_PasswordIsEmpty ${LANG_ENGLISH} "Password to drop DB is emptyy"
LangString WARNING_OPENERP_BKP_PasswordIsEmpty ${LANG_ENGLISH} "Password to backup DB is emptyy"
LangString WARNING_OPENERP_RESTORE_PasswordIsEmpty ${LANG_ENGLISH} "Password to restore DB is emptyy"

; French
LangString MSG_ConnectionOK ${LANG_FRENCH} "Connection réussie!"
LangString MSG_ConnectionFAILED ${LANG_FRENCH} "Échec de la connection!"
LangString DESC_TestConnection ${LANG_FRENCH} "Tester la connection"
LangString DESC_OpenERP_Server ${LANG_FRENCH} "Installation du Serveur OpenERP avec tous les modules OpenERP standards."
LangString DESC_OpenERP_Web_Client ${LANG_FRENCH} "Installation du Client OpenERP Web si vous d?siez acc?der ? OpenERP avec votre navigateur web"
LangString DESC_PostgreSQL ${LANG_FRENCH} "Installation de la base de donn?es PostgreSQL utilis?e par OpenERP."
LangString DESC_FinishPage_Link ${LANG_FRENCH} "Contactez OpenERP pour un Partenariat et/ou du Support"
LangString DESC_AtLeastOneComponent ${LANG_FRENCH} "Vous devez choisir au moins un composant"
LangString DESC_CanNotInstallPostgreSQL ${LANG_FRENCH} "Vous ne pouvez pas installer la base de données PostgreSQL sans le serveur OpenERP"
LangString WARNING_InstallUnderServerDirectory ${LANG_FRENCH} "Vous ne pouvez pas installer la base de données PostgreSQL sous le même répertoire que le serveur OpenERP"
LangString WARNING_InstallPathEmpty ${LANG_FRENCH} "Le chemin d'installation du serveur PostgreSQL est vide"
LangString WARNING_HostNameIsEmpty ${LANG_FRENCH} "L'adresse pour la connection au serveur PostgreSQL est vide"
LangString WARNING_UserNameIsEmpty ${LANG_FRENCH} "Le nom d'utilisateur pour la connection au serveur PostgreSQL est vide"
LangString WARNING_PasswordIsEmpty ${LANG_FRENCH} "Le mot de passe pour la connection au serveur PostgreSQL est vide"
LangString WARNING_PortIsWrong ${LANG_FRENCH} "Le port pour la connection au serveur PostgreSQL est erron? (d?faut: 5432)"
LangString DESC_PostgreSQLNewInstall ${LANG_FRENCH} "Nouvelle installation"
LangString DESC_PostgreSQLPage ${LANG_FRENCH} "Configurez les informations de connection pour le serveur PostgreSQL"
LangString DESC_PostgreSQL_Hostname ${LANG_FRENCH} "H?te"
LangString DESC_PostgreSQL_Port ${LANG_FRENCH} "Port"
LangString DESC_PostgreSQL_Username ${LANG_FRENCH} "Utilisateur"
LangString DESC_PostgreSQL_Password ${LANG_FRENCH} "Mot de passe"
LangString DESC_PostgreSQL_InstPath ${LANG_FRENCH} "Chemin d'install"
LangString Profile_AllInOne ${LANG_FRENCH} "All In One"
LangString Profile_Server ${LANG_FRENCH} "Seulement le serveur"
LangString Profile_Web_Client ${LANG_FRENCH} "Environement Web"
LangString TITLE_OpenERP_Server ${LANG_FRENCH} "Serveur OpenERP"
LangString TITLE_OpenERP_Web_Client ${LANG_FRENCH} "OpenERP Client Web"
LangString TITLE_PostgreSQL ${LANG_FRENCH} "Installation du serveur de base de donn?es PostgreSQL"
LangString DESC_FinishPageText ${LANG_FRENCH} "Se connecter à OpenERP Web"
LangString DESC_OPENERPPage ${LANG_FRENCH} "Definissez les mots de passe pour la manipulation des bdd depuis OpenERP"
LangString DESC_OPENERP_DROP_PWD ${LANG_FRENCH} "MdP pour supprimer une bdd"
LangString DESC_OPENERP_BKP_PWD ${LANG_FRENCH} "MdP pour sauvegarder une bdd"
LangString DESC_OPENERP_RESTORE_PWD ${LANG_FRENCH} "MdP pour restaurer une bdd"
LangString WARNING_OPENERP_DROP_PasswordIsEmpty ${LANG_FRENCH} "MdP pour supprimer une bdd est vide"
LangString WARNING_OPENERP_BKP_PasswordIsEmpty ${LANG_FRENCH} "MdP pour sauvegarder une bdd est vide"
LangString WARNING_OPENERP_RESTORE_PasswordIsEmpty ${LANG_FRENCH} "MdP pour restaurer une bdd est vide"

InstType $(Profile_AllInOne)
InstType $(Profile_Server)
InstType $(Profile_Web_Client)

Section $(TITLE_OpenERP_Server) SectionOpenERP_Server
    SectionIn 1 2
    SetOutPath "$TEMP"
    File "files\${OPENERP_SERVER_SETUP}"
    ExecWait '"$TEMP\${OPENERP_SERVER_SETUP}" /S /D=$INSTDIR\Server'

    Push $R0
    ${Base64_Encode} "$TextPostgreSQLPassword"
    Pop $R0
# If there is a previous install of the OpenERP Server, keep the login/password from the config file
    WriteIniStr "$INSTDIR\Server\openerp-server.conf" "options" "db_host" $TextPostgreSQLHostname
    WriteIniStr "$INSTDIR\Server\openerp-server.conf" "options" "db_user" $TextPostgreSQLUsername
    WriteIniStr "$INSTDIR\Server\openerp-server.conf" "options" "db_password" $R0
    WriteIniStr "$INSTDIR\Server\openerp-server.conf" "options" "db_port" $TextPostgreSQLPort
    WriteIniStr "$INSTDIR\Server\openerp-server.conf" "options" "db_maxconn" 95
    # Always override pg_path by the correct instance choosen by the user (newly installed or not...)
    WriteIniStr "$INSTDIR\Server\openerp-server.conf" "options" "pg_path" "$TextPostgreSQLInstPath\bin"

    Push $R1
    ${Base64_Encode} "$TextOPENERPDROPPWD"
    Pop $R1
    WriteIniStr "$INSTDIR\Server\openerp-server.conf" "options" "admin_dropdb_passwd" $R1
    Push $R2
    ${Base64_Encode} "$TextOPENERPBKPPWD"
    Pop $R2
    WriteIniStr "$INSTDIR\Server\openerp-server.conf" "options" "admin_bkpdb_passwd" $R2
    Push $R3
    ${Base64_Encode} "$TextOPENERPRESTOREPWD"
    Pop $R3
    WriteIniStr "$INSTDIR\Server\openerp-server.conf" "options" "admin_restoredb_passwd" $R3

    File /r "static\server-extra"
    CopyFiles "$TEMP\server-extra\*.*" "$INSTDIR\Server"

    nsExec::Exec "net stop openerp-server-6.0"
    sleep 2

    nsExec::Exec "net start openerp-server-6.0"
    sleep 2

SectionEnd

Section $(TITLE_OpenERP_Web_Client) SectionOpenERP_Web_Client
    SectionIn 1 4
    SetOutPath "$TEMP"
    File "files\${OPENERP_WEB_SETUP}"
    ExecWait '"$TEMP\${OPENERP_WEB_SETUP}" /S /D=$INSTDIR\Web'
SectionEnd

Section $(TITLE_PostgreSQL) SectionPostgreSQL
    SectionIn 1 2
    SetOutPath '$TEMP'
    nsExec::Exec 'net user openpgsvc /delete'

    File "postgresql-${PGVERSION}-windows.exe"

    ReadRegStr $0 HKLM "System\CurrentControlSet\Control\ComputerName\ActiveComputerName" "ComputerName"
    StrCmp $0 "" win9x
    Goto done
    win9x:
        ReadRegStr $0 HKLM "System\CurrentControlSet\Control\ComputerName\ComputerName" "ComputerName"
    done:
	Rmdir /r "$TextPostgreSQLInstPath"
	ExecWait '"$TEMP\postgresql-${PGVERSION}-windows.exe" \
		--mode unattended \
		--prefix "$TextPostgreSQLInstPath" \
		--datadir "$TextPostgreSQLInstPath\data" \
		--servicename "PostgreSQL_For_OpenERP" \
		--serviceaccount "openpgsvc" --servicepassword "0p3npgsvcPWD" \
		--superaccount "$TextPostgreSQLUsername" --superpassword "$TextPostgreSQLPassword" \
		--serverport $TextPostgreSQLPort'

	Push $R0
	FileOpen $R0 "$TextPostgreSQLInstPath\data\postgresql.conf" a
	FileSeek $R0 0 "END"
	# Start of custom PostgreSQL options
	FileWrite $R0 "listen_addresses = 'localhost'"
	# add \r\n
	FileWriteByte $R0 "13"
	FileWriteByte $R0 "10"
	FileClose $R0
	FileClose $R0
	Pop $R0

	nsExec::Exec 'net stop PostgreSQL_For_OpenERP'
	nsExec::Exec 'net start PostgreSQL_For_OpenERP'
#    ExecWait 'msiexec /i \
#        "$TEMP\postgresql-8.4.9-1-windows.exe" /qn INTERNALLAUNCH=1 \
#        ADDLOCAL=server,pgadmin \
#        SERVICEDOMAIN="$0" SERVICEACCOUNT="openpgsvc" SERVICEPASSWORD="0p3npgsvcPWD" CREATESERVICEUSER=1 SERVICENAME="PostgreSQL For OpenERP" \
#        SUPERUSER="$TextPostgreSQLUsername" \
#        SUPERPASSWORD="$TextPostgreSQLPassword" DOINITDB=1 DOSERVICE=1 \
#        LISTENPORT=$TextPostgreSQLPort ENCODING=UTF-8 BASEDIR="$INSTDIR\PostgreSQL"'
SectionEnd

Section -Post
    WriteRegExpandStr HKLM "${UNINSTALL_REGISTRY_KEY}" "UninstallString" "$INSTDIR\Uninstall.exe"
    WriteRegExpandStr HKLM "${UNINSTALL_REGISTRY_KEY}" "InstallLocation" "$INSTDIR"
    WriteRegStr HKLM       "${UNINSTALL_REGISTRY_KEY}" "DisplayName" "${DISPLAY_NAME}"
    WriteRegStr HKLM       "${UNINSTALL_REGISTRY_KEY}" "DisplayVersion" "${MAJOR_VERSION}.${MINOR_VERSION}"
    WriteRegStr HKLM       "${UNINSTALL_REGISTRY_KEY}" "Publisher" "${PUBLISHER}"
    WriteRegDWORD HKLM     "${UNINSTALL_REGISTRY_KEY}" "Version" "${VERSION}"
    WriteRegDWORD HKLM     "${UNINSTALL_REGISTRY_KEY}" "VersionMajor" "${MAJOR_VERSION}.${MINOR_VERSION}"
    WriteRegDWORD HKLM     "${UNINSTALL_REGISTRY_KEY}" "VersionMinor" "${REVISION_VERSION}"
    WriteRegStr HKLM       "${UNINSTALL_REGISTRY_KEY}" "HelpLink" "support@openerp.com"
    WriteRegStr HKLM       "${UNINSTALL_REGISTRY_KEY}" "HelpTelephone" "+32.81.81.37.00"
    WriteRegStr HKLM       "${UNINSTALL_REGISTRY_KEY}" "URLInfoAbout" "http://www.openerp.com"
    WriteRegStr HKLM       "${UNINSTALL_REGISTRY_KEY}" "Contact" "sales@openerp.com"
    WriteRegDWORD HKLM     "${UNINSTALL_REGISTRY_KEY}" "NoModify" "1"
    WriteRegDWORD HKLM     "${UNINSTALL_REGISTRY_KEY}" "NoRepair" "1"
    WriteUninstaller "$INSTDIR\Uninstall.exe"
SectionEnd

!insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
    !insertmacro MUI_DESCRIPTION_TEXT ${SectionOpenERP_Server} $(DESC_OpenERP_Server)
    !insertmacro MUI_DESCRIPTION_TEXT ${SectionOpenERP_Web_Client} $(DESC_OpenERP_Web_Client)
    !insertmacro MUI_DESCRIPTION_TEXT ${SectionPostgreSQL} $(DESC_PostgreSQL)
!insertmacro MUI_FUNCTION_DESCRIPTION_END

Section "Uninstall"
    # Check if the server is installed
    !insertmacro IfKeyExists "HKLM" "${UNINSTALL_REGISTRY_KEY_SERVER}" "UninstallString"
    Pop $R0

    ReadRegStr $0 HKLM "${UNINSTALL_REGISTRY_KEY_SERVER}" "UninstallString"
    ExecWait '"$0" /S'

    !insertmacro IfKeyExists "HKLM" "${UNINSTALL_REGISTRY_KEY_WEB_CLIENT}" "UninstallString"
    Pop $R0

    ReadRegStr $0 HKLM "${UNINSTALL_REGISTRY_KEY_WEB_CLIENT}" "UninstallString"
    ExecWait '"$0" /S'

    #Rmdir /r "$INSTDIR"

    DeleteRegKey HKLM "${UNINSTALL_REGISTRY_KEY}"
SectionEnd

Function .onInit
    Push $R0

    ${GetParameters} $cmdLineParams
    ClearErrors

    Pop $R0

    StrCpy $Option_AllInOne 0
    StrCpy $HasPostgreSQL 0

    StrCpy $TextPostgreSQLHostname ${DEFAULT_POSTGRESQL_HOSTNAME}
    StrCpy $TextPostgreSQLPort ${DEFAULT_POSTGRESQL_PORT}
    StrCpy $TextPostgreSQLUsername ${DEFAULT_POSTGRESQL_USERNAME}
    StrCpy $TextPostgreSQLPassword ${DEFAULT_POSTGRESQL_PASSWORD}
    StrCpy $TextPostgreSQLInstPath "${DEFAULT_POSTGRESQL_INSTPATH}"
    StrCpy $CmdLPostgreSQLInstPath "${DEFAULT_POSTGRESQL_INSTPATH}"

    StrCpy $TextOPENERPDROPPWD ${DEFAULT_OPENERP_DROP_PWD}
    StrCpy $TextOPENERPBKPPWD ${DEFAULT_OPENERP_BKP_PWD}
    StrCpy $TextOPENERPRESTOREPWD ${DEFAULT_OPENERP_RESTORE_PWD}

    Push $R0
    ${GetOptions} $cmdLineParams '/allinone' $R0
    IfErrors +2 0
    StrCpy $Option_AllInOne 1
    Pop $R0

    StrCmp $Option_AllInOne 1 AllInOneMode
    StrCmp $Option_AllInOne 0 NoAllInOneMode

    AllInOneMode:
        MessageBox MB_OK|MB_ICONINFORMATION "All In One"

    NoAllInOneMode:

    !insertmacro MUI_LANGDLL_DISPLAY

    ; check for forced PostgreSQL install path on command line
    ; /PGINSTDIR="C:\PATH\TO\PostgreSQL"
    ClearErrors
    Push $R0
    ${GetOptions} $cmdLineParams '/PGINSTDIR=' $R0
    IfErrors +3 0
    StrCpy $TextPostgreSQLInstPath $R0
    StrCpy $CmdLPostgreSQLInstPath $R0
    Pop $R0

    ClearErrors
    EnumRegKey $0 HKLM "SOFTWARE\PostgreSQL\Installations" 0
    IfErrors DoInstallPostgreSQL 0
		StrCmp $0 "" DoInstallPostgreSQL # Empty value means no subkey, i.e PostgreSQL not installed
        StrCpy $HasPostgreSQL 1
        #SectionSetText ${SectionPostgreSQL} ""
        !insertmacro UnselectSection ${SectionPostgreSQL}
        SectionSetFlags ${SectionPostgreSQL} ${SF_RO}

    DoInstallPostgreSQL:
FunctionEnd

Function .onSelChange
    ${If} $HasPostgreSQL == 1
        !insertmacro UnselectSection ${SectionPostgreSQL}
    ${EndIf}
FunctionEnd

Function PostgreSQLOnBack
FunctionEnd

Function ShowPostgreSQL
    SectionGetFlags ${SectionOpenERP_Server} $0
    IntOp $0 $0 & ${SF_SELECTED}
    IntCmp $0 ${SF_SELECTED} LaunchPostgreSQLConfiguration
    Abort
    LaunchPostgreSQLConfiguration:

    nsDialogs::Create /NOUNLOAD 1018
    Pop $0

    ${If} $0 == error
        Abort
    ${EndIf}

    GetFunctionAddress $0 PostgreSQLOnBack
    nsDialogs::OnBack $0

    ${NSD_CreateLabel} 0 0 100% 10u $(DESC_PostgreSQLPage)
    Pop $0

    ${NSD_CreateDropList} 0 25 215u 12u ""
    Pop $HWNDPostgreSQLInstancesList
    SetCtlColors $HWNDPostgreSQLInstancesList 0x000000 0xFFFFFF
    ${NSD_OnChange} $HWNDPostgreSQLInstancesList OnPostgresInstanceChange

    ; setup and update default postgresql install path
    ${If} $CmdLPostgreSQLInstPath == ""
        StrCpy $TextPostgreSQLInstPath "$INSTDIR\PostgreSQL"
    ${Else}
        StrCpy $TextPostgreSQLInstPath "$CmdLPostgreSQLInstPath"
    ${EndIf}
    ${NSD_CreateLabel} 0 55 60u 12u $(DESC_PostgreSQL_InstPath)
    Pop $0
    ${NSD_CreateText} 100 55 140u 12u $TextPostgreSQLInstPath
    Pop $HWNDPostgreSQLInstPath
    ${NSD_CreateButton} 207u 55 10u 12u "..."
    Pop $HWNDPostgreSQLInstPath_Btn
    ${NSD_OnClick} $HWNDPostgreSQLInstPath_Btn func_PostgreSQL_InstPath_Choose_Click


    ${NSD_CreateLabel} 0 85 60u 12u $(DESC_PostgreSQL_Hostname)
    Pop $0
    ${NSD_CreateText} 100 85 150u 12u $TextPostgreSQLHostname
    Pop $HWNDPostgreSQLHostname

    ${NSD_CreateLabel} 0 115 60u 12u $(DESC_PostgreSQL_Port)
    Pop $0
    ${NSD_CreateNumber} 100 115 150u 12u $TextPostgreSQLPort
    Pop $HWNDPostgreSQLPort
    ${NSD_CreateLabel} 0 145 60u 12u $(DESC_PostgreSQL_Username)
    Pop $0
    ${NSD_CreateText} 100 145 150u 12u $TextPostgreSQLUsername
    Pop $HWNDPostgreSQLUsername
    ${NSD_CreateLabel} 0 175 60u 12u $(DESC_PostgreSQL_Password)
    Pop $0
    ${NSD_CreateText} 100 175 150u 12u $TextPostgreSQLPassword
    Pop $HWNDPostgreSQLPassword

    ${NSD_CreateButton} 0 205 100u 12u $(DESC_TestConnection)
    Pop $HWNDPostgreSQLTestConn_Btn
    ${NSD_OnClick} $HWNDPostgreSQLTestConn_Btn func_PostgreSQL_TestConn_Click

    ; === detect PostgreSQL installations ====
    ClearErrors
    StrCpy $5 ""; the default value for selection
    StrCpy $0 0
    pginst_loop:
        EnumRegKey $1 HKLM "SOFTWARE\PostgreSQL\Installations" $0
        StrCmp $1 "" pginst_done
        ReadRegStr $2 HKLM "SOFTWARE\PostgreSQL\Installations\$1" "Service ID"
        ReadRegStr $3 HKLM "SOFTWARE\PostgreSQL\Installations\$1" "Version"
        ${NSD_CB_AddString} $HWNDPostgreSQLInstancesList "$0: $2 ($3)"
        ${If} $5 == ""
            StrCpy $5 "$0: $2 ($3)"
        ${EndIf}
        IntOp $0 $0 + 1
        Goto pginst_loop
    pginst_done:
        ClearErrors

    ; select default value for instances droplist
    ${If} $0 == 0
        ${NSD_CB_AddString} $HWNDPostgreSQLInstancesList $(DESC_PostgreSQLNewInstall)
        ${NSD_CB_SelectString} $HWNDPostgreSQLInstancesList $(DESC_PostgreSQLNewInstall)
    ${Else}
        ${NSD_CB_SelectString} $HWNDPostgreSQLInstancesList $5
    ${EndIf}
    ; setup default view state
    EnableWindow $HWNDPostgreSQLInstPath 0
    EnableWindow $HWNDPostgreSQLInstPath_Btn 0
    ShowWindow $HWNDPostgreSQLTestConn_Btn 0

    ; call onchange with initial value
    Push $HWNDPostgreSQLInstancesList
    Call OnPostgresInstanceChange

    nsDialogs::Show
FunctionEnd

Function LeavePostgreSQL
    ${NSD_GetText} $HWNDPostgreSQLInstPath $TextPostgreSQLInstPath
    ${NSD_GetText} $HWNDPostgreSQLHostname $TextPostgreSQLHostname
    ${NSD_GetText} $HWNDPostgreSQLPort $TextPostgreSQLPort
    ${NSD_GetText} $HWNDPostgreSQLUsername $TextPostgreSQLUsername
    ${NSD_GetText} $HWNDPostgreSQLPassword $TextPostgreSQLPassword

    Push $1
    Push $2
    Strlen $1 $TextPostgreSQLInstPath
    ${If} $1 == 0
	MessageBox MB_ICONEXCLAMATION|MB_OK $(WARNING_InstallPathEmpty)
	Abort
    ${EndIf}
    StrCpy $2 "$INSTDIR" $1 # cut INSTDIR as choosen PG install path
    StrCmp $2 "$TextPostgreSQLInstPath" pginstpatherror
    StrCpy $2 "$INSTDIR\Server\" $1 # cust INSTDIR\Server as choosen PG install path
    StrCmp $2 "$TextPostgreSQLInstPath" pginstpatherror pginstpathok
    pginstpatherror:
	MessageBox MB_ICONEXCLAMATION|MB_OK $(WARNING_InstallUnderServerDirectory)
	Abort
    pginstpathok:

    StrLen $1 $TextPostgreSQLHostname
    ${If} $1 == 0
        MessageBox MB_ICONEXCLAMATION|MB_OK $(WARNING_HostNameIsEmpty)
        Abort
    ${EndIf}

    ${If} $TextPostgreSQLPort <= 0
    ${OrIf} $TextPostgreSQLPort > 65535
        MessageBox MB_ICONEXCLAMATION|MB_OK $(WARNING_PortIsWrong)
        Abort
    ${EndIf}

    StrLen $1 $TextPostgreSQLUsername
    ${If} $1 == 0
        MessageBox MB_ICONEXCLAMATION|MB_OK $(WARNING_UserNameIsEmpty)
        Abort
    ${EndIf}

    StrLen $1 $TextPostgreSQLPassword
    ${If} $1 == 0
        MessageBox MB_ICONEXCLAMATION|MB_OK $(WARNING_PasswordIsEmpty)
        Abort
    ${EndIf}
FunctionEnd


Function DBPasswordPage
  SectionGetFlags ${SectionOpenERP_Server} $0
  IntOp $0 $0 & ${SF_SELECTED}
  IntCmp $0 ${SF_SELECTED} LaunchDBPwdConfiguration
  Abort
  LaunchDBPwdConfiguration:

  nsDialogs::Create /NOUNLOAD 1018
  Pop $0

  ${If} $0 == error
      Abort
  ${EndIf}

  ${NSD_CreateLabel} 0 0 100% 10u $(DESC_OPENERPPage)
  Pop $0

  ${NSD_CreateLabel} 0 85 90u 12u $(DESC_OPENERP_DROP_PWD)
  Pop $0
  ${NSD_CreateText} 150 85 150u 12u $TextOPENERPDROPPWD
  Pop $HWNDOpenERPDropPwd
  ${NSD_CreateLabel} 0 115 80u 12u $(DESC_OPENERP_BKP_PWD)
  Pop $0
  ${NSD_CreateText} 150 115 150u 12u $TextOPENERPBKPPWD
  Pop $HWNDOpenERPBkpPwd
  ${NSD_CreateLabel} 0 145 80u 12u $(DESC_OPENERP_RESTORE_PWD)
  Pop $0
  ${NSD_CreateText} 150 145 150u 12u $TextOPENERPRESTOREPWD
  Pop $HWNDOpenERPRestorePwd

  nsDialogs::Show

FunctionEnd


Function LeaveDBPasswordPage
    ${NSD_GetText} $HWNDOpenERPDropPwd $TextOPENERPDROPPWD
    ${NSD_GetText} $HWNDOpenERPBkpPwd $TextOPENERPBKPPWD
    ${NSD_GetText} $HWNDOpenERPRestorePwd $TextOPENERPRESTOREPWD

    StrLen $1 $TextOPENERPDROPPWD
    ${If} $1 == 0
        MessageBox MB_ICONEXCLAMATION|MB_OK $(WARNING_OPENERP_DROP_PasswordIsEmpty)
        Abort
    ${EndIf}

    StrLen $1 $TextOPENERPBKPPWD
    ${If} $1 == 0
        MessageBox MB_ICONEXCLAMATION|MB_OK $(WARNING_OPENERP_BKP_PasswordIsEmpty)
        Abort
    ${EndIf}

    StrLen $1 $TextOPENERPRESTOREPWD
    ${If} $1 == 0
        MessageBox MB_ICONEXCLAMATION|MB_OK $(WARNING_OPENERP_RESTORE_PasswordIsEmpty)
        Abort
    ${EndIf}
FunctionEnd

Function func_PostgreSQL_TestConn_Click
    Pop $R0
    ${If} $R0 == $HWNDPostgreSQLTestConn_Btn
        ${NSD_GetText} $HWNDPostgreSQLInstPath $R1
        ${NSD_GetText} $HWNDPostgreSQLHostname $R2
        ${NSD_GetText} $HWNDPostgreSQLPort $R3
        ${NSD_GetText} $HWNDPostgreSQLUsername $R4
        ${NSD_GetText} $HWNDPostgreSQLPassword $R5
        StrCpy $R6 '"$R1\bin\psql.exe" -h "$R2" -p "$R3" -U "$R4" -d postgres -c ""'
        ; set connection password from testing
        System::Call 'Kernel32::SetEnvironmentVariableA(t, t) i("PGPASSWORD", R5).r2'
        ; run connection test command
        StrCpy $R8 ""
        ClearErrors
        ExecWait $R6 $R8
        ; check return code and display status (success / fail)
        StrCmp $R8 0 testok
        MessageBox MB_OK "$(MSG_ConnectionFAILED)"
        Goto testdone
        testok:
            MessageBox MB_OK "$(MSG_ConnectionOK)"
        testdone:
        ; clear connection password
        StrCpy $R5 ""
        System::Call 'Kernel32::SetEnvironmentVariableA(t, t) i("PGPASSWORD", R5).r2'
    ${EndIf}

FunctionEnd

Function func_PostgreSQL_InstPath_Choose_Click
    Pop $R0
    ${If} $R0 == $HWNDPostgreSQLInstPath_Btn
        ${NSD_GetText} $HWNDPostgreSQLInstPath $R0
        nsDialogs::SelectFolderDialog "$R0" ""
        Pop $R0
        ${If} "$R0" != "error"
            ${NSD_SetText} $HWNDPostgreSQLInstPath "$R0\PostgreSQL"
        ${EndIf}
    ${EndIf}
FunctionEnd

Function OnPostgresInstanceChange
    Pop $1
    ${NSD_GetText} $HWNDPostgreSQLInstancesList $0
    ${If} $0 == $(DESC_PostgreSQLNewInstall)
        ; allow choosing install path, but disable test connection
        ; (as postgresql are not install now ;-D)
        EnableWindow $HWNDPostgreSQLInstPath 1
        EnableWindow $HWNDPostgreSQLInstPath_Btn 1
        ShowWindow $HWNDPostgreSQLTestConn_Btn 0
    ${Else}
        ; disable choosing install path, but allow test connection
        ; (already installed postgres path come from win32 registry)
        EnableWindow $HWNDPostgreSQLInstPath 0
        EnableWindow $HWNDPostgreSQLInstPath_Btn 0
        ShowWindow $HWNDPostgreSQLTestConn_Btn 1

        ; extract instance number from droplist test (0: ... => 1st instance)
        StrCpy $R0 0; string index
        pginst_loop_index:
            StrCpy $R1 $0 1 $R0
            StrCmp $R1 ":" pginst_done_index
            IntOp $R0 $R0 + 1
            Goto pginst_loop_index
        pginst_done_index:
            StrCpy $2 $0 $R0 0
            EnumRegKey $3 HKLM "SOFTWARE\PostgreSQL\Installations" $2
            ReadRegStr $4 HKLM "SOFTWARE\PostgreSQL\Installations\$3" "Base Directory"
            ${NSD_SetText} $HWNDPostgreSQLInstPath $4
    ${EndIf}
FunctionEnd

Function ComponentLeave
    SectionGetFlags ${SectionOpenERP_Server} $0
    IntOp $0 $0 & ${SF_SELECTED}
    IntCmp $0 ${SF_SELECTED} Done

    SectionGetFlags ${SectionPostgreSQL} $0
    IntOp $0 $0 & ${SF_SELECTED}
    IntCmp $0 ${SF_SELECTED} DontInstallPostgreSQL

    SectionGetFlags ${SectionOpenERP_Web_Client} $0
    IntOp $0 $0 & ${SF_SELECTED}
    IntCmp $0 ${SF_SELECTED} Done

    ChooseAtLeastOneComponent:
        MessageBox MB_ICONEXCLAMATION|MB_OK $(DESC_AtLeastOneComponent)
        Abort

    DontInstallPostgreSQL:
        MessageBox MB_ICONEXCLAMATION|MB_OK $(DESC_CanNotInstallPostgreSQL)
        Abort
    Done:
FunctionEnd

Function LaunchLink
    ExecShell "open" "http://localhost:8061/"
FunctionEnd
