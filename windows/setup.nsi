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

!define PUBLISHER 'Unifield'

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
!define DEFAULT_POSTGRESQL_PASSWORD '4Unifieldpg'

!define DEFAULT_OPENERP_PASSWORD '4UnifieldAdmin'
!define DEFAULT_OPENERP_DROP_PWD 'dropAdmin'
!define DEFAULT_OPENERP_BKP_PWD 'bkAdmin'
!define DEFAULT_OPENERP_RESTORE_PWD 'restoreAdmin'

Name '${DISPLAY_NAME}'
Caption "${PRODUCT_NAME} ${VERSION} Setup"
OutFile "openerp-allinone-setup-${VERSION}.exe"
ShowInstDetails show

XPStyle on

InstallDir "$PROGRAMFILES\msf\Unifield"
InstallDirRegKey HKCU "${REGISTRY_KEY}" ""

BrandingText '${PRODUCT_NAME} ${VERSION}'

RequestExecutionLevel admin

!insertmacro GetParameters
!insertmacro GetOptions

Var cmdLineParams

Var TextPostgreSQLInstPath
Var TextPostgreSQLHostname
Var TextPostgreSQLPort
Var TextPostgreSQLUsername
Var TextPostgreSQLPassword

Var TextOPENERPPWD
Var TextOPENERPDROPPWD
Var TextOPENERPBKPPWD
Var TextOPENERPRESTOREPWD

Var HWNDPostgreSQLInstPath
Var HWNDPostgreSQLInstPath_Btn

Var HWNDPostgreSQLHostname
Var HWNDPostgreSQLPort
Var HWNDPostgreSQLUsername
Var HWNDPostgreSQLPassword

Var HWNDOpenERPPwd
Var HWNDOpenERPDropPwd
Var HWNDOpenERPBkpPwd
Var HWNDOpenERPRestorePwd

!define STATIC_PATH "static"
!define PIXMAPS_PATH "${STATIC_PATH}\pixmaps"

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
LangString DESC_FinishPageText ${LANG_ENGLISH} "Connect to OpenERP Web"
LangString DESC_OPENERPPage ${LANG_ENGLISH} "Configure the passwords for DB drop, backup and create from openerp"
LangString DESC_OPENERP_PWD ${LANG_ENGLISH} "Password to create DB"
LangString DESC_OPENERP_DROP_PWD ${LANG_ENGLISH} "Password to drop DB"
LangString DESC_OPENERP_BKP_PWD ${LANG_ENGLISH} "Password to backup DB"
LangString DESC_OPENERP_RESTORE_PWD ${LANG_ENGLISH} "Password to restore DB"
LangString WARNING_OPENERP_PasswordIsEmpty ${LANG_ENGLISH} "Password to create DB is empty"
LangString WARNING_OPENERP_DROP_PasswordIsEmpty ${LANG_ENGLISH} "Password to drop DB is empty"
LangString WARNING_OPENERP_BKP_PasswordIsEmpty ${LANG_ENGLISH} "Password to backup DB is empty"
LangString WARNING_OPENERP_RESTORE_PasswordIsEmpty ${LANG_ENGLISH} "Password to restore DB is empty"

; French
LangString MSG_ConnectionOK ${LANG_FRENCH} "Connection réussie!"
LangString MSG_ConnectionFAILED ${LANG_FRENCH} "Échec de la connection!"
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
LangString DESC_FinishPageText ${LANG_FRENCH} "Se connecter à OpenERP Web"
LangString DESC_OPENERPPage ${LANG_FRENCH} "Definissez les mots de passe pour la manipulation des bdd depuis OpenERP"
LangString DESC_OPENERP_PWD ${LANG_FRENCH} "MdP pour créer un bdd"
LangString DESC_OPENERP_DROP_PWD ${LANG_FRENCH} "MdP pour supprimer une bdd"
LangString DESC_OPENERP_BKP_PWD ${LANG_FRENCH} "MdP pour sauvegarder une bdd"
LangString DESC_OPENERP_RESTORE_PWD ${LANG_FRENCH} "MdP pour restaurer une bdd"
LangString WARNING_OPENERP_PasswordIsEmpty ${LANG_FRENCH} "MdP pour créer un bdd est vide"
LangString WARNING_OPENERP_DROP_PasswordIsEmpty ${LANG_FRENCH} "MdP pour supprimer une bdd est vide"
LangString WARNING_OPENERP_BKP_PasswordIsEmpty ${LANG_FRENCH} "MdP pour sauvegarder une bdd est vide"
LangString WARNING_OPENERP_RESTORE_PasswordIsEmpty ${LANG_FRENCH} "MdP pour restaurer une bdd est vide"

InstType $(Profile_AllInOne)
InstType $(Profile_Server)
InstType $(Profile_Web_Client)

Section $(TITLE_OpenERP_Server) SectionOpenERP_Server
    SectionIn 1 2

    # Install the MSVC 2013 redistributable, needed by PostgreSQL
    SetOutPath "$TEMP"
    File vcredist_x86.exe
    nsExec::ExecToLog '$TEMP\vcredist_x86.exe /install /quiet /norestart'
    Delete "$TEMP\vcredist_x86.exe"

    # Install Postgres

    nsExec::ExecToLog 'sc stop Postgres'
    nsExec::ExecToLog 'sc delete Postgres'
    nsExec::ExecToLog 'net user openpgsvc /delete'

    SetOutPath "$INSTDIR"
    File /r "pgsql"

    # Put the db admin user password into a file so that initdb can find it.
    GetTempFileName $0
    FileOpen $1 $0 w
    FileWrite $1 "$TextPostgreSQLPassword"
    FileClose $1

    # Init the DB, unless it already exists.
    ${If} ${FileExists} "$TextPostgreSQLInstPath\*"
        MessageBox MB_OK "Database directory $TextPostgreSQLInstPath already exists. Stopping installation."
        Abort
    ${EndIf}
    nsExec::ExecToLog 'pgsql\bin\initdb --pwfile "$0" \
	--data-checksums -A md5 \
        -U "$TextPostgreSQLUsername" \
        --locale="English_United States" -E UTF8 \
        "$TextPostgreSQLInstPath"'
    Pop $1
    Delete $0
    ${If} "$1" != "0"
        MessageBox MB_OK "Failed to create database in $TextPostgreSQLInstPath. Stopping installation. (Result code $1)"
        Abort
    ${Endif}

    # Create the service user and service
    nsExec::ExecToLog 'net user openpgsvc 0p3npgsvcPWD /add'
    SimpleSC::GrantServiceLogonPrivilege openpgsvc
    nsExec::ExecToLog 'icacls "$TextPostgreSQLInstPath" /c /t /grant openpgsvc:F'
    nsExec::ExecToLog 'pgsql\bin\pg_ctl register -N Postgres \
        -U openpgsvc -P 0p3npgsvcPWD -D "$TextPostgreSQLInstPath"'

    # Edit the postgresql.conf

    Push $R0
    FileOpen $R0 "$TextPostgreSQLInstPath\postgresql.conf" a
    FileSeek $R0 0 "END"
    # Start of custom PostgreSQL options
    FileWrite $R0 "listen_addresses = 'localhost'"
    # add \r\n
    FileWriteByte $R0 "13"
    FileWriteByte $R0 "10"

    FileWrite $R0 "port = $TextPostgreSQLPort"
    FileWriteByte $R0 "13"
    FileWriteByte $R0 "10"

    FileWrite $R0 "logging_collector = on"
    FileWriteByte $R0 "13"
    FileWriteByte $R0 "10"

    # The Unifield IT manual says a Unifield server should have
    # minimum 4 gig ram, suggested 8 gig of ram.
    # For why I chose 4gb*0.25 = 1024MB see:
    # http://thebuild.com/blog/2017/06/09/shared_buffers-is-not-a-sensitive-setting/
    FileWrite $R0 "shared_buffers = 1024MB"
    FileWriteByte $R0 "13"
    FileWriteByte $R0 "10"
    FileClose $R0
    Pop $R0

    nsExec::ExecToLog 'net start Postgres'
    sleep 2

    # Install OpenERP Server
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
    WriteIniStr "$INSTDIR\Server\openerp-server.conf" "options" "pg_path" "$INSTDIR\pgsql\bin"

    Push $R1
    ${Base64_Encode} "$TextOPENERPPWD"
    Pop $R1
    WriteIniStr "$INSTDIR\Server\openerp-server.conf" "options" "admin_passwd" $R1
    Push $R2
    ${Base64_Encode} "$TextOPENERPDROPPWD"
    Pop $R2
    WriteIniStr "$INSTDIR\Server\openerp-server.conf" "options" "admin_dropdb_passwd" $R2
    Push $R3
    ${Base64_Encode} "$TextOPENERPBKPPWD"
    Pop $R3
    WriteIniStr "$INSTDIR\Server\openerp-server.conf" "options" "admin_bkpdb_passwd" $R3
    Push $R4
    ${Base64_Encode} "$TextOPENERPRESTOREPWD"
    Pop $R4
    WriteIniStr "$INSTDIR\Server\openerp-server.conf" "options" "admin_restoredb_passwd" $R4

    File /r "static\server-extra"
    CopyFiles "$TEMP\server-extra\*.*" "$INSTDIR\Server"
    nsExec::ExecToLog "net start openerp-server-6.0"
SectionEnd

Section $(TITLE_OpenERP_Web_Client) SectionOpenERP_Web_Client
    SectionIn 1 4
    SetOutPath "$TEMP"
    File "files\${OPENERP_WEB_SETUP}"
    ExecWait '"$TEMP\${OPENERP_WEB_SETUP}" /S /D=$INSTDIR\Web'
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

    # Uninstall Postgres
    nsExec::ExecToLog 'sc stop Postgres'
    nsExec::ExecToLog 'sc delete Postgres'
    nsExec::ExecToLog 'net user openpgsvc /delete'
    Rmdir /r "$INSTDIR/pgsql"

    DeleteRegKey HKLM "${UNINSTALL_REGISTRY_KEY}"
SectionEnd

Function .onInit
    Push $R0

    ${GetParameters} $cmdLineParams
    ClearErrors

    Pop $R0

    StrCpy $TextPostgreSQLHostname ${DEFAULT_POSTGRESQL_HOSTNAME}
    StrCpy $TextPostgreSQLPort ${DEFAULT_POSTGRESQL_PORT}
    StrCpy $TextPostgreSQLUsername ${DEFAULT_POSTGRESQL_USERNAME}
    StrCpy $TextPostgreSQLPassword ${DEFAULT_POSTGRESQL_PASSWORD}
    StrCpy $TextPostgreSQLInstPath "${DEFAULT_POSTGRESQL_INSTPATH}"

    StrCpy $TextOPENERPPWD ${DEFAULT_OPENERP_PASSWORD}
    StrCpy $TextOPENERPDROPPWD ${DEFAULT_OPENERP_DROP_PWD}
    StrCpy $TextOPENERPBKPPWD ${DEFAULT_OPENERP_BKP_PWD}
    StrCpy $TextOPENERPRESTOREPWD ${DEFAULT_OPENERP_RESTORE_PWD}

    !insertmacro MUI_LANGDLL_DISPLAY

    ; check for forced PostgreSQL install path on command line
    ; /PGINSTDIR="C:\PATH\TO\PostgreSQL"
    ClearErrors
    Push $R0
    ${GetOptions} $cmdLineParams '/PGINSTDIR=' $R0
    IfErrors +3 0
    StrCpy $TextPostgreSQLInstPath $R0
    Pop $R0

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

    ${NSD_CreateLabel} 0 0 100% 10u $(DESC_PostgreSQLPage)
    Pop $0

    ; setup and update default postgresql install path
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

  ${NSD_CreateLabel} 0 85 90u 12u $(DESC_OPENERP_PWD)
  Pop $0
  ${NSD_CreateText} 150 85 150u 12u $TextOPENERPPWD
  Pop $HWNDOpenERPPwd
  ${NSD_CreateLabel} 0 115 90u 12u $(DESC_OPENERP_DROP_PWD)
  Pop $0
  ${NSD_CreateText} 150 115 150u 12u $TextOPENERPDROPPWD
  Pop $HWNDOpenERPDropPwd
  ${NSD_CreateLabel} 0 145 90u 12u $(DESC_OPENERP_BKP_PWD)
  Pop $0
  ${NSD_CreateText} 150 145 150u 12u $TextOPENERPBKPPWD
  Pop $HWNDOpenERPBkpPwd
  ${NSD_CreateLabel} 0 175 90u 12u $(DESC_OPENERP_RESTORE_PWD)
  Pop $0
  ${NSD_CreateText} 150 175 150u 12u $TextOPENERPRESTOREPWD
  Pop $HWNDOpenERPRestorePwd

  nsDialogs::Show

FunctionEnd


Function LeaveDBPasswordPage
    ${NSD_GetText} $HWNDOpenERPPwd $TextOPENERPPWD
    ${NSD_GetText} $HWNDOpenERPDropPwd $TextOPENERPDROPPWD
    ${NSD_GetText} $HWNDOpenERPBkpPwd $TextOPENERPBKPPWD
    ${NSD_GetText} $HWNDOpenERPRestorePwd $TextOPENERPRESTOREPWD

    StrLen $1 $TextOPENERPPWD
    ${If} $1 == 0
        MessageBox MB_ICONEXCLAMATION|MB_OK $(WARNING_OPENERP_PasswordIsEmpty)
        Abort
    ${EndIf}

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

Function LaunchLink
    ExecShell "open" "http://localhost:8061/"
FunctionEnd
