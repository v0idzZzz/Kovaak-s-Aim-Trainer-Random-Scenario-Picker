# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.win32 import versioninfo

# This is the version information block that will be embedded in the .exe
version_file = versioninfo.VSVersionInfo(
    ffi=versioninfo.FixedFileInfo(
        filevers=(1, 0, 0, 0),
        prodvers=(1, 0, 0, 0),
        mask=0x3f,
        flags=0x0,
        OS=0x40004,
        fileType=0x1,
        subtype=0x0,
        date=(0, 0),
    ),
    kids=[
        versioninfo.StringFileInfo(
            [
                versioninfo.StringTable(
                    "040904B0", # English (US)
                    [
                        versioninfo.StringStruct("CompanyName", "Jogurkaka and v0id_"),
                        versioninfo.StringStruct("FileDescription", "KovaaK's Challenge Runner"),
                        versioninfo.StringStruct("FileVersion", "1.0.0.0"),
                        versioninfo.StringStruct("InternalName", "KovaaksChallenge"),
                        versioninfo.StringStruct("LegalCopyright", "© 2025 Jogurkaka and v0id_. All rights reserved."),
                        versioninfo.StringStruct("OriginalFilename", "KovaaksChallenge.exe"),
                        versioninfo.StringStruct("ProductName", "Kovaaks Challenge Runner"),
                        versioninfo.StringStruct("ProductVersion", "1.0.0.0"),
                    ],
                )
            ]
        ),
        versioninfo.VarFileInfo([versioninfo.VarStruct("Translation", [1033, 1200])]),
    ],
)

# This is the main analysis block. PyInstaller will find all scripts starting from kovaak_gui.py
a = Analysis(
    ['kovaak_gui.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data)

# This defines the final executable. It is configured for a one-file build.
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='KovaaksChallenge',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # This prevents a black console window from opening
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version=version_file, # This attaches all the version info from above
)