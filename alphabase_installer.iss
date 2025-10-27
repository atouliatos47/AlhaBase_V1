; AlphaBase Installer Script
#define MyAppName "AlphaBase"
#define MyAppVersion "4.0"
#define MyAppPublisher "Your Name"
#define MyAppURL "https://github.com/yourusername/alphabase"
#define MyAppExeName "start.bat"

[Setup]
AppId={{12345678-1234-1234-1234-123456789ABC}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
LicenseFile=
OutputDir=installer_output
OutputBaseFilename=AlphaBase_Setup
SetupIconFile=
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
; Python files
Source: "main.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "config.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "models.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "security_rules.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "query_system.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "file_storage.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "mqtt_manager.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "websocket_manager.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "setup.py"; DestDir: "{app}"; Flags: ignoreversion

; Web console
Source: "console\*"; DestDir: "{app}\console"; Flags: ignoreversion recursesubdirs createallsubdirs

; JavaScript client
Source: "alphabase.js"; DestDir: "{app}"; Flags: ignoreversion

; Setup files
Source: "requirements.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "start.bat"; DestDir: "{app}"; Flags: ignoreversion
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "INSTALL.txt"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
; Check and install Python
Filename: "{cmd}"; Parameters: "/c python --version || echo Python not found. Please install Python 3.9 or higher from python.org"; Flags: runhidden waituntilterminated postinstall; StatusMsg: "Checking Python installation..."

; Install dependencies
Filename: "{cmd}"; Parameters: "/c cd /d ""{app}"" && pip install -r requirements.txt"; Flags: runhidden waituntilterminated postinstall; StatusMsg: "Installing Python dependencies..."

; Run setup wizard on first install
Filename: "{cmd}"; Parameters: "/c cd /d ""{app}"" && python setup.py"; Flags: runhidden waituntilterminated postinstall; Description: "Configure AlphaBase"; StatusMsg: "Running configuration wizard..."

[UninstallDelete]
Type: filesandordirs; Name: "{app}\alphabase.db"
Type: filesandordirs; Name: "{app}\alphabase_storage"
Type: filesandordirs; Name: "{app}\alphabase_config.json"
Type: filesandordirs; Name: "{app}\__pycache__"