# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path
from PyInstaller.utils.hooks import collect_all

root = Path(SPECPATH)
datas = [(str(root / 'web'), 'web')]
binaries = []
hiddenimports = ['win32timezone', 'win32security', 'pystray', 'pystray._win32', 'pystray._util.win32', 'tkinter', 'tkinter.ttk', 'tkinter.messagebox', 'tkinter.filedialog', 'PIL.ImageTk', 'uvicorn.logging', 'uvicorn.loops.auto', 'uvicorn.protocols.http.auto', 'uvicorn.protocols.websockets.auto', 'uvicorn.lifespan.on']
for package in ('winrt', 'pycaw', 'comtypes'):
    d, b, h = collect_all(package)
    datas += [(src, dest) for src, dest in d if 'comtypes/test' not in src.replace('\\', '/')]
    binaries += b
    hiddenimports += [name for name in h if not name.startswith('comtypes.test')]

a = Analysis([str(root / 'DeskTouch.py')], pathex=[str(root)], binaries=binaries, datas=datas,
    hiddenimports=hiddenimports, hookspath=[], hooksconfig={}, runtime_hooks=[],
    excludes=['pytest', 'comtypes.test'], noarchive=False, optimize=0)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name='DeskTouch', debug=False,
    bootloader_ignore_signals=False, strip=False, upx=False, console=False,
    icon=str(root / 'web' / 'icon192.png'))
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name='DeskTouch')
