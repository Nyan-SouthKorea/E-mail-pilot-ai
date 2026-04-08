"""실제 계정으로 auth probe 후 최신 메일 1건을 bundle로 저장하는 smoke."""

from __future__ import annotations

import argparse
import json
import mimetypes
import re
import shutil
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from email import policy
from email.parser import BytesParser
from email.utils import getaddresses, parsedate_to_datetime
from hashlib import sha256
from html import escape, unescape
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from project_paths import ProfilePaths, default_example_profile_root

if __package__ in (None, ""):
    from mailbox.autoconfig import (
        MailServerCandidate,
        MailboxAutoConfigSmokeReport,
        run_mailbox_autoconfig_smoke,
        save_mailbox_autoconfig_report,
    )
    from mailbox.bundle_storage import build_mail_bundle_id, build_mail_bundle_paths
    from mailbox.local_account_config import (
        default_local_account_config_path,
        load_local_mailbox_account_config,
    )
    from mailbox.schema import Address, BodyPart, MailBundle, NormalizedMessage, StoredArtifact
else:
    from .autoconfig import (
        MailServerCandidate,
        MailboxAutoConfigSmokeReport,
        run_mailbox_autoconfig_smoke,
        save_mailbox_autoconfig_report,
    )
    from .bundle_storage import build_mail_bundle_id, build_mail_bundle_paths
    from .local_account_config import (
        default_local_account_config_path,
        load_local_mailbox_account_config,
    )
    from .schema import Address, BodyPart, MailBundle, NormalizedMessage, StoredArtifact

import imaplib
import ssl


@dataclass(slots=True)
class FetchedImapMessage:
    """기능: IMAP에서 읽어온 메일 1건을 표현한다."""

    folder: str
    uid: str
    raw_bytes: bytes
    internal_date: str | None = None


@dataclass(slots=True)
class MaterializedFetchedMailResult:
    """기능: fetched message를 bundle로 저장한 결과를 표현한다."""

    bundle_id: str
    bundle_root: str
    normalized_json_path: str
    attachment_count: int
    has_text_body: bool
    has_html_body: bool
    remote_message_id: str


@dataclass(slots=True)
class MailboxImapFetchSmokeReport:
    """기능: 실제 계정 IMAP fetch smoke 전체 결과를 표현한다."""

    email_address: str
    login_username_kind: str
    auth_report_path: str
    success: bool
    selected_candidate: dict[str, object] | None
    folder: str
    fetched_uid: str | None = None
    fetched_remote_message_id: str | None = None
    saved_bundle_path: str | None = None
    normalized_json_path: str | None = None
    attachment_count: int = 0
    has_text_body: bool = False
    has_html_body: bool = False
    failure_message: str = ""
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def default_profile_root() -> Path:
    """기능: 현재 예시 사용자 프로필 루트 기본 경로를 반환한다."""

    return default_example_profile_root()


def default_fetch_report_path(profile_root: str, email_address: str) -> Path:
    """기능: IMAP fetch smoke report 기본 저장 경로를 만든다."""

    profile_paths = ProfilePaths(profile_root)
    return profile_paths.runtime_mailbox_logs_root() / f"{_safe_email_name(email_address)}_imap_fetch_smoke.json"


def default_autoconfig_report_path(profile_root: str, email_address: str) -> Path:
    """기능: auth probe report 기본 저장 경로를 만든다."""

    profile_paths = ProfilePaths(profile_root)
    return profile_paths.runtime_mailbox_logs_root() / f"{_safe_email_name(email_address)}_autoconfig_smoke.json"


def run_imap_latest_mail_fetch_smoke(
    *,
    credentials_path: str | Path | None = None,
    profile_root: str | Path | None = None,
    account_config=None,
    folder: str = "INBOX",
    timeout_seconds: float = 8.0,
    max_probes_per_protocol: int = 2,
) -> MailboxImapFetchSmokeReport:
    """기능: 실제 계정 정보로 auth probe 후 최신 메일 1건을 bundle로 저장한다."""

    config = account_config or load_local_mailbox_account_config(
        credentials_path=credentials_path,
        profile_root=profile_root,
    )
    profile_paths = ProfilePaths(config.profile_root)
    profile_paths.ensure_runtime_dirs()

    auth_report = run_mailbox_autoconfig_smoke(
        email_address=config.email_address,
        login_username=config.login_username,
        password=config.password,
        timeout_seconds=timeout_seconds,
        max_probes_per_protocol=max_probes_per_protocol,
    )
    auth_report_path = save_mailbox_autoconfig_report(
        auth_report,
        default_autoconfig_report_path(config.profile_root, config.email_address),
    )

    notes = list(config.notes) + list(auth_report.notes)
    selected_candidate = choose_successful_imap_candidate(auth_report)
    if selected_candidate is None:
        report = MailboxImapFetchSmokeReport(
            email_address=config.email_address,
            login_username_kind=auth_report.login_username_kind,
            auth_report_path=str(auth_report_path),
            success=False,
            selected_candidate=None,
            folder=folder,
            failure_message="로그인 성공한 IMAP 후보가 없어 latest fetch를 진행하지 않았다.",
            notes=notes,
        )
        return save_imap_fetch_report(
            report,
            default_fetch_report_path(config.profile_root, config.email_address),
        )

    successful_login_username_kind = resolve_successful_imap_login_username_kind(
        report=auth_report,
        candidate=selected_candidate,
        explicit_login_username=config.login_username,
        email_address=config.email_address,
    )

    try:
        fetched = fetch_latest_imap_message(
            candidate=selected_candidate,
            login_username=resolve_successful_imap_login_username(
                report=auth_report,
                candidate=selected_candidate,
                explicit_login_username=config.login_username,
                email_address=config.email_address,
            ),
            password=config.password,
            folder=folder,
            timeout_seconds=timeout_seconds,
        )
        materialized = materialize_fetched_imap_message(
            fetched_message=fetched,
            profile_root=config.profile_root,
            provider=auth_report.plan.provider_key,
            account_id=config.email_address,
        )
        report = MailboxImapFetchSmokeReport(
            email_address=config.email_address,
            login_username_kind=successful_login_username_kind,
            auth_report_path=str(auth_report_path),
            success=True,
            selected_candidate=selected_candidate.to_dict(),
            folder=fetched.folder,
            fetched_uid=fetched.uid,
            fetched_remote_message_id=materialized.remote_message_id,
            saved_bundle_path=materialized.bundle_root,
            normalized_json_path=materialized.normalized_json_path,
            attachment_count=materialized.attachment_count,
            has_text_body=materialized.has_text_body,
            has_html_body=materialized.has_html_body,
            notes=notes,
        )
    except Exception as exc:
        report = MailboxImapFetchSmokeReport(
            email_address=config.email_address,
            login_username_kind=successful_login_username_kind,
            auth_report_path=str(auth_report_path),
            success=False,
            selected_candidate=selected_candidate.to_dict(),
            folder=folder,
            failure_message=f"{exc.__class__.__name__}: {exc}",
            notes=notes,
        )

    return save_imap_fetch_report(
        report,
        default_fetch_report_path(config.profile_root, config.email_address),
    )


def choose_successful_imap_candidate(
    report: MailboxAutoConfigSmokeReport,
) -> MailServerCandidate | None:
    """기능: auth probe에 성공한 IMAP 후보를 고른다."""

    success_keys = {
        (item.protocol, item.host, item.port, item.security)
        for item in report.probe_results
        if item.success and item.protocol == "imap"
    }
    if not success_keys:
        return None

    recommended = report.recommended_incoming
    if recommended is not None and recommended.protocol == "imap" and recommended.key() in success_keys:
        return recommended

    for candidate in report.plan.imap_candidates:
        if candidate.key() in success_keys:
            return candidate
    return None


def resolve_successful_imap_login_username(
    *,
    report: MailboxAutoConfigSmokeReport,
    candidate: MailServerCandidate,
    explicit_login_username: str,
    email_address: str,
) -> str:
    """기능: 성공한 IMAP 후보에서 실제로 먹힌 로그인 username을 고른다."""

    for item in report.probe_results:
        if not item.success or item.protocol != "imap":
            continue
        if (item.protocol, item.host, item.port, item.security) != candidate.key():
            continue
        if item.login_username_kind == "email_address_fallback":
            return email_address
        if item.login_username_kind == "explicit_login_username":
            return explicit_login_username or email_address
    if report.login_username_kind in {
        "email_address_fallback",
        "email_address_after_explicit_failure",
    }:
        return email_address
    return explicit_login_username or email_address


def resolve_successful_imap_login_username_kind(
    *,
    report: MailboxAutoConfigSmokeReport,
    candidate: MailServerCandidate,
    explicit_login_username: str,
    email_address: str,
) -> str:
    """기능: 성공한 IMAP 후보 기준 실제 유효했던 로그인 username 종류를 반환한다."""

    successful_username = resolve_successful_imap_login_username(
        report=report,
        candidate=candidate,
        explicit_login_username=explicit_login_username,
        email_address=email_address,
    )
    if successful_username.strip() == email_address.strip():
        if explicit_login_username.strip() and explicit_login_username.strip() != email_address.strip():
            return "email_address_after_explicit_failure"
        return "email_address_fallback"
    return "explicit_login_username"


def fetch_latest_imap_message(
    *,
    candidate: MailServerCandidate,
    login_username: str,
    password: str,
    folder: str,
    timeout_seconds: float,
) -> FetchedImapMessage:
    """기능: IMAP INBOX에서 최신 메일 1건을 read-only로 가져온다."""

    client = _open_logged_in_imap_client(
        candidate=candidate,
        login_username=login_username,
        password=password,
        timeout_seconds=timeout_seconds,
    )
    try:
        uid_list = list_imap_message_uids(client=client, folder=folder)
        if not uid_list:
            raise RuntimeError("INBOX에 가져올 메일이 없다.")
        return fetch_imap_message_by_uid(client=client, uid=uid_list[-1], folder=folder)
    finally:
        try:
            client.logout()
        except Exception:
            pass


def list_imap_message_uids(
    *,
    client,
    folder: str,
) -> list[str]:
    """기능: 지정 폴더의 UID 목록을 read-only로 읽는다."""

    status, _ = client.select(folder, readonly=True)
    if status != "OK":
        raise RuntimeError(f"IMAP 폴더를 read-only로 열지 못했다: {folder}")

    status, data = client.uid("search", None, "ALL")
    if status != "OK":
        raise RuntimeError("IMAP UID SEARCH ALL이 실패했다.")

    uid_blob = b"".join(item for item in data if isinstance(item, bytes)).strip()
    if not uid_blob:
        return []

    return [
        item.decode("utf-8", errors="replace")
        for item in uid_blob.split()
        if item
    ]


def fetch_imap_message_by_uid(
    *,
    client,
    uid: str,
    folder: str,
) -> FetchedImapMessage:
    """기능: UID 하나를 BODY.PEEK 기준으로 read-only fetch한다."""

    status, fetch_data = client.uid(
        "fetch",
        uid,
        "(UID BODY.PEEK[] FLAGS INTERNALDATE)",
    )
    if status != "OK":
        raise RuntimeError(f"UID {uid} fetch가 실패했다.")

    raw_bytes, internal_date = _extract_imap_fetch_payload(fetch_data)
    if not raw_bytes:
        raise RuntimeError(f"UID {uid}에서 RFC822 원문을 읽지 못했다.")

    return FetchedImapMessage(
        folder=folder,
        uid=uid,
        raw_bytes=raw_bytes,
        internal_date=internal_date,
    )


def materialize_fetched_imap_message(
    *,
    fetched_message: FetchedImapMessage,
    profile_root: str,
    provider: str,
    account_id: str,
    labels: list[str] | None = None,
) -> MaterializedFetchedMailResult:
    """기능: fetched IMAP message를 runtime bundle 구조로 저장한다."""

    profile_paths = ProfilePaths(profile_root)
    profile_paths.ensure_runtime_dirs()

    message = BytesParser(policy=policy.default).parsebytes(fetched_message.raw_bytes)

    internet_message_id = str(message.get("Message-ID") or "").strip()
    sent_at = _normalize_header_datetime(message.get("Date"))
    received_at = fetched_message.internal_date or sent_at or _utc_now_iso()
    bundle_id = predict_bundle_id_for_fetched_imap_message(fetched_message=fetched_message)
    bundle_paths = build_mail_bundle_paths(profile_root, bundle_id)
    bundle_root = Path(bundle_paths.root_dir)
    attachments_root = bundle_root / bundle_paths.attachments_dir

    bundle_root.mkdir(parents=True, exist_ok=True)
    if attachments_root.exists():
        shutil.rmtree(attachments_root)
    attachments_root.mkdir(parents=True, exist_ok=True)

    subject = str(message.get("Subject") or "").strip()
    from_addresses = _parse_addresses(message.get_all("From", []))
    to_addresses = _parse_addresses(message.get_all("To", []))
    cc_addresses = _parse_addresses(message.get_all("Cc", []))
    bcc_addresses = _parse_addresses(message.get_all("Bcc", []))
    reply_to_addresses = _parse_addresses(message.get_all("Reply-To", []))

    body_parts, artifacts = _extract_message_parts(
        message=message,
        attachments_root=attachments_root,
        preview_relative_path=bundle_paths.preview_html_path,
    )
    body_text = _primary_body_content(body_parts, "text/plain")
    body_html = _primary_body_content(body_parts, "text/html")
    if not body_text and body_html:
        body_text = _html_to_text(body_html)
        body_parts.append(
            BodyPart(
                part_id="body_text_from_html",
                mime_type="text/plain",
                content=body_text,
                is_primary=True,
            )
        )

    preview_html = build_message_preview_html(
        subject=subject,
        sender=", ".join(_format_address(item) for item in from_addresses),
        recipient=", ".join(_format_address(item) for item in to_addresses),
        body_text=body_text,
        body_html=body_html,
    )

    (bundle_root / bundle_paths.raw_eml_path).write_bytes(fetched_message.raw_bytes)
    (bundle_root / bundle_paths.preview_html_path).write_text(preview_html, encoding="utf-8")

    bundle = MailBundle(
        bundle_id=bundle_id,
        provider=provider,
        account_id=account_id,
        folder=fetched_message.folder,
        fetched_at=_utc_now_iso(),
        from_address=from_addresses[0] if from_addresses else Address(email=""),
        paths=bundle_paths,
        internet_message_id=internet_message_id,
        remote_message_id=fetched_message.uid,
        remote_thread_id=_extract_thread_key(message),
        subject=subject,
        sent_at=sent_at,
        received_at=received_at,
        reply_to=reply_to_addresses,
        to=to_addresses,
        cc=cc_addresses,
        bcc=bcc_addresses,
        body_parts=body_parts,
        artifacts=artifacts,
        headers=_extract_header_snapshot(message),
        labels=list(labels or ["imap_latest_fetch_smoke"]),
    )
    normalized = NormalizedMessage.from_bundle(bundle)

    normalized_path = bundle_root / bundle_paths.normalized_json_path
    normalized_path.write_text(
        json.dumps(normalized.to_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (bundle_root / bundle_paths.summary_md_path).write_text(
        build_mailbox_summary_markdown(
            subject=subject,
            sender=_format_address(bundle.from_address),
            recipient=", ".join(_format_address(item) for item in to_addresses),
            body_text=body_text,
            artifacts=artifacts,
        ),
        encoding="utf-8",
    )

    return MaterializedFetchedMailResult(
        bundle_id=bundle_id,
        bundle_root=str(bundle_root),
        normalized_json_path=str(normalized_path),
        attachment_count=len(artifacts),
        has_text_body=bool(body_text.strip()),
        has_html_body=bool(body_html.strip()),
        remote_message_id=fetched_message.uid,
    )


def predict_bundle_id_for_fetched_imap_message(
    *,
    fetched_message: FetchedImapMessage,
) -> str:
    """기능: fetched message를 실제 저장 전에 동일 규칙 bundle id로 계산한다."""

    message = BytesParser(policy=policy.default).parsebytes(fetched_message.raw_bytes)
    internet_message_id = str(message.get("Message-ID") or "").strip()
    sent_at = _normalize_header_datetime(message.get("Date"))
    received_at = fetched_message.internal_date or sent_at or _utc_now_iso()
    return build_mail_bundle_id(
        received_at=received_at,
        message_key=internet_message_id or f"imap-uid:{fetched_message.uid}",
    )


def save_imap_fetch_report(
    report: MailboxImapFetchSmokeReport,
    output_path: str | Path,
) -> MailboxImapFetchSmokeReport:
    """기능: IMAP fetch smoke 결과를 JSON 파일로 저장한다."""

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(report.to_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return report


def build_message_preview_html(
    *,
    subject: str,
    sender: str,
    recipient: str,
    body_text: str,
    body_html: str,
) -> str:
    """기능: fetched message 기준 preview.html을 만든다."""

    if body_html.strip():
        normalized_html = _wrap_html_fragment(body_html)
        return (
            "<!doctype html>\n"
            "<html lang=\"ko\">\n"
            "<head>\n"
            "  <meta charset=\"utf-8\">\n"
            "  <title>Mail Preview</title>\n"
            "  <style>body{font-family:'Malgun Gothic',sans-serif;line-height:1.6;margin:24px;} "
            ".meta{margin-bottom:20px;padding-bottom:12px;border-bottom:1px solid #ddd;} "
            ".label{font-weight:700;display:inline-block;min-width:72px;}</style>\n"
            "</head>\n"
            "<body>\n"
            "  <div class=\"meta\">\n"
            f"    <div><span class=\"label\">제목</span>{escape(subject)}</div>\n"
            f"    <div><span class=\"label\">보낸사람</span>{escape(sender)}</div>\n"
            f"    <div><span class=\"label\">받는사람</span>{escape(recipient)}</div>\n"
            "  </div>\n"
            f"  <div class=\"body\">{normalized_html}</div>\n"
            "</body>\n"
            "</html>\n"
        )

    escaped_body = escape(body_text or "(본문 없음)").replace("\n", "<br>\n")
    return (
        "<!doctype html>\n"
        "<html lang=\"ko\">\n"
        "<head>\n"
        "  <meta charset=\"utf-8\">\n"
        "  <title>Mail Preview</title>\n"
        "  <style>body{font-family:'Malgun Gothic',sans-serif;line-height:1.6;margin:24px;} "
        ".meta{margin-bottom:20px;padding-bottom:12px;border-bottom:1px solid #ddd;} "
        ".label{font-weight:700;display:inline-block;min-width:72px;}</style>\n"
        "</head>\n"
        "<body>\n"
        "  <div class=\"meta\">\n"
        f"    <div><span class=\"label\">제목</span>{escape(subject)}</div>\n"
        f"    <div><span class=\"label\">보낸사람</span>{escape(sender)}</div>\n"
        f"    <div><span class=\"label\">받는사람</span>{escape(recipient)}</div>\n"
        "  </div>\n"
        f"  <div class=\"body\">{escaped_body}</div>\n"
        "</body>\n"
        "</html>\n"
    )


def build_mailbox_summary_markdown(
    *,
    subject: str,
    sender: str,
    recipient: str,
    body_text: str,
    artifacts: list[StoredArtifact],
) -> str:
    """기능: mailbox 단계용 간단한 summary.md를 만든다."""

    preview_lines = [line.strip() for line in body_text.splitlines() if line.strip()]
    preview_text = "\n".join(preview_lines[:12]).strip() or "(본문 없음)"

    lines = [
        "# Mail Summary",
        "",
        "## 메일 요약",
        f"- 제목: {subject}",
        f"- 보낸사람: {sender}",
        f"- 받는사람: {recipient or '(없음)'}",
        f"- 첨부 개수: {len(artifacts)}",
        "",
        "## 본문 미리보기",
        preview_text,
        "",
        "## 첨부",
    ]
    if not artifacts:
        lines.append("- 없음")
    else:
        for artifact in artifacts:
            lines.append(f"- {artifact.filename} ({artifact.media_type})")
    return "\n".join(lines).strip() + "\n"


def _open_logged_in_imap_client(
    *,
    candidate: MailServerCandidate,
    login_username: str,
    password: str,
    timeout_seconds: float,
):
    if candidate.security == "ssl":
        client = imaplib.IMAP4_SSL(candidate.host, candidate.port, timeout=timeout_seconds)
    else:
        client = imaplib.IMAP4(candidate.host, candidate.port, timeout=timeout_seconds)
        if candidate.security == "starttls":
            client.starttls(ssl_context=ssl.create_default_context())
    client.login(login_username, password)
    return client


def _extract_imap_fetch_payload(
    fetch_data: list[object],
) -> tuple[bytes, str | None]:
    """기능: IMAP `UID FETCH` 응답에서 RFC822 원문과 INTERNALDATE를 추출한다."""

    raw_bytes = b""
    header_blobs: list[bytes] = []

    for item in fetch_data:
        if isinstance(item, tuple):
            for sub_item in item:
                if isinstance(sub_item, bytes):
                    if not raw_bytes and _looks_like_email_bytes(sub_item):
                        raw_bytes = sub_item
                    else:
                        header_blobs.append(sub_item)
            continue
        if isinstance(item, bytes):
            header_blobs.append(item)

    internal_date = None
    for header_blob in header_blobs:
        header_text = header_blob.decode("utf-8", errors="replace")
        internal_match = re.search(r'INTERNALDATE "([^"]+)"', header_text)
        if internal_match is not None:
            internal_date = _normalize_mail_datetime(internal_match.group(1))
            break

    return raw_bytes, internal_date


def _looks_like_email_bytes(payload: bytes) -> bool:
    """기능: bytes payload가 RFC822 원문처럼 보이는지 대략 판단한다."""

    if not payload:
        return False
    prefix = payload[:1024]
    lowered_prefix = prefix.lower()
    if b"\r\n" not in prefix:
        return False

    first_line = prefix.splitlines()[0].strip()
    if re.match(rb"^[A-Za-z0-9-]+:\s*", first_line):
        return True

    return any(
        token in lowered_prefix
        for token in [
            b"\r\nsubject:",
            b"\r\nfrom:",
            b"\r\nto:",
            b"\r\nmessage-id:",
            b"\r\nreceived:",
            b"\r\nreturn-path:",
            b"\r\ndelivered-to:",
            b"\r\nmime-version:",
        ]
    )


def _extract_message_parts(
    *,
    message,
    attachments_root: Path,
    preview_relative_path: str,
) -> tuple[list[BodyPart], list[StoredArtifact]]:
    body_parts: list[BodyPart] = []
    artifacts: list[StoredArtifact] = []
    used_filenames: set[str] = set()
    body_plain_index = 0
    body_html_index = 0
    artifact_index = 0

    for part in message.walk():
        if part.is_multipart():
            continue

        content_type = part.get_content_type()
        filename = part.get_filename()
        disposition = part.get_content_disposition()
        content_id = _normalize_content_id(part.get("Content-ID"))

        if content_type in {"text/plain", "text/html"} and disposition != "attachment" and not filename:
            content = _extract_text_content(part)
            if content_type == "text/plain":
                body_plain_index += 1
                part_id = f"body_text_{body_plain_index}"
                is_primary = body_plain_index == 1
            else:
                body_html_index += 1
                part_id = f"body_html_{body_html_index}"
                is_primary = body_html_index == 1

            body_parts.append(
                BodyPart(
                    part_id=part_id,
                    mime_type=content_type,
                    content=content,
                    charset=part.get_content_charset(),
                    content_path=preview_relative_path if content_type == "text/html" else None,
                    is_primary=is_primary,
                )
            )
            continue

        payload = part.get_payload(decode=True) or b""
        if not payload and not filename and disposition is None and not content_id:
            continue

        artifact_index += 1
        role = "inline" if disposition == "inline" or content_id else "attachment"
        artifact_filename = _build_artifact_filename(
            filename=filename,
            content_type=content_type,
            artifact_index=artifact_index,
            used_filenames=used_filenames,
        )
        target_path = attachments_root / artifact_filename
        target_path.write_bytes(payload)
        artifacts.append(
            StoredArtifact(
                artifact_id=f"{role}_{artifact_index}",
                role=role,
                filename=artifact_filename,
                media_type=content_type,
                relative_path=f"attachments/{artifact_filename}",
                size_bytes=target_path.stat().st_size,
                sha256=_sha256_of_file(target_path),
                content_id=content_id,
            )
        )

    return body_parts, artifacts


def _parse_addresses(values: list[str]) -> list[Address]:
    addresses: list[Address] = []
    for name, email_address in getaddresses(values):
        normalized_email = email_address.strip()
        if not normalized_email:
            continue
        normalized_name = name.strip().strip("'\"") or None
        addresses.append(Address(email=normalized_email, name=normalized_name))
    return addresses


def _format_address(address: Address) -> str:
    if address.name:
        return f"{address.name} <{address.email}>"
    return address.email


def _primary_body_content(body_parts: list[BodyPart], mime_type: str) -> str:
    for body_part in body_parts:
        if body_part.mime_type == mime_type and body_part.is_primary:
            return body_part.content
    for body_part in body_parts:
        if body_part.mime_type == mime_type:
            return body_part.content
    return ""


def _extract_text_content(part) -> str:
    try:
        content = part.get_content()
        if isinstance(content, str):
            return content
    except Exception:
        pass

    payload = part.get_payload(decode=True) or b""
    charset = part.get_content_charset() or "utf-8"
    try:
        return payload.decode(charset, errors="replace")
    except LookupError:
        return payload.decode("utf-8", errors="replace")


def _build_artifact_filename(
    *,
    filename: str | None,
    content_type: str,
    artifact_index: int,
    used_filenames: set[str],
) -> str:
    raw_filename = filename or f"artifact_{artifact_index}{_extension_for_content_type(content_type)}"
    sanitized = _sanitize_filename(raw_filename)
    candidate = sanitized
    counter = 2
    while candidate in used_filenames:
        stem = Path(sanitized).stem
        suffix = Path(sanitized).suffix
        candidate = f"{stem}_{counter}{suffix}"
        counter += 1
    used_filenames.add(candidate)
    return candidate


def _sanitize_filename(value: str) -> str:
    sanitized = re.sub(r"[^\w.\-()가-힣 ]+", "_", value).strip()
    sanitized = sanitized.replace("/", "_").replace("\\", "_")
    return sanitized or "artifact.bin"


def _extension_for_content_type(content_type: str) -> str:
    extension = mimetypes.guess_extension(content_type)
    return extension or ".bin"


def _normalize_content_id(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip().strip("<>").strip()
    return normalized or None


def _wrap_html_fragment(html_text: str) -> str:
    lower = html_text.lower()
    if "<html" in lower or "<body" in lower:
        return html_text
    return f"<div>{html_text}</div>"


def _html_to_text(html_text: str) -> str:
    text = re.sub(r"(?is)<(script|style).*?>.*?</\\1>", " ", html_text)
    text = re.sub(r"(?i)<br\\s*/?>", "\n", text)
    text = re.sub(r"(?i)</p\\s*>", "\n\n", text)
    text = re.sub(r"(?s)<[^>]+>", " ", text)
    text = unescape(text)
    text = re.sub(r"\r\n?", "\n", text)
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _extract_header_snapshot(message) -> dict[str, str]:
    snapshot: dict[str, str] = {}
    for header_name in [
        "Subject",
        "From",
        "To",
        "Cc",
        "Reply-To",
        "Date",
        "Message-ID",
        "In-Reply-To",
        "References",
        "Thread-Index",
    ]:
        value = message.get(header_name)
        if value:
            snapshot[header_name.lower()] = str(value)
    return snapshot


def _extract_thread_key(message) -> str | None:
    for header_name in ["Thread-Index", "References", "In-Reply-To"]:
        value = message.get(header_name)
        if value:
            return str(value).strip()
    return None


def _normalize_header_datetime(value: str | None) -> str | None:
    if not value:
        return None
    try:
        parsed = parsedate_to_datetime(value)
    except Exception:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).isoformat()


def _normalize_mail_datetime(value: str) -> str | None:
    try:
        parsed = parsedate_to_datetime(value)
    except Exception:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).isoformat()


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256_of_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(65536)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def _safe_email_name(email_address: str) -> str:
    return email_address.replace("@", "_at_").replace(".", "_")


def main() -> None:
    """기능: CLI에서 실제 계정 IMAP fetch smoke를 실행한다."""

    parser = argparse.ArgumentParser(description="real account latest IMAP fetch smoke")
    parser.add_argument(
        "--credentials-path",
        default=str(default_local_account_config_path()),
    )
    parser.add_argument("--profile-root", default=str(default_profile_root()))
    parser.add_argument("--folder", default="INBOX")
    parser.add_argument("--timeout-seconds", type=float, default=8.0)
    parser.add_argument("--max-probes-per-protocol", type=int, default=2)
    args = parser.parse_args()

    report = run_imap_latest_mail_fetch_smoke(
        credentials_path=args.credentials_path,
        profile_root=args.profile_root,
        folder=args.folder,
        timeout_seconds=args.timeout_seconds,
        max_probes_per_protocol=args.max_probes_per_protocol,
    )
    print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
