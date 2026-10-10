#ifndef AppVersion
  #define AppVersion "1.0.0"
#endif

#ifndef PublishDir
  #define PublishDir "..\..\artifacts\PCDSLibrary.Desktop-win-x64"
#endif

#ifndef InstallerOutputDir
  #define InstallerOutputDir "..\..\artifacts\installer"
#endif

[Setup]
AppId={{1D0E6E94-5BC5-4CEE-AB44-E26572912B30}
AppName=PCDS Library Desktop
AppVersion={#AppVersion}
AppPublisher=Polytechnic College of Davao del Sur
SetupIconFile=..\PCDSLibrary.Desktop\Assets\pcds-library-icon.ico
DefaultDirName={autopf}\PCDS Library Desktop
DefaultGroupName=PCDS Library Desktop
UninstallDisplayIcon={app}\PCDSLibrary.Desktop.exe
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64
PrivilegesRequired=admin
OutputDir={#InstallerOutputDir}
OutputBaseFilename=Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"; Flags: unchecked

[Files]
Source: "{#PublishDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\PCDS Library Desktop"; Filename: "{app}\PCDSLibrary.Desktop.exe"; WorkingDir: "{app}"
Name: "{autodesktop}\PCDS Library Desktop"; Filename: "{app}\PCDSLibrary.Desktop.exe"; WorkingDir: "{app}"; Tasks: desktopicon
