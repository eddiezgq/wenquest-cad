; 问渠 CAD 测试版安装向导（Inno Setup 6）。ISCC /DEnvDir=<pixi 环境> /DAppVersion=<版本>
#ifndef AppVersion
  #define AppVersion "0.3.0-beta"
#endif
[Setup]
AppId={{7E2A5B0C-6C1F-4F2B-9C3E-5A1D2E8B9F10}
AppName=问渠 CAD
AppVerName=问渠 CAD {#AppVersion}（测试版）
AppVersion={#AppVersion}
AppPublisher=WenQuest 问渠
AppPublisherURL=https://wenquestrobotics.com/download
DefaultDirName={autopf}\WenQuestCAD
DefaultGroupName=问渠 CAD
DisableProgramGroupPage=yes
OutputBaseFilename=WenQuestCAD-{#AppVersion}-Setup
Compression=lzma2/max
SolidCompression=yes
LZMANumBlockThreads=4
LZMAUseSeparateProcess=yes
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequiredOverridesAllowed=dialog
DiskSpanning=no
WizardStyle=modern
ShowLanguageDialog=yes
LicenseFile=license-zh.txt
[Languages]
Name: "zh"; MessagesFile: "ChineseSimplified.isl"; LicenseFile: "license-zh.txt"
Name: "en"; MessagesFile: "compiler:Default.isl"; LicenseFile: "license-en.txt"
[Files]
Source: "{#EnvDir}\*"; DestDir: "{app}\env"; Flags: recursesubdirs createallsubdirs ignoreversion
Source: "WenQuestCAD.cmd"; DestDir: "{app}"; Flags: ignoreversion
Source: "license-zh.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "license-en.txt"; DestDir: "{app}"; Flags: ignoreversion
[Icons]
Name: "{group}\问渠 CAD"; Filename: "{app}\WenQuestCAD.cmd"; WorkingDir: "{app}"; IconFilename: "{app}\env\Library\bin\FreeCAD.exe"; Flags: runminimized
Name: "{autodesktop}\问渠 CAD"; Filename: "{app}\WenQuestCAD.cmd"; WorkingDir: "{app}"; IconFilename: "{app}\env\Library\bin\FreeCAD.exe"; Flags: runminimized
Name: "{group}\卸载问渠 CAD"; Filename: "{uninstallexe}"
[Run]
Filename: "{app}\WenQuestCAD.cmd"; Description: "启动问渠 CAD / Launch WenQuest CAD"; Flags: postinstall nowait skipifsilent runminimized
