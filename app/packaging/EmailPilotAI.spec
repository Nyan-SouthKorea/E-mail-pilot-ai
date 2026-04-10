# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

REPO_ROOT = Path(SPECPATH).resolve().parents[1]
APP_ROOT = REPO_ROOT / "app"

# 프로젝트 모듈은 `app/main.py -> app/server.py` import 체인에서 따라가게 두고,
# 최종 대상 플랫폼인 Windows에서 쓰는 pywebview backend만 명시적으로 포함한다.
hiddenimports = [
    "backports",
    "backports.tarfile",
    "webview.platforms.edgechromium",
    "webview.platforms.mshtml",
    "webview.platforms.winforms",
]

datas = [
    (str(APP_ROOT / "templates"), "app/templates"),
    (str(APP_ROOT / "static"), "app/static"),
]


a = Analysis(
    [str(APP_ROOT / "main.py")],
    pathex=[str(REPO_ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="EmailPilotAI",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="EmailPilotAI",
)
