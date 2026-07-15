import os
import sys
import subprocess
import shutil

print("--- OceanNav Updater Builder ---")
new_version = input("Enter the new version number (e.g. 1.1.0): ").strip()
if not new_version:
    print("Version cannot be empty!")
    sys.exit(1)

# Update version.py
with open("app/version.py", "w") as f:
    f.write(f'__version__ = "{new_version}"\n')
print(f"Updated app/version.py to {new_version}")

print("\n1. Packaging OceanNav App with PyInstaller...")
subprocess.run(["pyinstaller", "OceanNav.spec", "--clean", "-y"], check=True)

print("2. Creating Update Installer with Inno Setup...")
iss_content = r"""
[Setup]
AppName=OceanNav
AppVersion=1.1
DefaultDirName={localappdata}\OceanNav
DefaultGroupName=OceanNav
OutputDir=C:\Janith\EXE fil
OutputBaseFilename=OceanNav_Update_Installer
Compression=lzma2
SolidCompression=yes
PrivilegesRequired=lowest

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop icon"; GroupDescription: "Additional icons:"

[Files]
Source: "dist\OceanNav\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "srilanka map\*"; DestDir: "{app}\srilanka map"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\OceanNav"; Filename: "{app}\OceanNav.exe"
Name: "{autodesktop}\OceanNav"; Filename: "{app}\OceanNav.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\OceanNav.exe"; Description: "Launch OceanNav"; Flags: nowait postinstall skipifsilent
"""

with open("installer.iss", "w") as f:
    f.write(iss_content)

inno_path = r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
try:
    subprocess.run([inno_path, "installer.iss"], check=True)
    print("\nSUCCESS! The new update installer is ready at: C:\\Janith\\EXE fil\\OceanNav_Update_Installer.exe")
except Exception as e:
    print("\nFailed to run Inno Setup. Is it installed at", inno_path, "?")
