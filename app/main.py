"""Windows 데스크톱 통합 리뷰센터 실행 진입점."""

from __future__ import annotations

import argparse
from pathlib import Path
import threading
import time
import traceback
import webbrowser
import sys
import os
from typing import Any

import uvicorn

if __package__ in {None, ""}:
    repo_root = Path(__file__).resolve().parents[1]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

from runtime import (
    default_local_portable_exe_path,
    default_local_portable_bundle_root,
    default_startup_log_path,
    load_local_app_settings,
)


class DesktopBridge:
    """기능: pywebview 창에서 네이티브 파일 탐색기를 여는 JS bridge다."""

    def __init__(self) -> None:
        self.window = None

    def attach_window(self, window: Any) -> None:
        self.window = window

    def dialog_capabilities(self) -> dict[str, object]:
        _append_startup_log(
            "bridge: dialog_capabilities called "
            + ("with window" if self.window is not None else "without window")
        )
        return {
            "native_dialog": self.window is not None,
        }

    def pick_folder(self, current_path: str = "", workspace_root: str = "") -> dict[str, object]:
        return self._pick_dialog(
            dialog_type_name="FOLDER_DIALOG",
            current_path=current_path,
            workspace_root=workspace_root,
            file_types=(),
        )

    def pick_file(
        self,
        current_path: str = "",
        workspace_root: str = "",
        file_types: list[str] | None = None,
    ) -> dict[str, object]:
        return self._pick_dialog(
            dialog_type_name="OPEN_DIALOG",
            current_path=current_path,
            workspace_root=workspace_root,
            file_types=tuple(file_types or ["Excel (*.xlsx;*.xlsm;*.xltx;*.xltm)"]),
        )

    def _pick_dialog(
        self,
        *,
        dialog_type_name: str,
        current_path: str,
        workspace_root: str,
        file_types: tuple[str, ...],
    ) -> dict[str, object]:
        if self.window is None:
            _append_startup_log("bridge: create_file_dialog requested before window attach")
            return {
                "ok": False,
                "error": "이 환경에서는 네이티브 파일 탐색기를 열 수 없다.",
                "path": "",
            }
        try:
            import webview

            directory = self._resolve_dialog_directory(
                current_path=current_path,
                workspace_root=workspace_root,
            )
            result = self.window.create_file_dialog(
                getattr(webview, dialog_type_name),
                directory=directory,
                allow_multiple=False,
                file_types=file_types,
            )
            selected = str(result[0]) if result else ""
            _append_startup_log(
                f"bridge: {dialog_type_name} "
                + ("selected path" if selected else "cancelled")
            )
            return {
                "ok": bool(selected),
                "error": "" if selected else "선택이 취소되었다.",
                "path": selected,
            }
        except Exception as exc:
            _append_startup_log(f"bridge: {dialog_type_name} failed: {exc.__class__.__name__}: {exc}")
            return {
                "ok": False,
                "error": f"{exc.__class__.__name__}: {exc}",
                "path": "",
            }

    def _resolve_dialog_directory(self, *, current_path: str, workspace_root: str) -> str:
        default_root = Path(workspace_root).expanduser() if workspace_root else Path.home()
        text = current_path.strip()
        if not text:
            return str(default_root if default_root.exists() else Path.home())
        candidate = Path(text).expanduser()
        if not candidate.is_absolute() and workspace_root:
            candidate = Path(workspace_root) / candidate
        if candidate.is_file():
            candidate = candidate.parent
        if candidate.exists():
            return str(candidate)
        if candidate.parent.exists():
            return str(candidate.parent)
        if default_root.exists():
            return str(default_root)
        return str(Path.home())


def _startup_log_path() -> Path:
    return default_startup_log_path()


def _append_startup_log(message: str) -> None:
    log_path = _startup_log_path()
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(message.rstrip() + "\n")


def _current_launch_path() -> Path:
    source = sys.executable if getattr(sys, "frozen", False) else __file__
    return Path(source).resolve()


def _is_remote_windows_launch_path(path: Path) -> bool:
    if os.name != "nt":
        return False
    text = str(path)
    if text.startswith("\\\\"):
        return True
    if not path.drive:
        return False
    try:
        import ctypes

        drive_root = f"{path.drive}\\"
        return ctypes.windll.kernel32.GetDriveTypeW(drive_root) == 4
    except Exception:
        return False


def _normalized_windows_path(path: Path) -> str:
    return os.path.normcase(os.path.abspath(str(path)))


def _is_official_local_launch_path(*, launch_path: Path, official_local_bundle_root: Path) -> bool:
    root_text = _normalized_windows_path(official_local_bundle_root)
    launch_text = _normalized_windows_path(launch_path)
    if launch_text == _normalized_windows_path(official_local_bundle_root / "EmailPilotAI.exe"):
        return True
    return launch_text.startswith(root_text + os.sep)


def _unsupported_launch_reason(
    *,
    launch_path: Path,
    official_local_bundle_root: Path,
    official_local_exe_path: Path,
) -> str:
    if os.name != "nt" or not getattr(sys, "frozen", False):
        return ""
    if _is_remote_windows_launch_path(launch_path):
        return (
            "공유 폴더 직접 실행은 공식 지원 경로가 아니다. "
            "세이브 파일은 공유 폴더에서 열 수 있지만, 실행 파일은 반드시 "
            f"`{official_local_exe_path}`로 실행해야 한다."
        )
    if not _is_official_local_launch_path(
        launch_path=launch_path,
        official_local_bundle_root=official_local_bundle_root,
    ):
        return (
            "현재 실행 경로는 임시 build 산출물 또는 비공식 복사본이다. "
            f"항상 `{official_local_exe_path}`만 실행해야 한다."
        )
    return ""


def _show_windows_error_dialog(*, title: str, message: str) -> None:
    if os.name != "nt":
        return
    try:
        import ctypes

        ctypes.windll.user32.MessageBoxW(None, message, title, 0x10)
    except Exception:
        _append_startup_log("launcher: failed to open Windows message box")


def main() -> None:
    _append_startup_log("launcher: entered main()")
    parser = argparse.ArgumentParser(description="Email Pilot AI desktop launcher")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument(
        "--no-window",
        action="store_true",
        help="pywebview 창 대신 headless 서버로만 띄운다.",
    )
    parser.add_argument(
        "--browser-fallback",
        action="store_true",
        help="pywebview 창 생성에 실패하면 로컬 브라우저로 fallback 한다.",
    )
    args = parser.parse_args()
    _append_startup_log(
        f"launcher: parsed args host={args.host} port={args.port} "
        f"no_window={args.no_window} browser_fallback={args.browser_fallback}"
    )
    local_settings = load_local_app_settings()
    _append_startup_log("launcher: loaded local settings")
    launch_path = _current_launch_path()
    startup_log_path = _startup_log_path()
    official_local_bundle_root = default_local_portable_bundle_root()
    official_local_exe_path = default_local_portable_exe_path()
    unsupported_launch_reason = _unsupported_launch_reason(
        launch_path=launch_path,
        official_local_bundle_root=official_local_bundle_root,
        official_local_exe_path=official_local_exe_path,
    )

    if not args.no_window and unsupported_launch_reason:
        _append_startup_log(f"launcher: unsupported launch path detected: {launch_path}")
        _append_startup_log(f"launcher: unsupported reason: {unsupported_launch_reason}")
        _show_windows_error_dialog(
            title="Email Pilot AI",
            message=(
                "공유 폴더 직접 실행은 지원하지 않습니다.\n\n"
                f"현재 실행 경로:\n{launch_path}\n\n"
                f"공식 실행 파일:\n{official_local_exe_path}\n\n"
                f"startup.log:\n{startup_log_path}\n\n"
                "세이브 파일은 공유 폴더에서 열 수 있지만, 실행 파일은 위 경로에서만 실행해 주세요."
            ),
        )
        return

    from app.server import app as fastapi_app, set_shell_context
    _append_startup_log("launcher: imported app.server")
    if args.no_window:
        set_shell_context(
            shell_mode="headless",
            native_dialog_state="desktop_failed",
            startup_log_path=str(startup_log_path),
            official_local_bundle_path=str(official_local_exe_path),
            native_dialog_expected=False,
            launch_path=str(launch_path),
        )
    else:
        set_shell_context(
            shell_mode="desktop_window",
            native_dialog_state="desktop_pending",
            startup_log_path=str(startup_log_path),
            official_local_bundle_path=str(official_local_exe_path),
            native_dialog_expected=True,
            unsupported_launch_reason=unsupported_launch_reason,
            launch_path=str(launch_path),
        )

    config = uvicorn.Config(
        fastapi_app,
        host=args.host,
        port=args.port,
        reload=False,
        log_level="info",
        log_config=None,
    )
    server = uvicorn.Server(config)
    url = f"http://{args.host}:{args.port}"
    _append_startup_log(f"launcher: created uvicorn config for {url}")

    if args.no_window:
        _append_startup_log("launcher: starting in --no-window mode")
        server.run()
        return

    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    time.sleep(1.2)
    _append_startup_log("launcher: background server thread started")

    try:
        import webview

        _append_startup_log("launcher: imported pywebview")
        bridge = DesktopBridge()
        window = webview.create_window(
            "Email Pilot AI",
            url,
            js_api=bridge,
            width=local_settings.window_width,
            height=local_settings.window_height,
        )
        bridge.attach_window(window)
        _append_startup_log("launcher: pywebview window created and bridge attached")
        set_shell_context(
            shell_mode="desktop_window",
            native_dialog_state="desktop_pending",
            startup_log_path=str(startup_log_path),
            official_local_bundle_path=str(official_local_exe_path),
            native_dialog_expected=True,
            unsupported_launch_reason=unsupported_launch_reason,
            launch_path=str(launch_path),
        )
        webview.start()
    except Exception as exc:
        _append_startup_log("launcher: pywebview failed, checking browser fallback")
        set_shell_context(
            shell_mode="browser_fallback" if args.browser_fallback else "desktop_window",
            native_dialog_state="browser_fallback" if args.browser_fallback else "desktop_failed",
            startup_log_path=str(startup_log_path),
            official_local_bundle_path=str(official_local_exe_path),
            native_dialog_expected=not args.browser_fallback,
            launch_path=str(launch_path),
        )
        if not args.browser_fallback:
            raise RuntimeError(
                (
                    "pywebview 창을 열지 못했다. "
                    "--browser-fallback 옵션으로 로컬 브라우저 fallback을 허용할 수 있다."
                )
            ) from exc
        webbrowser.open(url)
        thread.join()


if __name__ == "__main__":
    try:
        main()
    except Exception:
        _append_startup_log("launcher: unhandled exception")
        _append_startup_log(traceback.format_exc())
        raise
