; Build locally: iscc build\setup.iss /DMyAppVersion=0.1.0

#define MyAppName "IPA Pipeline GUI"
#ifndef MyAppVersion
  #define MyAppVersion "0.0.0"
#endif
#define MyAppExe "IPA Pipeline GUI.exe"

[Setup]
AppName={#MyAppName}
AppVersion={#MyAppVersion}
DefaultDirName={pf}\{#MyAppName}
DefaultGroupName={#MyAppName}
OutputBaseFilename=IPA-Pipeline-GUI-Setup
ArchitecturesInstallIn64BitMode=x64
UninstallDisplayIcon={app}\{#MyAppExe}

[Files]
Source: "..\dist\IPA Pipeline GUI\*"; DestDir: "{app}"; Flags: recursesubdirs ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExe}"
Name: "{commondesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExe}"

[Run]
Filename: "{app}\{#MyAppExe}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent
