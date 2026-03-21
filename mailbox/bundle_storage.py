"""사용자 프로필 기준의 메일 번들 저장 레이아웃을 만든다."""

from __future__ import annotations

from datetime import datetime
from hashlib import sha1
from pathlib import Path

from project_paths import ProfilePaths

from .schema import MailBundlePaths


def build_mail_bundle_id(
    *,
    received_at: str | None = None,
    message_key: str = "",
    fallback_label: str = "message",
) -> str:
    """기능: ASCII 기반 메일 번들 폴더 id를 만든다.

    입력:
    - received_at: ISO 시각 문자열 또는 비어 있는 값
    - message_key: message-id, fixture id 같은 식별값
    - fallback_label: message_key가 없을 때 쓸 보조 라벨

    반환:
    - `YYYYMMDD_HHMMSS_msg_ab12cd34` 형식 id
    """

    timestamp = _normalize_timestamp(received_at)
    digest_source = message_key.strip() or fallback_label.strip() or "message"
    digest = sha1(digest_source.encode("utf-8")).hexdigest()[:8]
    return f"{timestamp}_msg_{digest}"


def build_mail_bundle_paths(profile_root: str, bundle_id: str) -> MailBundlePaths:
    """기능: 프로필 기준 메일 번들 표준 경로 정보를 만든다.

    입력:
    - profile_root: `secrets/사용자 설정/<이름>` 루트
    - bundle_id: 메일 번들 폴더 id

    반환:
    - `MailBundlePaths`
    """

    profile_paths = ProfilePaths(profile_root)
    bundle_root = profile_paths.runtime_mail_bundles_root() / bundle_id
    return MailBundlePaths(root_dir=str(bundle_root))


def create_mail_bundle_skeleton(profile_root: str, bundle_id: str) -> MailBundlePaths:
    """기능: 메일 번들 최소 파일 구조를 실제 디렉토리에 만든다.

    입력:
    - profile_root: `secrets/사용자 설정/<이름>` 루트
    - bundle_id: 메일 번들 폴더 id

    반환:
    - 생성된 번들의 `MailBundlePaths`
    """

    profile_paths = ProfilePaths(profile_root)
    profile_paths.ensure_runtime_dirs()

    bundle_paths = build_mail_bundle_paths(profile_root, bundle_id)
    bundle_root = Path(bundle_paths.root_dir)
    attachments_dir = bundle_root / bundle_paths.attachments_dir

    bundle_root.mkdir(parents=True, exist_ok=True)
    attachments_dir.mkdir(parents=True, exist_ok=True)
    _write_placeholder_file(bundle_root / bundle_paths.raw_eml_path, "")
    _write_placeholder_file(
        bundle_root / bundle_paths.preview_html_path,
        (
            "<!doctype html>\n"
            "<html lang=\"ko\">\n"
            "<head><meta charset=\"utf-8\"><title>Mail Preview</title></head>\n"
            "<body><p>preview placeholder</p></body>\n"
            "</html>\n"
        ),
    )
    _write_placeholder_file(
        bundle_root / bundle_paths.normalized_json_path,
        "{\n  \"status\": \"placeholder\"\n}\n",
    )
    _write_placeholder_file(
        bundle_root / bundle_paths.summary_md_path,
        "# Summary\n\nplaceholder\n",
    )
    return bundle_paths


def _normalize_timestamp(received_at: str | None) -> str:
    value = (received_at or "").strip()
    if value:
        normalized = value.replace("Z", "+00:00")
        try:
            parsed = datetime.fromisoformat(normalized)
            return parsed.strftime("%Y%m%d_%H%M%S")
        except ValueError:
            pass
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def _write_placeholder_file(path: Path, content: str) -> None:
    if not path.exists():
        path.write_text(content, encoding="utf-8")
