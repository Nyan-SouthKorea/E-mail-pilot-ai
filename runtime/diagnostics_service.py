"""런타임 진단과 Windows 네이티브 dialog helper를 모은다."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import os
from pathlib import Path
import shutil
import subprocess


@dataclass(slots=True)
class PickerBridgeDiagnosticsResult:
    """기능: 파일 탐색기 bridge/self-test 결과를 표현한다."""

    status: str
    backend: str
    native_dialog_supported: bool
    powershell_available: bool
    window_attached: bool
    message: str
    details: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(slots=True)
class NativePickerResult:
    """기능: 네이티브 파일/폴더 선택 결과를 표현한다."""

    ok: bool
    path: str
    error: str
    backend: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def picker_bridge_self_test(
    *,
    shell_mode: str,
    window_attached: bool,
) -> PickerBridgeDiagnosticsResult:
    """기능: 현재 실행 환경에서 파일 탐색기 bridge 가능 여부를 진단한다."""

    powershell_path = _powershell_command_name()
    powershell_available = bool(powershell_path)
    native_dialog_supported = os.name == "nt" and powershell_available
    backend = "powershell-native" if native_dialog_supported else "unsupported"
    if shell_mode == "headless":
        return PickerBridgeDiagnosticsResult(
            status="fail",
            backend=backend,
            native_dialog_supported=False,
            powershell_available=powershell_available,
            window_attached=window_attached,
            message="headless 실행이라 파일 탐색기를 열 수 없습니다.",
            details=[
                "GUI 없이 실행 중이라 네이티브 picker를 띄울 수 없습니다.",
            ],
        )
    if not native_dialog_supported:
        return PickerBridgeDiagnosticsResult(
            status="fail",
            backend=backend,
            native_dialog_supported=native_dialog_supported,
            powershell_available=powershell_available,
            window_attached=window_attached,
            message="현재 환경에서는 Windows 네이티브 파일 탐색기를 사용할 수 없습니다.",
            details=[
                f"os.name={os.name}",
                f"powershell_available={powershell_available}",
            ],
        )
    return PickerBridgeDiagnosticsResult(
        status="pass",
        backend=backend,
        native_dialog_supported=True,
        powershell_available=True,
        window_attached=window_attached,
        message="Windows 네이티브 파일 탐색기를 호출할 준비가 되었습니다.",
        details=[
            f"shell_mode={shell_mode}",
            f"window_attached={window_attached}",
            "native backend는 PowerShell + System.Windows.Forms dialog를 사용합니다.",
        ],
    )


def pick_folder_native(
    *,
    current_path: str = "",
    workspace_root: str = "",
) -> NativePickerResult:
    """기능: Windows 네이티브 폴더 선택창을 연다."""

    return _run_native_picker(
        picker_kind="folder",
        current_path=current_path,
        workspace_root=workspace_root,
    )


def pick_file_native(
    *,
    current_path: str = "",
    workspace_root: str = "",
) -> NativePickerResult:
    """기능: Windows 네이티브 파일 선택창을 연다."""

    return _run_native_picker(
        picker_kind="file",
        current_path=current_path,
        workspace_root=workspace_root,
    )


def _run_native_picker(
    *,
    picker_kind: str,
    current_path: str,
    workspace_root: str,
) -> NativePickerResult:
    test_override = os.environ.get("EPA_PICKER_TEST_RESPONSE", "").strip()
    if test_override:
        return NativePickerResult(
            ok=True,
            path=test_override,
            error="",
            backend="test-override",
        )
    test_error = os.environ.get("EPA_PICKER_TEST_ERROR", "").strip()
    if test_error:
        return NativePickerResult(
            ok=False,
            path="",
            error=test_error,
            backend="test-override",
        )
    if os.environ.get("EPA_PICKER_TEST_CANCEL", "").strip():
        return NativePickerResult(
            ok=False,
            path="",
            error="선택이 취소되었습니다.",
            backend="test-override",
        )

    if os.name != "nt":
        return NativePickerResult(
            ok=False,
            path="",
            error="Windows가 아닌 환경에서는 네이티브 파일 탐색기를 열 수 없습니다.",
            backend="unsupported",
        )
    powershell_command = _powershell_command_name()
    if not powershell_command:
        return NativePickerResult(
            ok=False,
            path="",
            error="PowerShell을 찾지 못해 파일 탐색기를 열 수 없습니다.",
            backend="unsupported",
        )

    directory = _resolve_dialog_directory(
        current_path=current_path,
        workspace_root=workspace_root,
    )
    script = _folder_picker_script() if picker_kind == "folder" else _file_picker_script()
    env = os.environ.copy()
    env["EPA_PICKER_DIRECTORY"] = directory
    completed = subprocess.run(
        [powershell_command, "-NoProfile", "-STA", "-Command", script],
        capture_output=True,
        text=True,
        env=env,
    )
    if completed.returncode != 0:
        stderr = (completed.stderr or "").strip()
        return NativePickerResult(
            ok=False,
            path="",
            error=stderr or "파일 탐색기를 열지 못했습니다.",
            backend="powershell-native",
        )
    selected = (completed.stdout or "").strip()
    if not selected:
        return NativePickerResult(
            ok=False,
            path="",
            error="선택이 취소되었습니다.",
            backend="powershell-native",
        )
    return NativePickerResult(
        ok=True,
        path=selected,
        error="",
        backend="powershell-native",
    )


def _resolve_dialog_directory(*, current_path: str, workspace_root: str) -> str:
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


def _powershell_command_name() -> str:
    return (
        shutil.which("powershell")
        or shutil.which("powershell.exe")
        or shutil.which("pwsh")
        or ""
    )


def _folder_picker_script() -> str:
    return r"""
Add-Type -AssemblyName System.Windows.Forms
[System.Windows.Forms.Application]::EnableVisualStyles()
$dialog = New-Object System.Windows.Forms.FolderBrowserDialog
$directory = $env:EPA_PICKER_DIRECTORY
if ($directory) { $dialog.SelectedPath = $directory }
$result = $dialog.ShowDialog()
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
if ($result -eq [System.Windows.Forms.DialogResult]::OK) {
  [Console]::Write($dialog.SelectedPath)
}
"""


def _file_picker_script() -> str:
    return r"""
Add-Type -AssemblyName System.Windows.Forms
[System.Windows.Forms.Application]::EnableVisualStyles()
$dialog = New-Object System.Windows.Forms.OpenFileDialog
$dialog.Filter = 'Excel Files (*.xlsx;*.xlsm;*.xltx;*.xltm)|*.xlsx;*.xlsm;*.xltx;*.xltm'
$directory = $env:EPA_PICKER_DIRECTORY
if ($directory) {
  if (Test-Path $directory -PathType Container) {
    $dialog.InitialDirectory = $directory
  } elseif (Test-Path $directory -PathType Leaf) {
    $dialog.InitialDirectory = Split-Path $directory -Parent
    $dialog.FileName = Split-Path $directory -Leaf
  }
}
$result = $dialog.ShowDialog()
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
if ($result -eq [System.Windows.Forms.DialogResult]::OK) {
  [Console]::Write($dialog.FileName)
}
"""
