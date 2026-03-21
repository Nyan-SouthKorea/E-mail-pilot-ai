"""reference fixture 이메일을 실제 MailBundle 구조로 풀어놓는 smoke."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from project_paths import ProfilePaths, default_example_profile_root

from .bundle_storage import build_mail_bundle_id, build_mail_bundle_paths
from .fixture_reference import (
    build_fixture_preview_html,
    build_fixture_surrogate_eml,
    extract_fixture_body,
    extract_fixture_header,
    find_fixture_attachment_dir,
    parse_fixture_address,
    read_fixture_email_text,
)
from .schema import Address, BodyPart, MailBundle, NormalizedMessage, StoredArtifact


@dataclass(slots=True)
class FixtureMaterializeResult:
    """기능: fixture 1건 materialize 결과를 표현한다.

    입력:
    - fixture_id: 처리한 fixture 이름
    - bundle_id: 생성한 bundle id
    - bundle_root: 생성된 bundle 루트 경로
    - normalized_json_path: 생성된 normalized.json 경로
    - attachment_count: 복사한 첨부 개수
    - notes: 보조 메모

    반환:
    - dataclass 인스턴스
    """

    fixture_id: str
    bundle_id: str
    bundle_root: str
    normalized_json_path: str
    attachment_count: int
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        """기능: 결과를 JSON 직렬화용 dict로 바꾼다.

        입력:
        - 없음

        반환:
        - dict
        """

        return asdict(self)


def list_fixture_directories(profile_root: str) -> list[Path]:
    """기능: 프로필 아래 fixture 이메일 디렉토리 목록을 반환한다.

    입력:
    - profile_root: 사용자 프로필 루트 경로

    반환:
    - fixture 디렉토리 목록
    """

    fixture_root = ProfilePaths(profile_root).fixture_examples_root()
    return [
        path
        for path in sorted(fixture_root.iterdir())
        if path.is_dir() and path.name.startswith("수신 이메일")
    ]


def run_fixture_mailbundle_materialize_smoke(profile_root: str) -> list[FixtureMaterializeResult]:
    """기능: fixture 이메일들을 실제 MailBundle 구조로 materialize 한다.

    입력:
    - profile_root: 사용자 프로필 루트 경로

    반환:
    - fixture별 materialize 결과 목록
    """

    results: list[FixtureMaterializeResult] = []
    for fixture_dir in list_fixture_directories(profile_root):
        results.append(materialize_fixture_mail_bundle(str(fixture_dir), profile_root))
    return results


def materialize_fixture_mail_bundle(fixture_dir: str, profile_root: str) -> FixtureMaterializeResult:
    """기능: fixture 1건을 실제 MailBundle 폴더 구조로 만든다.

    입력:
    - fixture_dir: fixture 이메일 디렉토리 경로
    - profile_root: 사용자 프로필 루트 경로

    반환:
    - `FixtureMaterializeResult`
    """

    fixture_path = Path(fixture_dir)
    profile_paths = ProfilePaths(profile_root)
    profile_paths.ensure_runtime_dirs()

    raw_text = read_fixture_email_text(fixture_path)
    subject = extract_fixture_header(raw_text, "제목")
    sender_raw = extract_fixture_header(raw_text, "보낸사람")
    recipient_raw = extract_fixture_header(raw_text, "받는사람")
    body_text = extract_fixture_body(raw_text)

    fixture_timestamp = _fixture_timestamp(fixture_path)
    bundle_id = build_mail_bundle_id(
        received_at=fixture_timestamp,
        message_key=f"fixture-materialized:{fixture_path.name}",
    )
    bundle_paths = build_mail_bundle_paths(profile_root, bundle_id)
    bundle_root = Path(bundle_paths.root_dir)
    if bundle_root.exists():
        shutil.rmtree(bundle_root)
    attachments_root = bundle_root / bundle_paths.attachments_dir
    attachments_root.mkdir(parents=True, exist_ok=True)

    preview_html = build_fixture_preview_html(
        subject=subject,
        sender=sender_raw,
        recipient=recipient_raw,
        body_text=body_text,
    )
    surrogate_eml = build_fixture_surrogate_eml(
        subject=subject,
        sender=sender_raw,
        recipient=recipient_raw,
        body_text=body_text,
        fixture_id=fixture_path.name,
    )

    (bundle_root / bundle_paths.raw_eml_path).write_text(surrogate_eml, encoding="utf-8")
    (bundle_root / bundle_paths.preview_html_path).write_text(preview_html, encoding="utf-8")

    sender_name, sender_email = parse_fixture_address(sender_raw)
    recipient_name, recipient_email = parse_fixture_address(recipient_raw)

    artifacts = _copy_fixture_attachments(
        fixture_dir=fixture_path,
        attachments_root=attachments_root,
    )

    bundle = MailBundle(
        bundle_id=bundle_id,
        provider="fixture",
        account_id="fixture-profile",
        folder="reference_fixture",
        fetched_at=_utc_now_iso(),
        from_address=Address(email=sender_email, name=sender_name),
        paths=bundle_paths,
        internet_message_id=f"<fixture:{fixture_path.name}>",
        remote_message_id=f"fixture:{fixture_path.name}",
        remote_thread_id=f"fixture:{fixture_path.name}",
        subject=subject,
        sent_at=fixture_timestamp,
        received_at=fixture_timestamp,
        to=[Address(email=recipient_email, name=recipient_name)] if recipient_email else [],
        body_parts=[
            BodyPart(
                part_id="body_text",
                mime_type="text/plain",
                content=body_text,
                is_primary=True,
            ),
            BodyPart(
                part_id="body_html",
                mime_type="text/html",
                content=preview_html,
                content_path=bundle_paths.preview_html_path,
                is_primary=True,
            ),
        ],
        artifacts=artifacts,
        headers={
            "subject": subject,
            "from": sender_raw,
            "to": recipient_raw,
            "x-fixture-source": fixture_path.name,
        },
        labels=["fixture_materialized"],
    )
    normalized = NormalizedMessage.from_bundle(bundle)

    normalized_path = bundle_root / bundle_paths.normalized_json_path
    normalized_path.write_text(
        json.dumps(normalized.to_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    summary_md = _build_fixture_summary_markdown(
        fixture_id=fixture_path.name,
        subject=subject,
        sender=sender_raw,
        recipient=recipient_raw,
        body_text=body_text,
        artifacts=artifacts,
    )
    (bundle_root / bundle_paths.summary_md_path).write_text(summary_md, encoding="utf-8")

    return FixtureMaterializeResult(
        fixture_id=fixture_path.name,
        bundle_id=bundle_id,
        bundle_root=str(bundle_root),
        normalized_json_path=str(normalized_path),
        attachment_count=len(artifacts),
        notes=["reference fixture를 runtime MailBundle 구조로 materialize 했다."],
    )


def _copy_fixture_attachments(
    *,
    fixture_dir: Path,
    attachments_root: Path,
) -> list[StoredArtifact]:
    attachment_dir = find_fixture_attachment_dir(fixture_dir)
    if attachment_dir is None:
        return []

    artifacts: list[StoredArtifact] = []
    for index, source_path in enumerate(sorted(attachment_dir.iterdir()), start=1):
        if not source_path.is_file():
            continue
        target_path = attachments_root / source_path.name
        shutil.copy2(source_path, target_path)
        artifacts.append(
            StoredArtifact(
                artifact_id=f"attachment_{index}",
                role="attachment",
                filename=source_path.name,
                media_type=_guess_media_type(source_path),
                relative_path=f"attachments/{source_path.name}",
                size_bytes=target_path.stat().st_size,
                sha256=_sha256_of_file(target_path),
            )
        )
    return artifacts


def _build_fixture_summary_markdown(
    *,
    fixture_id: str,
    subject: str,
    sender: str,
    recipient: str,
    body_text: str,
    artifacts: list[StoredArtifact],
) -> str:
    lines = [
        f"# {fixture_id}",
        "",
        "## 메일 요약",
        f"- 제목: {subject}",
        f"- 보낸사람: {sender}",
        f"- 받는사람: {recipient}",
        "",
        "## 본문",
        body_text.strip() or "(본문 없음)",
        "",
        "## 첨부",
    ]
    if not artifacts:
        lines.append("- 없음")
    else:
        for artifact in artifacts:
            lines.append(f"- {artifact.filename} ({artifact.media_type})")
    return "\n".join(lines).strip() + "\n"


def _fixture_timestamp(fixture_dir: Path) -> str:
    email_text_path = fixture_dir / "이메일 내용.txt"
    stat = email_text_path.stat()
    return datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat()


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _guess_media_type(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".zip":
        return "application/zip"
    if suffix == ".xlsx":
        return "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    if suffix == ".pdf":
        return "application/pdf"
    if suffix in {".png", ".jpg", ".jpeg"}:
        return f"image/{suffix.lstrip('.')}"
    return "application/octet-stream"


def _sha256_of_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(65536)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def default_profile_root() -> Path:
    """기능: 현재 예시 사용자 프로필 루트 기본 경로를 반환한다.

    입력:
    - 없음

    반환:
    - `secrets/사용자 설정/김정민`
    """

    return default_example_profile_root()


def main() -> None:
    """기능: CLI에서 fixture materialize smoke를 실행한다.

    입력:
    - 없음

    반환:
    - 없음
    """

    parser = argparse.ArgumentParser(description="fixture mailbundle materialize smoke")
    parser.add_argument("--profile-root", default=str(default_profile_root()))
    args = parser.parse_args()

    results = run_fixture_mailbundle_materialize_smoke(args.profile_root)
    print(json.dumps([item.to_dict() for item in results], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
