# Build locally with: py -m PyInstaller build\ipa_gui.spec
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

hidden = collect_submodules('pandas') + collect_submodules('PySide6')
datas = collect_data_files('PySide6', includes=['Qt/plugins/platforms/*', 'Qt/translations/*'])
datas += [('resources/icon.ico', 'resources')]  # optional icon file

a = Analysis(
    ['ipa_gui_advanced.py'],   # entry point
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hidden,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data)
exe = EXE(
    pyz, a.scripts, a.binaries, a.zipfiles, a.datas,
    name='IPA Pipeline GUI',
    icon='resources/icon.ico',   # remove if you skip the icon
    console=False,               # no console window
)
coll = COLLECT(
    exe, a.binaries, a.zipfiles, a.datas,
    strip=False, upx=False, name='IPA Pipeline GUI'
)
