# build/ipa_gui.spec
# Build locally with:  py -m PyInstaller build\ipa_gui.spec
import os
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

# --- Paths ---
ROOT  = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
ENTRY = os.path.join(ROOT, 'ipa_gui_advanced.py')          
ICON  = os.path.join(ROOT, 'resources', 'icon.ico')

# --- Hidden imports & data ---
hidden = collect_submodules('pandas') + collect_submodules('PySide6')
datas  = collect_data_files('PySide6', includes=['Qt/plugins/platforms/*', 'Qt/translations/*'])
if os.path.exists(ICON):
    datas += [(ICON, 'resources')]

# --- Analysis ---
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

# --- Build ---
pyz = PYZ(a.pure, a.zipped_data)
exe = EXE(
    pyz,
    a.scripts, a.binaries, a.zipfiles, a.datas,
    name='IPA Pipeline GUI',
    icon=ICON if os.path.exists(ICON) else None,
    console=False,
)

coll = COLLECT(
    exe, a.binaries, a.zipfiles, a.datas,
    strip=False, upx=False, name='IPA Pipeline GUI'
)

