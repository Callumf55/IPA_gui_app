# build/ipa_gui.spec
# Build locally with:  py -m PyInstaller build\ipa_gui.spec
import os
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

# --- Paths (point to repo root, not build/) ---
ROOT  = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
ENTRY = os.path.join(ROOT, 'ipa_gui_advanced.py')          # your GUI entry script
ICON  = os.path.join(ROOT, 'resources', 'icon.ico')         # optional

# --- Hidden imports & data (Qt plugins, pandas/numpy internals) ---
hidden = collect_submodules('pandas') + collect_submodules('PySide6')
datas  = collect_data_files('PySide6', includes=['Qt/plugins/platforms/*', 'Qt/translations/*'])
if os.path.exists(ICON):
    datas += [(ICON, 'resources')]

# --- Analysis ---
a = Analysis(
    [ENTRY],                 # absolute path so PyInstaller doesn't look in build/
    pathex=[ROOT],           # add repo root to sys.path
    binaries=[],
    datas=datas,
    hiddenimports=hidden,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['pytest', '_pytest'],   # avoid pytest hook issues on Python 3.13
    noarchive=False,
)

# --- Build ---
pyz = PYZ(a.pure, a.zipped_data)
exe = EXE(
    pyz,
    a.scripts, a.binaries, a.zipfiles, a.datas,
    name='IPA Pipeline GUI',
    icon=ICON if os.path.exists(ICON) else None,
    console=False,           # no console window
)

coll = COLLECT(
    exe, a.binaries, a.zipfiles, a.datas,
    strip=False, upx=False, name='IPA Pipeline GUI'
)
