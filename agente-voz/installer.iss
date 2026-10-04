; Instalador de Jarcrow - requiere Inno Setup 6 (lo instala build.ps1 si falta)
; AppVersion = versión del launcher/.exe. La versión del código vive en app/version.txt y se actualiza sola.
#define AppName "Jarcrow"
#define AppVersion "1.1.0"
#define AppExe "Jarcrow.exe"

[Setup]
AppId={{6F3C2A51-9B7E-4D2A-8C11-4A4152435257}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher=Overskull
; Instalación por usuario: no pide permisos de administrador
PrivilegesRequired=lowest
DefaultDirName={localappdata}\Programs\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
OutputDir=installer
OutputBaseFilename=Jarcrow-Setup-{#AppVersion}
Compression=lzma2/ultra64
SolidCompression=yes
UninstallDisplayIcon={app}\{#AppExe}
WizardStyle=modern

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "Crear acceso directo en el escritorio"; GroupDescription: "Accesos directos:"

[Files]
Source: "dist\Jarcrow\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExe}"
Name: "{group}\Configurar {#AppName} (.env)"; Filename: "notepad.exe"; Parameters: """{userappdata}\Jarcrow\.env"""
Name: "{group}\Desinstalar {#AppName}"; Filename: "{uninstallexe}"
Name: "{userdesktop}\{#AppName}"; Filename: "{app}\{#AppExe}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExe}"; Description: "Abrir {#AppName}"; Flags: nowait postinstall skipifsilent
