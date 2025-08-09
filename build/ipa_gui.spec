# build/ipa_gui.spec
import os
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

# Build is invoked from repo root; keep entry absolute so it's unambiguous
ROOT  = os.path.abspath(os.getcwd())
ENTRY = os.path.join(ROOT, 'ipa_gui_advanced.py')

# Icon path is now RELATIVE TO THE SPEC DIRECTORY (we will copy it there in CI)
ICON_REL = os.path.join('resources', 'icon.ico')

hidden = collect_submodules('pandas') + collect_submodules('PySide6')
datas  = collect_data_files('PySide6', includes=['Qt/plugins/platforms/*', 'Qt/translations/*'])
# also bundle the icon so it’s available at runtime if you need it
if os.path.exists(os.path.join('build', ICON_REL)):
    datas += [(os.path.join('build', ICON_REL), 'resources')]

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
    name='IPA Pipeline GUI',
    icon=ICON_REL if os.path.exists(ICON_REL) else None,  # resolved from spec dir
    console=False,
)

coll = COLLECT(
    exe, a.binaries, a.zipfiles, a.datas,
    strip=False, upx=False, name='IPA Pipeline GUI'
)
