"""runtime MailBundle 디렉토리를 다시 읽는 helper."""

from __future__ import annotations

import json
from pathlib import Path

from project_paths import ProfilePaths

from .schema import NORMALIZED_MESSAGE_SCHEMA_VERSION, NormalizedMessage


def list_valid_runtime_bundle_directories(profile_root: str) -> list[Path]:
    """기능: 현재 프로필 아래의 유효한 runtime bundle 디렉토리 목록을 반환한다.

    입력:
    - profile_root: 사용자 프로필 루트 경로

    반환:
    - `normalized.json`이 유효한 bundle 디렉토리 목록
    """

    bundles_root = ProfilePaths(profile_root).runtime_mail_bundles_root()
    if not bundles_root.exists():
        return []

    directories: list[Path] = []
    for path in sorted(bundles_root.iterdir()):
        if not path.is_dir():
            continue
        if is_valid_runtime_bundle_directory(path):
            directories.append(path)
    return directories


def is_valid_runtime_bundle_directory(bundle_root: str | Path) -> bool:
    """기능: 주어진 bundle 디렉토리가 유효한 runtime bundle인지 확인한다.

    입력:
    - bundle_root: bundle 루트 디렉토리 경로

    반환:
    - `normalized.json` schema가 현재 버전이면 `True`
    """

    return _is_valid_normalized_bundle(Path(bundle_root))


def load_normalized_message_from_bundle(bundle_root: str | Path) -> NormalizedMessage:
    """기능: bundle 디렉토리의 `normalized.json`을 `NormalizedMessage`로 복원한다.

    입력:
    - bundle_root: bundle 루트 디렉토리 경로

    반환:
    - `NormalizedMessage`
    """

    root = Path(bundle_root)
    payload = json.loads((root / "normalized.json").read_text(encoding="utf-8"))
    return NormalizedMessage.from_dict(payload)


def list_bundle_attachment_files(bundle_root: str | Path) -> list[Path]:
    """기능: bundle 디렉토리의 첨부 파일 경로 목록을 반환한다.

    입력:
    - bundle_root: bundle 루트 디렉토리 경로

    반환:
    - 첨부 파일 `Path` 목록
    """

    attachments_dir = Path(bundle_root) / "attachments"
    if not attachments_dir.exists():
        return []
    return [path for path in sorted(attachments_dir.iterdir()) if path.is_file()]


def _is_valid_normalized_bundle(bundle_root: Path) -> bool:
    normalized_path = bundle_root / "normalized.json"
    if not normalized_path.exists():
        return False

    try:
        payload = json.loads(normalized_path.read_text(encoding="utf-8"))
    except Exception:
        return False

    return payload.get("schema_version") == NORMALIZED_MESSAGE_SCHEMA_VERSION
