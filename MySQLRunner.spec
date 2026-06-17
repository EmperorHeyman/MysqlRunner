# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for MySQL Runner.

Build a one-file Windows executable:

    pip install -r requirements.txt
    pyinstaller MySQLRunner.spec

Output:
    dist/MySQLRunner.exe
"""

from pathlib import Path

# In PyInstaller spec execution, __file__ is not guaranteed; use CWD.
# We invoke pyinstaller from the project root.
ROOT = Path().resolve()
ICON_PATH = ROOT / "icon.ico"
VERSION_PATH = ROOT / "version_info.txt"

# Ship the icon so the running app can set its window/taskbar icon too.
datas = [(str(ICON_PATH), ".")]
binaries = []
# PyInstaller's PyQt6 hooks collect required WebEngine modules/resources
# from imports in code.
hiddenimports = []


a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "tkinter",
        "turtle",
        "unittest",
        "test",
        "pydoc",
        "doctest",
        "xmlrpc",
    ],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    exclude_binaries=False,
    name="MySQLRunner",
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,
    # Compress payload with UPX, but keep Python runtime DLLs uncompressed.
    # This avoids common startup failures while still shrinking the one-file EXE.
    upx=True,
    upx_exclude=["python313.dll", "vcruntime140.dll", "vcruntime140_1.dll"],
    console=False,  # GUI app: no console window.
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(ICON_PATH),
    version=str(VERSION_PATH),
)
