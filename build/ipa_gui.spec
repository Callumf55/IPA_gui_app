# build/ipa_gui.spec
import os
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

ROOT  = os.path.abspath(os.getcwd())              # repo root
ENTRY = os.path.join(ROOT, 'ipa_gui_advanced.py') # entry script (absolute)
ICON  = os.path.join(ROOT, 'resources', 'icon.ico')  # icon in repo root (absolute)

hidden = collect_submodules('pandas') + collect_submodules('PySide6')
datas  = collect_data_files('PySide6', includes=['Qt/plugins/platforms/*', 'Qt/translations/*'])
# bundling the icon as data is optional; safe to include if present
if os.path.exists(ICON):
    datas += [(ICON, 'resources')]

a = Analysis(
    [ENTRY],
    pathex=[ROOT],
    binaries=[],
    datas=datas,
    hiddenimports=hidden,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['pytest', '_pytest'],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(
    pyz,
    a.scripts, a.binaries, a.zipfiles, a.datas,
    name='IPA_Pipeline_GUI',
    icon=ICON if os.path.exists(ICON) else None,  # use absolute icon; skip if missing
    console=False,
)

coll = COLLECT(
    exe, a.binaries, a.zipfiles, a.datas,
    strip=False, upx=False, name='IPA_Pipeline_GUI'
)
