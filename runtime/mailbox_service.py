"""메일 계정 연결 확인과 fetch 공용 service를 모은다."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from mailbox import (
    build_local_mailbox_account_config,
    choose_successful_imap_candidate,
    run_imap_inbox_backfill_smoke,
    run_mailbox_autoconfig_smoke,
)
from mailbox.imap_backfill_smoke import default_backfill_report_path
from mailbox.imap_fetch_smoke import (
    resolve_successful_imap_login_username,
    resolve_successful_imap_login_username_kind,
)
from runtime.device_secret_store import (
    load_local_device_secrets,
    remember_default_openai_api_key,
    sanitize_openai_api_key,
)
from runtime.secrets_store import WorkspaceSecretsStore
from runtime.workspace import load_shared_workspace


StageCallback = Callable[[dict[str, object]], None]


@dataclass(slots=True)
class MailboxConnectionCheckResult:
    success: bool
    login_username_kind: str
    available_folders: list[str]
    recommended_folder: str
    friendly_error: str
    connection_status: str
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(slots=True)
class MailboxFetchResult:
    success: bool
    backfill_report_path: str
    fetched_count: int
    skipped_existing_count: int
    failed_count: int
    total_message_count: int
    limit: int | None
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def run_mailbox_connection_check_service(
    *,
    workspace_root: str,
    workspace_password: str,
    llm_model: str,
    llm_api_key: str,
    email_address: str,
    login_username: str,
    mailbox_password: str,
    default_folder: str,
    template_workbook_relative_path: str,
    on_stage: StageCallback | None = None,
) -> MailboxConnectionCheckResult:
    workspace = load_shared_workspace(workspace_root)
    secrets_store = WorkspaceSecretsStore(
        path=str(workspace.secure_blob_path()),
        password=workspace_password,
    )
    payload = secrets_store.read()
    current_llm = dict(payload.get("llm") or {})
    current_mailbox = dict(payload.get("mailbox") or {})
    current_exports = dict(payload.get("exports") or {})
    device_secrets = load_local_device_secrets()
    resolved_email = email_address.strip() or str(current_mailbox.get("email_address") or "")
    resolved_login_username = login_username.strip() or str(current_mailbox.get("login_username") or "")
    resolved_password = mailbox_password.strip() or str(current_mailbox.get("password") or "")
    resolved_api_key = (
        sanitize_openai_api_key(llm_api_key)
        or sanitize_openai_api_key(str(current_llm.get("api_key") or ""))
        or sanitize_openai_api_key(device_secrets.default_openai_api_key)
    )
    if not resolved_email:
        raise RuntimeError("이메일 주소를 먼저 입력해 주세요.")
    if not resolved_password:
        raise RuntimeError("비밀번호 또는 앱 비밀번호를 먼저 입력해 주세요.")

    payload["llm"] = {
        "api_key": resolved_api_key,
        "model": llm_model.strip() or str(current_llm.get("model") or "gpt-5.4"),
    }
    payload["mailbox"] = {
        **current_mailbox,
        "email_address": resolved_email,
        "login_username": resolved_login_username,
        "password": resolved_password,
        "default_folder": default_folder.strip() or str(current_mailbox.get("default_folder") or ""),
        "connection_status": "checking",
        "last_error": "",
    }
    payload["exports"] = {
        **current_exports,
        "template_workbook_relative_path": template_workbook_relative_path,
        "operating_workbook_relative_path": workspace.to_workspace_relative(
            workspace.profile_paths().operating_export_workbook_path()
        ),
    }
    secrets_store.write(payload)
    if resolved_api_key:
        remember_default_openai_api_key(api_key=resolved_api_key)

    _emit_stage(
        on_stage,
        stage_id="discover",
        stage_label="서버 후보 확인",
        progress_current=2,
        progress_total=5,
        details=["메일 서비스에 맞는 IMAP 후보를 확인하는 중입니다."],
        message="메일 서버 후보를 확인하고 있습니다.",
        next_action="잠시만 기다려 주세요.",
    )
    auth_report = run_mailbox_autoconfig_smoke(
        email_address=resolved_email,
        login_username=resolved_login_username,
        password=resolved_password,
        timeout_seconds=8.0,
        max_probes_per_protocol=2,
    )
    selected_candidate = choose_successful_imap_candidate(auth_report)
    available_folders: list[str] = []
    recommended_folder = default_folder.strip() or "INBOX"
    last_error = ""
    connection_status = "failed"
    login_username_kind = auth_report.login_username_kind

    _emit_stage(
        on_stage,
        stage_id="login",
        stage_label="로그인 시도",
        progress_current=3,
        progress_total=5,
        details=["로그인 가능 여부를 확인하고 있습니다."],
        message="실제 로그인을 시도하고 있습니다.",
        next_action="앱 비밀번호가 필요한 계정이면 조금 더 오래 걸릴 수 있습니다.",
    )
    if selected_candidate is None:
        last_error = "로그인에 성공한 IMAP 후보를 찾지 못했습니다."
    else:
        successful_login_username = resolve_successful_imap_login_username(
            report=auth_report,
            candidate=selected_candidate,
            explicit_login_username=resolved_login_username,
            email_address=resolved_email,
        )
        login_username_kind = resolve_successful_imap_login_username_kind(
            report=auth_report,
            candidate=selected_candidate,
            explicit_login_username=resolved_login_username,
            email_address=resolved_email,
        )
        try:
            _emit_stage(
                on_stage,
                stage_id="folders",
                stage_label="폴더 목록 읽기",
                progress_current=4,
                progress_total=5,
                details=["연결에 성공하면 접근 가능한 폴더 목록을 저장합니다."],
                message="받은편지함 목록을 읽는 중입니다.",
                next_action="기본 받은편지함을 추천하는 중입니다.",
            )
            available_folders = _list_imap_folders(
                candidate=selected_candidate,
                login_username=successful_login_username,
                password=resolved_password,
                timeout_seconds=8.0,
            )
            recommended_folder = _recommended_default_folder(available_folders)
            connection_status = "connected"
        except Exception as exc:
            connection_status = "connected"
            last_error = f"로그인은 성공했지만 폴더 목록을 읽지 못했습니다: {_friendly_mailbox_error_message(exc)}"

    payload = secrets_store.read()
    current_mailbox = dict(payload.get("mailbox") or {})
    payload["mailbox"] = {
        **current_mailbox,
        "email_address": resolved_email,
        "login_username": resolved_login_username,
        "password": resolved_password,
        "default_folder": current_mailbox.get("default_folder") or recommended_folder or "INBOX",
        "available_folders": available_folders,
        "recommended_folder": recommended_folder,
        "connection_status": connection_status,
        "connection_checked_at": datetime.now().isoformat(timespec="seconds"),
        "last_error": last_error,
        "login_username_kind": login_username_kind,
    }
    secrets_store.write(payload)

    notes = [
        f"recommended_folder={recommended_folder or 'INBOX'}",
        f"login_username_kind={login_username_kind}",
    ]
    return MailboxConnectionCheckResult(
        success=connection_status == "connected",
        login_username_kind=login_username_kind,
        available_folders=available_folders,
        recommended_folder=recommended_folder,
        friendly_error=last_error,
        connection_status=connection_status,
        notes=notes,
    )


def run_mailbox_fetch_service(
    *,
    workspace_root: str,
    workspace_password: str,
    limit: int | None,
    app_kind_note: str,
    on_stage: StageCallback | None = None,
) -> MailboxFetchResult:
    workspace = load_shared_workspace(workspace_root)
    secrets_store = WorkspaceSecretsStore(
        path=str(workspace.secure_blob_path()),
        password=workspace_password,
    )
    payload = secrets_store.read()
    mailbox_settings = dict(payload.get("mailbox") or {})
    account_config = build_local_mailbox_account_config(
        email_address=str(mailbox_settings.get("email_address") or ""),
        login_username=str(mailbox_settings.get("login_username") or ""),
        password=str(mailbox_settings.get("password") or ""),
        profile_root=workspace.profile_root(),
        source_path="workspace.encrypted_settings",
        notes=[app_kind_note],
    )
    report = run_imap_inbox_backfill_smoke(
        account_config=account_config,
        folder=str(mailbox_settings.get("default_folder") or mailbox_settings.get("recommended_folder") or "INBOX"),
        latest_limit=limit,
        on_progress=lambda payload: _emit_stage(
            on_stage,
            stage_id="fetch",
            stage_label="메일 가져오는 중",
            progress_current=int(payload.get("processed_count") or 0),
            progress_total=int(payload.get("total_count") or 0),
            stage_progress_current=int(payload.get("processed_count") or 0),
            stage_progress_total=int(payload.get("total_count") or 0),
            details=[
                f"새로 저장한 메일: {int(payload.get('fetched_count') or 0)}건",
                f"이미 있던 메일 건너뜀: {int(payload.get('skipped_existing_count') or 0)}건",
                f"문제 있는 메일: {int(payload.get('failed_count') or 0)}건",
            ],
            message=(
                f"메일을 가져오는 중입니다. {int(payload.get('processed_count') or 0)} / "
                f"{int(payload.get('total_count') or 0)}"
            ),
            next_action="이미 받은 메일은 건너뛰고 새 메일부터 저장합니다.",
        ),
    )
    report_path = default_backfill_report_path(
        str(workspace.profile_root()),
        account_config.email_address,
    )
    return MailboxFetchResult(
        success=report.success,
        backfill_report_path=workspace.to_workspace_relative(report_path),
        fetched_count=report.fetched_count,
        skipped_existing_count=report.skipped_existing_count,
        failed_count=report.failed_count,
        total_message_count=report.total_message_count,
        limit=limit,
        notes=list(report.notes),
    )


def _emit_stage(callback: StageCallback | None, **payload: object) -> None:
    if callback is None:
        return
    callback(payload)


def _list_imap_folders(*, candidate, login_username: str, password: str, timeout_seconds: float) -> list[str]:
    import imaplib
    import ssl

    socket = imaplib.IMAP4_SSL(
        host=candidate.host,
        port=candidate.port,
        ssl_context=ssl.create_default_context(),
        timeout=timeout_seconds,
    )
    try:
        socket.login(login_username, password)
        status, mailboxes = socket.list()
        if status != "OK":
            return []
        folder_names: list[str] = []
        for mailbox_line in mailboxes or []:
            decoded = mailbox_line.decode("utf-8", errors="ignore")
            if '"' in decoded:
                folder_name = decoded.split('"')[-2]
            else:
                folder_name = decoded.rsplit(" ", 1)[-1]
            folder_name = folder_name.strip()
            if folder_name:
                folder_names.append(folder_name)
        return folder_names
    finally:
        try:
            socket.logout()
        except Exception:
            pass


def _recommended_default_folder(folder_names: list[str]) -> str:
    candidates = [
        "INBOX",
        "Inbox",
        "받은편지함",
    ]
    for candidate in candidates:
        if candidate in folder_names:
            return candidate
    return folder_names[0] if folder_names else "INBOX"


def _friendly_mailbox_error_message(exc: Exception) -> str:
    text = str(exc).strip()
    if text:
        return text
    return f"{exc.__class__.__name__}가 발생했습니다."
