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

[Dirs]
Name: "{app}\logs"; Permissions: users-modify

[Run]
; Install Faqture service via NSSM
Filename: "{app}\nssm.exe"; Parameters: "install {#MyServiceName} ""{app}\{#MyAppExeName}"""; StatusMsg: "Instalando servicio..."; Flags: runhidden
Filename: "{app}\nssm.exe"; Parameters: "set {#MyServiceName} AppDirectory ""{app}"""; Flags: runhidden
Filename: "{app}\nssm.exe"; Parameters: "set {#MyServiceName} AppParameters ""--gui"""; Flags: runhidden
Filename: "{app}\nssm.exe"; Parameters: "set {#MyServiceName} Start SERVICE_AUTO_START"; Flags: runhidden
Filename: "{app}\nssm.exe"; Parameters: "set {#MyServiceName} AppStdout ""{app}\service.log"""; Flags: runhidden
Filename: "{app}\nssm.exe"; Parameters: "set {#MyServiceName} AppStderr ""{app}\service.log"""; Flags: runhidden
Filename: "{app}\nssm.exe"; Parameters: "set {#MyServiceName} AppRotateFiles 1"; Flags: runhidden
Filename: "{app}\nssm.exe"; Parameters: "set {#MyServiceName} AppRotateBytes 5242880"; Flags: runhidden
; Start the service (only if checkbox is checked)
Filename: "{app}\nssm.exe"; Parameters: "start {#MyServiceName}"; StatusMsg: "Iniciando servicio..."; Flags: runhidden; Check: ShouldStartService
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

[Code]
var
  // DB connection page
  DBPage: TInputQueryWizardPage;
  // Backup page
  BackupPage: TInputQueryWizardPage;
  BackupEnabled: TNewCheckBox;
  BackupDrive: TNewCheckBox;
  // Main processes page
  ProcPage: TInputQueryWizardPage;
  ProcDocCheck: TNewCheckBox;
  ProcAnulCheck: TNewCheckBox;
  ProcNcrediCheck: TNewCheckBox;
  ProcNventasCheck: TNewCheckBox;
  ProcGuiaCheck: TNewCheckBox;
  // Options page
  OptPage: TInputQueryWizardPage;
  DebugCheck: TNewCheckBox;
  SSLCheck: TNewCheckBox;
  // Final page
  StartServiceCheck: TNewCheckBox;

procedure InitializeWizard;
begin
  // === Page 1: Database connection ===
  DBPage := CreateInputQueryPage(wpSelectDir,
    'Conexión a Base de Datos',
    'Configure la conexión a PostgreSQL',
    'La contraseña se guardará localmente en config.ini.');
  DBPage.Add('Servidor (DB_HOST):', False);
  DBPage.Add('Puerto (DB_PORT):', False);
  DBPage.Add('Base de datos (DB_NAME):', False);
  DBPage.Add('Usuario (DB_USER):', False);
  DBPage.Add('Contraseña (DB_PASS):', True);
  DBPage.Values[0] := '127.0.0.1';
  DBPage.Values[1] := '5432';
  DBPage.Values[2] := 'BD_Comercial';
  DBPage.Values[3] := 'comercial';
  DBPage.Values[4] := 'comercial';

  // === Page 2: Backup ===
  BackupPage := CreateInputQueryPage(DBPage.ID,
    'Configuración de Backup',
    'Backup automático de la base de datos',
    'El backup se ejecuta mediante pg_dump dentro de la ventana horaria definida.');
  BackupPage.Add('Nombre del backup (BU_NAME):', False);
  BackupPage.Add('Hora inicio (BU_TIME):', False);
  BackupPage.Add('Hora fin (BU_TIME2):', False);
  BackupPage.Values[0] := 'FaqtureBackup';
  BackupPage.Values[1] := '00:00:00';
  BackupPage.Values[2] := '23:59:00';

  BackupEnabled := TNewCheckBox.Create(BackupPage.Surface);
  BackupEnabled.Parent := BackupPage.Surface;
  BackupEnabled.Left := ScaleX(20);
  BackupEnabled.Top := BackupPage.Edits[2].Top + ScaleY(30);
  BackupEnabled.Width := ScaleX(400);
  BackupEnabled.Caption := 'Habilitar backup automático (BU_STATE)';
  BackupEnabled.Checked := False;

  BackupDrive := TNewCheckBox.Create(BackupPage.Surface);
  BackupDrive.Parent := BackupPage.Surface;
  BackupDrive.Left := ScaleX(20);
  BackupDrive.Top := BackupEnabled.Top + ScaleY(25);
  BackupDrive.Width := ScaleX(400);
  BackupDrive.Caption := 'Subir backup a Google Drive (BU_DRIVE)';
  BackupDrive.Checked := False;

  // === Page 3: Processes ===
  ProcPage := CreateInputQueryPage(BackupPage.ID,
    'Procesos Habilitados',
    'Seleccione qué procesos ejecutar en cada ciclo',
    'Solo los procesos marcados se ejecutarán automáticamente.');

  ProcDocCheck := TNewCheckBox.Create(ProcPage.Surface);
  ProcDocCheck.Parent := ProcPage.Surface;
  ProcDocCheck.Left := ScaleX(20);
  ProcDocCheck.Top := ScaleY(10);
  ProcDocCheck.Width := ScaleX(400);
  ProcDocCheck.Caption := 'Enviar facturas/boletas (M_DOC)';
  ProcDocCheck.Checked := True;

  ProcAnulCheck := TNewCheckBox.Create(ProcPage.Surface);
  ProcAnulCheck.Parent := ProcPage.Surface;
  ProcAnulCheck.Left := ScaleX(20);
  ProcAnulCheck.Top := ProcDocCheck.Top + ScaleY(25);
  ProcAnulCheck.Width := ScaleX(400);
  ProcAnulCheck.Caption := 'Enviar anulaciones (M_ANUL)';
  ProcAnulCheck.Checked := False;

  ProcNcrediCheck := TNewCheckBox.Create(ProcPage.Surface);
  ProcNcrediCheck.Parent := ProcPage.Surface;
  ProcNcrediCheck.Left := ScaleX(20);
  ProcNcrediCheck.Top := ProcAnulCheck.Top + ScaleY(25);
  ProcNcrediCheck.Width := ScaleX(400);
  ProcNcrediCheck.Caption := 'Enviar notas de crédito (M_NCREDI)';
  ProcNcrediCheck.Checked := False;

  ProcNventasCheck := TNewCheckBox.Create(ProcPage.Surface);
  ProcNventasCheck.Parent := ProcPage.Surface;
  ProcNventasCheck.Left := ScaleX(20);
  ProcNventasCheck.Top := ProcNcrediCheck.Top + ScaleY(25);
  ProcNventasCheck.Width := ScaleX(400);
  ProcNventasCheck.Caption := 'Enviar notas de venta (M_NVENTAS)';
  ProcNventasCheck.Checked := False;

  ProcGuiaCheck := TNewCheckBox.Create(ProcPage.Surface);
  ProcGuiaCheck.Parent := ProcPage.Surface;
  ProcGuiaCheck.Left := ScaleX(20);
  ProcGuiaCheck.Top := ProcNventasCheck.Top + ScaleY(25);
  ProcGuiaCheck.Width := ScaleX(400);
  ProcGuiaCheck.Caption := 'Enviar guías de remisión (M_GUIA)';
  ProcGuiaCheck.Checked := False;

  // === Page 4: Options ===
  OptPage := CreateInputQueryPage(ProcPage.ID,
    'Opciones de Aplicación',
    'Configuración avanzada',
    'Generalmente no requiere cambios.');
  OptPage.Add('Fecha filtro (DATE_HEADER):', False);
  OptPage.Values[0] := '2025-01-01';

  DebugCheck := TNewCheckBox.Create(OptPage.Surface);
  DebugCheck.Parent := OptPage.Surface;
  DebugCheck.Left := ScaleX(20);
  DebugCheck.Top := OptPage.Edits[0].Top + ScaleY(30);
  DebugCheck.Width := ScaleX(400);
  DebugCheck.Caption := 'Modo debug (DEBUG) — logs detallados';
  DebugCheck.Checked := False;

  SSLCheck := TNewCheckBox.Create(OptPage.Surface);
  SSLCheck.Parent := OptPage.Surface;
  SSLCheck.Left := ScaleX(20);
  SSLCheck.Top := DebugCheck.Top + ScaleY(25);
  SSLCheck.Width := ScaleX(400);
  SSLCheck.Caption := 'Verificar certificados SSL del API externo (SSL_VERIFY)';
  SSLCheck.Checked := False;

  // === Final page: Start service checkbox ===
  StartServiceCheck := TNewCheckBox.Create(WizardForm);
  StartServiceCheck.Parent := WizardForm.FinishedPage;
  StartServiceCheck.Left := ScaleX(20);
  StartServiceCheck.Top := ScaleY(120);
  StartServiceCheck.Width := ScaleX(400);
  StartServiceCheck.Caption := 'Iniciar servicio FaqtureServicio ahora';
  StartServiceCheck.Checked := True;
end;

function ShouldStartService: Boolean;
begin
  Result := StartServiceCheck.Checked;
end;

function NextButtonClick(CurPageID: Integer): Boolean;
begin
  Result := True;
  if CurPageID = DBPage.ID then begin
    if DBPage.Values[2] = '' then begin
      MsgBox('Debe ingresar el nombre de la base de datos.', mbError, MB_OK);
      Result := False;
    end else if DBPage.Values[4] = '' then begin
      MsgBox('Debe ingresar la contraseña de la base de datos.', mbError, MB_OK);
      Result := False;
    end;
  end;
end;

function BoolToStr(Value: Boolean): String;
begin
  if Value then
    Result := 'True'
  else
    Result := 'False';
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  ConfigFile: String;
  Lines: TArrayOfString;
begin
  if CurStep = ssPostInstall then begin
    SetArrayLength(Lines, 32);
    Lines[0]  := '; config.ini - Faqture Configuration';
    Lines[1]  := '; Generado por el instalador';
    Lines[2]  := '';
    Lines[3]  := '[BASE]';
    Lines[4]  := 'DB_HOST = ' + DBPage.Values[0];
    Lines[5]  := 'DB_PORT = ' + DBPage.Values[1];
    Lines[6]  := 'DB_NAME = ' + DBPage.Values[2];
    Lines[7]  := 'DB_USER = ' + DBPage.Values[3];
    Lines[8]  := 'DB_PASS = ' + DBPage.Values[4];
    Lines[9]  := '';
    Lines[10] := '[BACKUP]';
    Lines[11] := 'BU_NAME = ' + BackupPage.Values[0];
    Lines[12] := 'BU_STATE = ' + BoolToStr(BackupEnabled.Checked);
    Lines[13] := 'BU_DRIVE = ' + BoolToStr(BackupDrive.Checked);
    Lines[14] := 'BU_TIME = ' + BackupPage.Values[1];
    Lines[15] := 'BU_TIME2 = ' + BackupPage.Values[2];
    Lines[16] := '';
    Lines[17] := '[MAIN]';
    Lines[18] := 'M_DOC = ' + BoolToStr(ProcDocCheck.Checked);
    Lines[19] := 'M_ANUL = ' + BoolToStr(ProcAnulCheck.Checked);
    Lines[20] := 'M_NCREDI = ' + BoolToStr(ProcNcrediCheck.Checked);
    Lines[21] := 'M_NVENTAS = ' + BoolToStr(ProcNventasCheck.Checked);
    Lines[22] := 'M_GUIA = ' + BoolToStr(ProcGuiaCheck.Checked);
    Lines[23] := '';
    Lines[24] := '[MODELS]';
    Lines[25] := 'DATE_HEADER = ' + OptPage.Values[0];
    Lines[26] := '';
    Lines[27] := '[APP]';
    Lines[28] := 'DEBUG = ' + BoolToStr(DebugCheck.Checked);
    Lines[29] := '';
    Lines[30] := '[API]';
    Lines[31] := 'SSL_VERIFY = ' + BoolToStr(SSLCheck.Checked);

    ConfigFile := ExpandConstant('{app}\config.ini');
    SaveStringsToFile(ConfigFile, Lines, False);
  end;
end;
