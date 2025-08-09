# build/ipa_gui.spec
# Build locally with: py -m PyInstaller build\ipa_gui.spec
import os
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
ENTRY = os.path.join(ROOT, 'ipa_gui_advanced.py')
ICON  = os.path.join(ROOT, 'resources', 'icon.ico')

hidden = collect_submodules('pandas') + collect_submodules('PySide6')
datas = collect_data_files('PySide6', includes=['Qt/plugins/platforms/*', 'Qt/translations/*'])
datas += [(ICON, 'resources')]  # optional icon

a = Analysis(
    [ENTRY],                 # ← absolute path to entry script
    pathex=[ROOT],           # ← add repo root to sys.path for imports
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
    icon=ICON,               # ← absolute icon path
    console=False,
)
coll = COLLECT(
    exe, a.binaries, a.zipfiles, a.datas,
    strip=False, upx=False, name='IPA Pipeline GUI'
)
