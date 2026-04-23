# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['app_gui.py'],
    pathex=[],
    binaries=[],
    datas=[('yolov8n.pt', '.'), ('yolov8n-seg.pt', '.'), ('/Users/yigitcanyontem/Saritay-infra/Cam-Censor/venv/lib/python3.12/site-packages/customtkinter/gui', 'customtkinter/gui'), ('/Users/yigitcanyontem/Saritay-infra/Cam-Censor/venv/lib/python3.12/site-packages/customtkinter/themes', 'customtkinter/themes')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='CamCensor',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
app = BUNDLE(
    exe,
    name='CamCensor.app',
    icon=None,
    bundle_identifier=None,
)
