"""공유 워크스페이스 밖에 남는 로컬 UI 설정을 관리한다."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
import os
from pathlib import Path


@dataclass(slots=True)
class LocalAppSettings:
    """기능: 로컬 장치 전용 앱 설정을 표현한다."""

    recent_workspaces: list[str] = field(default_factory=list)
    last_open_workspace: str = ""
    window_width: int = 1360
    window_height: int = 920
    last_review_filters: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> "LocalAppSettings":
        return cls(
            recent_workspaces=list(payload.get("recent_workspaces") or []),
            last_open_workspace=str(payload.get("last_open_workspace") or ""),
            window_width=int(payload.get("window_width") or 1360),
            window_height=int(payload.get("window_height") or 920),
            last_review_filters=dict(payload.get("last_review_filters") or {}),
        )


def default_local_settings_path() -> Path:
    """기능: 현재 OS 기준 로컬 전용 설정 파일 경로를 반환한다."""

    if os.name == "nt":
        appdata = Path(os.environ.get("APPDATA") or Path.home() / "AppData" / "Roaming")
        return appdata / "EmailPilotAI" / "local_settings.json"
    return Path.home() / ".config" / "email-pilot-ai" / "local_settings.json"


def default_startup_log_path() -> Path:
    """기능: 데스크톱 런처 startup log의 기본 경로를 반환한다."""

    if os.name == "nt":
        appdata = Path(os.environ.get("APPDATA") or Path.home() / "AppData" / "Roaming")
        return appdata / "EmailPilotAI" / "startup.log"
    return Path.home() / ".config" / "email-pilot-ai" / "startup.log"


def default_local_portable_bundle_root() -> Path:
    """기능: 공식 Windows 로컬 portable bundle 루트를 반환한다."""

    if os.name == "nt":
        return Path("D:/EmailPilotAI/portable/EmailPilotAI")
    return Path.home() / ".local" / "share" / "email-pilot-ai" / "portable" / "EmailPilotAI"


def default_local_portable_exe_path() -> Path:
    """기능: 공식 Windows 로컬 portable exe 경로를 반환한다."""

    return default_local_portable_bundle_root() / "EmailPilotAI.exe"


def load_local_app_settings(path: str | Path | None = None) -> LocalAppSettings:
    """기능: 로컬 장치 전용 설정을 읽는다."""

    settings_path = Path(path or default_local_settings_path())
    if not settings_path.exists():
        return LocalAppSettings()
    payload = json.loads(settings_path.read_text(encoding="utf-8"))
    return LocalAppSettings.from_dict(payload)


def save_local_app_settings(
    settings: LocalAppSettings,
    path: str | Path | None = None,
) -> Path:
    """기능: 로컬 장치 전용 설정을 저장한다."""

    settings_path = Path(path or default_local_settings_path())
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    settings_path.write_text(
        json.dumps(settings.to_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return settings_path


def remember_workspace(
    workspace_root: str,
    *,
    path: str | Path | None = None,
) -> LocalAppSettings:
    """기능: 최근 연 워크스페이스 목록과 마지막 경로를 갱신한다."""

    settings = load_local_app_settings(path)
    resolved = str(Path(workspace_root))
    recent = [item for item in settings.recent_workspaces if item != resolved]
    recent.insert(0, resolved)
    settings.recent_workspaces = recent[:10]
    settings.last_open_workspace = resolved
    save_local_app_settings(settings, path)
    return settings
