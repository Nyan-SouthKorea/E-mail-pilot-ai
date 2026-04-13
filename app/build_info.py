"""앱 빌드 메타데이터를 읽는 helper."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
import json
from pathlib import Path
import subprocess
import sys


@dataclass(slots=True)
class BuildInfo:
    build_commit: str
    build_time: str
    official_exe_path: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


def load_build_info(*, official_exe_path: str) -> BuildInfo:
    """기능: 현재 실행본 또는 source tree 기준 빌드 메타데이터를 읽는다."""

    bundled = _load_bundled_build_info()
    if bundled is not None:
        if not bundled.official_exe_path:
            bundled.official_exe_path = official_exe_path
        return bundled
    return BuildInfo(
        build_commit=_git_head_commit(),
        build_time=datetime.now().isoformat(timespec="seconds"),
        official_exe_path=official_exe_path,
    )


def _load_bundled_build_info() -> BuildInfo | None:
    if not getattr(sys, "frozen", False):
        return None
    executable_dir = Path(sys.executable).resolve().parent
    build_info_path = executable_dir / "portable_build_info.json"
    if not build_info_path.exists():
        return None
    try:
        payload = json.loads(build_info_path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return BuildInfo(
        build_commit=str(payload.get("build_commit") or ""),
        build_time=str(payload.get("build_time") or ""),
        official_exe_path=str(payload.get("official_exe_path") or ""),
    )


def _git_head_commit() -> str:
    repo_root = Path(__file__).resolve().parents[1]
    try:
        return subprocess.check_output(
            ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
            text=True,
        ).strip()
    except Exception:
        return ""
