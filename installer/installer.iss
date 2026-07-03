; Faqture Installer - Inno Setup Script
; Requires: nssm.exe in installer/bin/
; Build: ISCC.exe /DAPP_VERSION=x.y.z installer\installer.iss

#define MyAppName "Faqture"
#define MyAppPublisher "Dalnec"
#define MyAppURL "https://github.com/Dalnec/faqture-api"
#define MyAppExeName "faqture.exe"
#define MyServiceName "FaqtureServicio"
#define MyUpdaterExeName "updater.exe"
#define MyUpdaterTaskName "FaqtureUpdater"

; Version passed from CI via /DAPP_VERSION=x.y.z
#ifndef APP_VERSION
  #define APP_VERSION "0.0.0"
#endif

[Setup]
AppId={{B5E3A7D1-4F2C-4A8E-9D6B-1C3E5A7F9B2D}
AppName={#MyAppName}
AppVersion={#APP_VERSION}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
OutputDir=dist
OutputBaseFilename=Faqture-{#APP_VERSION}-Setup
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=admin
SetupIconFile=..\logo.ico
UninstallDisplayIcon={app}\{#MyAppExeName}

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
; Main application
Source: "..\dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
; Updater
Source: "..\dist\{#MyUpdaterExeName}"; DestDir: "{app}"; Flags: ignoreversion
; NSSM service manager
Source: "bin\nssm.exe"; DestDir: "{app}"; Flags: ignoreversion
; Version file for updater
Source: "..\dist\version.txt"; DestDir: "{app}"; Flags: ignoreversion
; Default config (client edits after install)
Source: "..\config.ini.example"; DestDir: "{app}"; DestName: "config.ini"; Flags: ignoreversion onlyifdoesntexist

[Dirs]
Name: "{app}\logs"; Permissions: users-modify

[Run]
; Install Faqture service via NSSM
Filename: "{app}\nssm.exe"; Parameters: "install {#MyServiceName} ""{app}\{#MyAppExeName}"""; StatusMsg: "Instalando servicio..."; Flags: runhidden
Filename: "{app}\nssm.exe"; Parameters: "set {#MyServiceName} AppDirectory ""{app}"""; Flags: runhidden
Filename: "{app}\nssm.exe"; Parameters: "set {#MyServiceName} Start SERVICE_AUTO_START"; Flags: runhidden
Filename: "{app}\nssm.exe"; Parameters: "set {#MyServiceName} AppStdout ""{app}\service.log"""; Flags: runhidden
Filename: "{app}\nssm.exe"; Parameters: "set {#MyServiceName} AppStderr ""{app}\service.log"""; Flags: runhidden
Filename: "{app}\nssm.exe"; Parameters: "set {#MyServiceName} AppRotateFiles 1"; Flags: runhidden
Filename: "{app}\nssm.exe"; Parameters: "set {#MyServiceName} AppRotateBytes 5242880"; Flags: runhidden
; Start the service
Filename: "{app}\nssm.exe"; Parameters: "start {#MyServiceName}"; StatusMsg: "Iniciando servicio..."; Flags: runhidden
; Create scheduled task for auto-updater (every 6 hours)
Filename: "schtasks.exe"; Parameters: "/Create /TN ""{#MyUpdaterTaskName}"" /TR ""\22{app}\{#MyUpdaterExeName}\22"" /SC HOURLY /MO 6 /RU SYSTEM /F"; StatusMsg: "Configurando actualizador automatico..."; Flags: runhidden

[UninstallRun]
; Stop and remove service
Filename: "{app}\nssm.exe"; Parameters: "stop {#MyServiceName}"; Flags: runhidden
Filename: "{app}\nssm.exe"; Parameters: "remove {#MyServiceName} confirm"; Flags: runhidden
; Remove scheduled task
Filename: "schtasks.exe"; Parameters: "/Delete /TN ""{#MyUpdaterTaskName}"" /F"; Flags: runhidden

[UninstallDelete]
Type: filesandordirs; Name: "{app}\logs"
Type: files; Name: "{app}\service.log"
Type: files; Name: "{app}\updater.log"
