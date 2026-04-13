"""전용 데스크톱 창 안에서 쓰는 로컬 Web UI 서버."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from html import escape
import imaplib
import os
from pathlib import Path
import re
import subprocess
import ssl
import sys
import threading
from typing import Any
from urllib.parse import urlencode

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from llm import OpenAIResponsesConfig, OpenAIResponsesWrapper
from runtime import (
    assert_supported_workspace,
    assess_workspace_path,
    clear_last_workspace_secret,
    close_workspace_entry,
    create_shared_workspace,
    create_workspace_entry,
    default_device_secrets_path,
    LockedWorkspaceError,
    WorkspaceSecretsStore,
    WorkspaceStateStore,
    acquire_workspace_write_lock,
    check_feature,
    default_local_portable_exe_path,
    default_local_portable_bundle_root,
    default_local_settings_path,
    default_startup_log_path,
    default_workspace_parent_dir,
    feature_catalog_rows,
    forget_workspace,
    ingest_review_report_into_state,
    list_feature_specs,
    load_local_device_secrets,
    load_local_app_settings,
    load_exports_summary_service,
    load_review_center_page_service,
    load_review_detail_service,
    load_shared_workspace,
    open_workspace_entry,
    normalize_workspace_relative_input,
    pick_file_native,
    pick_folder_native,
    picker_bridge_self_test,
    remember_default_openai_api_key,
    remember_last_workspace_secret,
    remember_workspace,
    rebuild_operating_workbook,
    run_mailbox_connection_check_service,
    run_pipeline_sync_service,
    run_feature,
    save_local_app_settings,
    save_workspace_settings,
    suggest_workspace_root,
    template_status_for_workspace,
)


TEMPLATES = Jinja2Templates(directory=str(Path(__file__).resolve().parent / "templates"))
STATIC_ROOT = Path(__file__).resolve().parent / "static"
APP_ID = "email_pilot_ai_desktop"
APP_VERSION = "0.1.0"


@dataclass(slots=True)
class BackgroundJobState:
    status: str = "idle"
    message: str = ""
    feature_id: str = ""
    stage_id: str = ""
    stage_label: str = ""
    progress_current: int = 0
    progress_total: int = 0
    progress_percent: int = 0
    next_action: str = ""
    details: list[str] = field(default_factory=list)
    started_at: str = ""
    finished_at: str = ""
    last_result: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "message": self.message,
            "feature_id": self.feature_id,
            "stage_id": self.stage_id,
            "stage_label": self.stage_label,
            "progress_current": self.progress_current,
            "progress_total": self.progress_total,
            "progress_percent": self.progress_percent,
            "next_action": self.next_action,
            "details": list(self.details),
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "last_result": self.last_result,
        }


@dataclass(slots=True)
class WorkspaceSession:
    workspace_root: str
    workspace_password: str
    readonly: bool
    app_kind: str
    lock_handle: Any | None = None
    job_state: BackgroundJobState = field(default_factory=BackgroundJobState)


@dataclass(slots=True)
class ServerState:
    current_session: WorkspaceSession | None = None
    shell_context: "ShellContext" | None = None
    pending_notice: str = ""
    pending_error: str = ""
    auto_restore_suppressed: bool = False


def _shell_mode_label(mode: str) -> str:
    return {
        "desktop_window": "전용 앱 창",
        "browser_fallback": "로컬 브라우저 fallback",
        "headless": "headless / smoke",
    }.get(mode, mode or "(미확정)")


def _native_dialog_state_label(state: str) -> str:
    return {
        "checking": "확인 중",
        "desktop_pending": "전용 창 연결 확인 중",
        "desktop_ready": "사용 가능",
        "browser_fallback": "브라우저 fallback",
        "desktop_failed": "전용 창 연결 실패",
    }.get(state, state or "(미확정)")


@dataclass(slots=True)
class ShellContext:
    shell_mode: str = "browser_fallback"
    native_dialog_state: str = "browser_fallback"
    startup_log_path: str = ""
    official_local_bundle_path: str = ""
    native_dialog_expected: bool = False
    unsupported_launch_reason: str = ""
    launch_path: str = ""

    def to_template_dict(self) -> dict[str, Any]:
        return {
            "shell_mode": self.shell_mode,
            "shell_mode_label": _shell_mode_label(self.shell_mode),
            "native_dialog_state": self.native_dialog_state,
            "native_dialog_state_label": _native_dialog_state_label(self.native_dialog_state),
            "startup_log_path": self.startup_log_path,
            "official_local_bundle_path": self.official_local_bundle_path,
            "native_dialog_expected": self.native_dialog_expected,
            "unsupported_launch_reason": self.unsupported_launch_reason,
            "launch_path": self.launch_path,
            "launch_support_label": "지원 안 됨" if self.unsupported_launch_reason else "지원됨",
        }


def _default_shell_context() -> ShellContext:
    return ShellContext(
        shell_mode="browser_fallback",
        native_dialog_state="browser_fallback",
        startup_log_path=str(default_startup_log_path()),
        official_local_bundle_path=str(default_local_portable_exe_path()),
        native_dialog_expected=False,
    )


SERVER_STATE = ServerState(shell_context=_default_shell_context())
app = FastAPI(title="Email Pilot AI Desktop")
app.mount("/static", StaticFiles(directory=str(STATIC_ROOT)), name="static")


@app.get("/app-meta")
def app_meta():
    shell_context = SERVER_STATE.shell_context or _default_shell_context()
    return JSONResponse(
        {
            "app_id": APP_ID,
            "app_name": "Email Pilot AI Desktop",
            "version": APP_VERSION,
            "shell_mode": shell_context.shell_mode,
            "native_dialog_state": shell_context.native_dialog_state,
        }
    )


def set_shell_context(
    *,
    shell_mode: str,
    native_dialog_state: str,
    startup_log_path: str | None = None,
    official_local_bundle_path: str | None = None,
    native_dialog_expected: bool | None = None,
    unsupported_launch_reason: str = "",
    launch_path: str = "",
) -> ShellContext:
    SERVER_STATE.shell_context = ShellContext(
        shell_mode=shell_mode,
        native_dialog_state=native_dialog_state,
        startup_log_path=startup_log_path or str(default_startup_log_path()),
        official_local_bundle_path=(
            official_local_bundle_path or str(default_local_portable_exe_path())
        ),
        native_dialog_expected=bool(native_dialog_expected),
        unsupported_launch_reason=unsupported_launch_reason,
        launch_path=launch_path,
    )
    return SERVER_STATE.shell_context


MODEL_OPTIONS: tuple[str, ...] = ("gpt-5.4", "gpt-5.4-mini", "gpt-5.4-nano")


def _workspace_objects(session: WorkspaceSession):
    workspace = load_shared_workspace(session.workspace_root)
    secrets_store = WorkspaceSecretsStore(
        path=str(workspace.secure_blob_path()),
        password=session.workspace_password,
    )
    state_store = WorkspaceStateStore(workspace.state_db_path())
    state_store.ensure_schema()
    return workspace, secrets_store, state_store


def _first_reason(*reasons: str) -> str:
    for item in reasons:
        if item:
            return item
    return ""


def _action_state(*, enabled: bool, reason: str = "", helper: str = "") -> dict[str, Any]:
    return {
        "enabled": bool(enabled),
        "disabled": not enabled,
        "reason": reason,
        "helper": helper,
        "tooltip": reason or helper,
    }


def _redirect_with_message(
    url: str,
    *,
    notice: str | None = None,
    error: str | None = None,
    extra_params: dict[str, str] | None = None,
) -> RedirectResponse:
    payload: dict[str, str] = {}
    if notice:
        payload["notice"] = notice
    if error:
        payload["error"] = error
    if extra_params:
        payload.update(extra_params)
    if payload:
        separator = "&" if "?" in url else "?"
        url = f"{url}{separator}{urlencode(payload)}"
    return RedirectResponse(url=url, status_code=303)


def _page_feedback(request: Request) -> dict[str, str]:
    pending_notice = SERVER_STATE.pending_notice
    pending_error = SERVER_STATE.pending_error
    SERVER_STATE.pending_notice = ""
    SERVER_STATE.pending_error = ""
    return {
        "notice": str(request.query_params.get("notice") or pending_notice or ""),
        "error": str(request.query_params.get("error") or pending_error or ""),
        "current_path": request.url.path,
    }


def _parse_bool_text(value: str | None, *, default: bool = False) -> bool:
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _parse_positive_int_text(value: str | None, *, default: int) -> int:
    if value is None or not str(value).strip():
        return default
    try:
        parsed = int(str(value).strip())
    except ValueError:
        return default
    return parsed if parsed > 0 else default


def _review_sort_label(sort: str) -> str:
    normalized = (sort or "received_desc").strip().lower()
    return {
        "received_desc": "받은 시각 최신순",
        "company_asc": "회사명순",
        "sender_asc": "발신자순",
    }.get(normalized, "받은 시각 최신순")


def _review_query_from_request(request: Request) -> dict[str, Any]:
    local_settings = load_local_app_settings()
    stored = dict(local_settings.last_review_filters or {})
    params = request.query_params

    def _pick_text(key: str, default: str = "") -> str:
        if key in params:
            return str(params.get(key) or default)
        return str(stored.get(key) or default)

    search = _pick_text("search", "")
    triage_label = _pick_text("triage_label", "")
    export_only = _parse_bool_text(_pick_text("export_only", "false"), default=False)
    page = _parse_positive_int_text(_pick_text("page", "1"), default=1)
    page_size = _parse_positive_int_text(_pick_text("page_size", "50"), default=50)
    sort = _pick_text("sort", "received_desc") or "received_desc"
    selected_bundle_id = _pick_text("selected_bundle_id", "")
    artifact_kind = _pick_text("artifact_kind", "preview") or "preview"

    local_settings.last_review_filters = {
        "search": search,
        "triage_label": triage_label,
        "export_only": "true" if export_only else "false",
        "page": str(page),
        "page_size": str(page_size),
        "sort": sort,
        "selected_bundle_id": selected_bundle_id,
        "artifact_kind": artifact_kind,
    }
    save_local_app_settings(local_settings)
    return {
        "search": search,
        "triage_label": triage_label,
        "export_only": export_only,
        "page": page,
        "page_size": page_size,
        "sort": sort,
        "selected_bundle_id": selected_bundle_id,
        "artifact_kind": artifact_kind,
    }


def _review_query_string(query: dict[str, Any], **overrides: Any) -> str:
    merged = dict(query)
    merged.update(overrides)
    payload: dict[str, str] = {}
    for key in (
        "search",
        "triage_label",
        "export_only",
        "page",
        "page_size",
        "sort",
        "selected_bundle_id",
        "artifact_kind",
    ):
        value = merged.get(key)
        if key == "export_only":
            payload[key] = "true" if bool(value) else "false"
        elif value not in {None, ""}:
            payload[key] = str(value)
    return urlencode(payload)


def _review_url(query: dict[str, Any], **overrides: Any) -> str:
    payload = _review_query_string(query, **overrides)
    return f"/review?{payload}" if payload else "/review"


def _review_hidden_fields(query: dict[str, Any], **overrides: Any) -> list[tuple[str, str]]:
    merged = dict(query)
    merged.update(overrides)
    fields: list[tuple[str, str]] = []
    for key in (
        "search",
        "triage_label",
        "export_only",
        "page",
        "page_size",
        "sort",
        "selected_bundle_id",
        "artifact_kind",
    ):
        value = merged.get(key)
        if value in {None, ""}:
            continue
        if key == "export_only":
            fields.append((key, "true" if bool(value) else "false"))
        else:
            fields.append((key, str(value)))
    return fields


def _read_workspace_text(path: Path, *, default: str = "", max_bytes: int = 1_000_000) -> str:
    if not path.exists() or not path.is_file():
        return default
    raw = path.read_bytes()[:max_bytes]
    return raw.decode("utf-8", errors="replace")


def _review_artifact_label(kind: str) -> str:
    normalized = (kind or "preview").strip().lower()
    return {
        "preview": "메일 미리보기",
        "raw": "원본 메일 파일",
        "summary": "요약 메모",
        "record": "추출 결과 원본",
        "projected": "엑셀 반영 미리보기",
    }.get(normalized, "메일 미리보기")


def _load_review_artifact_preview(*, workspace, item: dict[str, Any] | None, kind: str) -> dict[str, Any] | None:
    if not item:
        return None
    normalized = (kind or "preview").strip().lower()
    mapping = {
        "preview": item.get("preview_relpath"),
        "raw": item.get("raw_eml_relpath"),
        "summary": item.get("summary_relpath"),
        "record": item.get("extracted_record_relpath"),
        "projected": item.get("projected_row_relpath"),
    }
    relative_path = str(mapping.get(normalized) or "")
    if not relative_path:
        return None
    target = workspace.from_workspace_relative(relative_path).resolve()
    if not target.is_relative_to(workspace.root().resolve()) or not target.exists():
        return None
    if normalized == "preview":
        html_content = target.read_text(encoding="utf-8", errors="replace")
        return {
            "kind": normalized,
            "label": _review_artifact_label(normalized),
            "content_type": "html",
            "relative_path": relative_path,
            "content": html_content,
        }
    text = _read_workspace_text(target, default="파일을 읽지 못했습니다.")
    return {
        "kind": normalized,
        "label": _review_artifact_label(normalized),
        "content_type": "text",
        "relative_path": relative_path,
        "content": text,
    }


def _job_progress_percent(current: int, total: int) -> int:
    if total <= 0:
        return 0
    return max(0, min(100, int((current / total) * 100)))


def _job_failure_stage_label(*, stage_id: str, stage_label: str) -> str:
    if stage_label:
        return stage_label
    return {
        "prepare": "준비 중",
        "fetch": "메일 가져오는 중",
        "analysis": "분석 중",
        "export": "엑셀 반영 중",
        "partial": "부분 완료 정리",
        "failed": "실패 정리",
    }.get(stage_id, "후속 처리")


def _set_job_state(
    session: WorkspaceSession,
    *,
    status: str,
    feature_id: str,
    message: str,
    stage_id: str = "",
    stage_label: str = "",
    progress_current: int = 0,
    progress_total: int = 0,
    next_action: str = "",
    details: list[str] | None = None,
    last_result: dict[str, Any] | None = None,
    preserve_started_at: bool = False,
) -> None:
    started_at = session.job_state.started_at if preserve_started_at and session.job_state.started_at else datetime.now().isoformat(timespec="seconds")
    finished_at = datetime.now().isoformat(timespec="seconds") if status in {"completed", "failed", "partial_success"} else ""
    session.job_state = BackgroundJobState(
        status=status,
        message=message,
        feature_id=feature_id,
        stage_id=stage_id,
        stage_label=stage_label,
        progress_current=progress_current,
        progress_total=progress_total,
        progress_percent=_job_progress_percent(progress_current, progress_total),
        next_action=next_action,
        details=list(details or []),
        started_at=started_at,
        finished_at=finished_at,
        last_result=last_result,
    )


def _recent_workspace_items() -> list[dict[str, str | bool]]:
    items: list[dict[str, str | bool]] = []
    settings = load_local_app_settings()
    device_secrets = load_local_device_secrets()
    for workspace_path in settings.recent_workspaces:
        candidate = Path(workspace_path)
        exists = candidate.exists()
        items.append(
            {
                "path": workspace_path,
                "name": candidate.name or workspace_path,
                "exists": exists,
                "has_saved_password": (
                    device_secrets.last_workspace_root == workspace_path
                    and bool(device_secrets.last_workspace_password)
                ),
            }
        )
    return items


def _remember_session_locally(session: WorkspaceSession) -> None:
    SERVER_STATE.auto_restore_suppressed = False
    remember_workspace(session.workspace_root)
    remember_last_workspace_secret(
        workspace_root=session.workspace_root,
        workspace_password=session.workspace_password,
    )


def _try_restore_last_workspace_session() -> None:
    if SERVER_STATE.current_session is not None:
        return
    if SERVER_STATE.auto_restore_suppressed:
        return
    local_settings = load_local_app_settings()
    device_secrets = load_local_device_secrets()
    workspace_root = device_secrets.last_workspace_root or local_settings.last_open_workspace
    workspace_password = device_secrets.last_workspace_password
    if not workspace_root or not workspace_password:
        return
    try:
        workspace = assert_supported_workspace(load_shared_workspace(workspace_root))
        _validate_workspace_password(workspace, workspace_password)
    except Exception:
        SERVER_STATE.pending_error = "마지막 세이브 파일을 자동으로 다시 열지 못했습니다. 경로 또는 암호를 다시 확인해 주세요."
        clear_last_workspace_secret()
        return

    readonly = False
    lock_handle = None
    try:
        lock_handle = acquire_workspace_write_lock(
            lock_path=workspace.lock_path(),
            workspace_id=workspace.manifest.workspace_id,
            app_kind="desktop-app",
        )
    except LockedWorkspaceError:
        readonly = True

    _replace_current_session(
        WorkspaceSession(
            workspace_root=str(workspace.root()),
            workspace_password=workspace_password,
            readonly=readonly,
            app_kind="desktop-app",
            lock_handle=lock_handle,
        )
    )
    SERVER_STATE.pending_notice = (
        "이 PC에서 마지막으로 사용한 세이브 파일을 자동으로 다시 열었습니다."
        if not readonly
        else "마지막 세이브 파일을 읽기 전용으로 다시 열었습니다."
    )


def _dialog_context(*, workspace=None) -> dict[str, Any]:
    shell_context = SERVER_STATE.shell_context or _default_shell_context()
    picker_diagnostics = picker_bridge_self_test(
        shell_mode=shell_context.shell_mode,
        window_attached=shell_context.native_dialog_expected,
    )
    return {
        "native_dialog_supported": picker_diagnostics.native_dialog_supported,
        "dialog_workspace_root": str(workspace.root()) if workspace is not None else "",
        "shell_context": shell_context.to_template_dict(),
        "picker_diagnostics": picker_diagnostics.to_dict(),
    }


def _validate_workspace_password(workspace, workspace_password: str) -> None:
    WorkspaceSecretsStore(
        path=str(workspace.secure_blob_path()),
        password=workspace_password,
    ).read()


def _replace_current_session(session: WorkspaceSession | None) -> None:
    previous = SERVER_STATE.current_session
    if previous is not None and previous.lock_handle is not None:
        previous.lock_handle.release()
    SERVER_STATE.current_session = session


def _open_workspace_session(
    *,
    workspace,
    workspace_password: str,
    readonly_requested: bool = False,
) -> tuple[WorkspaceSession, str]:
    readonly = bool(readonly_requested)
    lock_handle = None
    notice = "세이브 파일을 열었습니다."
    if not readonly:
        try:
            lock_handle = acquire_workspace_write_lock(
                lock_path=workspace.lock_path(),
                workspace_id=workspace.manifest.workspace_id,
                app_kind="desktop-app",
            )
        except LockedWorkspaceError:
            readonly = True
            notice = "다른 곳에서 사용 중이라 읽기 전용으로 세이브 파일을 열었습니다."
    session = WorkspaceSession(
        workspace_root=str(workspace.root()),
        workspace_password=workspace_password,
        readonly=readonly,
        app_kind="desktop-app",
        lock_handle=lock_handle,
    )
    _replace_current_session(session)
    _remember_session_locally(session)
    return session, notice


def _template_status(*, workspace, shared_settings: dict[str, Any]) -> dict[str, str]:
    return template_status_for_workspace(
        workspace_root=str(workspace.root()),
        shared_settings=shared_settings,
    )


def _sync_action_states(
    *,
    session: WorkspaceSession,
    shared_settings: dict[str, Any],
    template_status: dict[str, str],
    state_counts: dict[str, int],
) -> dict[str, dict[str, Any]]:
    mailbox = dict(shared_settings.get("mailbox") or {})
    llm = dict(shared_settings.get("llm") or {})
    connection_error = str(mailbox.get("last_error") or "").strip()
    connection_reason = _first_reason(
        "읽기 전용 세션에서는 실행할 수 없습니다." if session.readonly else "",
        "OpenAI API key를 먼저 저장해 주세요." if not llm.get("api_key_saved") else "",
        "이메일 주소를 먼저 입력해 주세요." if not mailbox.get("email_address") else "",
        "이메일 비밀번호를 먼저 입력해 주세요." if not mailbox.get("password_saved") else "",
        (
            f"계정 연결 확인이 아직 끝나지 않았습니다. {connection_error}"
            if connection_error and mailbox.get("connection_status") != "connected"
            else ""
        ),
        (
            "먼저 설정에서 계정 연결 확인을 완료해 주세요."
            if mailbox.get("connection_status") != "connected"
            else ""
        ),
        template_status["message"] if template_status.get("status") != "pass" else "",
    )
    rebuild_reason = _first_reason(
        "읽기 전용 세션에서는 재반영할 수 없습니다." if session.readonly else "",
        "먼저 동기화를 실행해 리뷰 항목을 만들어 주세요."
        if int(state_counts.get("total") or 0) == 0
        else "",
        template_status["message"] if template_status.get("status") != "pass" else "",
    )
    connection_check_reason = _first_reason(
        "읽기 전용 세션에서는 연결 확인을 실행할 수 없습니다." if session.readonly else "",
    )
    return {
        "quick_sync": _action_state(
            enabled=not bool(connection_reason),
            reason=connection_reason,
            helper="최근 10건으로 연결과 분류 품질을 빠르게 확인합니다.",
        ),
        "full_sync": _action_state(
            enabled=not bool(connection_reason),
            reason=connection_reason,
            helper="새 메일만 증분으로 가져오고, 바뀐 분석만 다시 계산합니다.",
        ),
        "rebuild_workbook": _action_state(
            enabled=not bool(rebuild_reason),
            reason=rebuild_reason,
            helper="현재 대표 신청 건 기준으로 운영 workbook을 다시 씁니다.",
        ),
        "connection_check": _action_state(
            enabled=not bool(connection_check_reason),
            reason=connection_check_reason,
            helper="입력한 이메일 주소와 비밀번호로 로그인 가능한지 확인하고 폴더 목록을 가져옵니다.",
        ),
        "settings_save": _action_state(
            enabled=not session.readonly,
            reason="읽기 전용 세션에서는 설정을 저장할 수 없습니다." if session.readonly else "",
            helper="입력한 설정을 이 세이브 파일에 저장합니다.",
        ),
    }


def _build_onboarding_steps(
    *,
    shared_settings: dict[str, Any],
    latest_sync_run: dict[str, Any] | None,
    action_states: dict[str, dict[str, Any]],
) -> list[dict[str, str]]:
    mailbox = dict(shared_settings.get("mailbox") or {})
    quick_done = bool(
        latest_sync_run
        and latest_sync_run.get("status") == "completed"
        and str((latest_sync_run.get("metadata") or {}).get("sync_mode") or "") == "quick_smoke"
    )
    full_done = bool(
        latest_sync_run
        and latest_sync_run.get("status") == "completed"
        and str((latest_sync_run.get("metadata") or {}).get("sync_mode") or "") == "incremental_full"
    )
    return [
        {
            "step": "1",
            "title": "세이브 파일 열기",
            "status": "done",
            "status_label": "완료",
            "detail": "현재 세이브 파일이 열려 있습니다.",
        },
        {
            "step": "2",
            "title": "계정 연결",
            "status": "done" if mailbox.get("connection_status") == "connected" else "current",
            "status_label": "완료" if mailbox.get("connection_status") == "connected" else "다음",
            "detail": (
                f"연결 확인 완료 · 추천 받은편지함 {mailbox.get('recommended_folder') or mailbox.get('default_folder') or 'INBOX'}"
                if mailbox.get("connection_status") == "connected"
                else "설정에서 이메일 주소와 비밀번호를 입력한 뒤 계정 연결 확인을 실행합니다."
            ),
        },
        {
            "step": "3",
            "title": "빠른 테스트 동기화",
            "status": "done" if quick_done else ("current" if action_states["quick_sync"]["enabled"] else "blocked"),
            "status_label": "완료" if quick_done else ("가능" if action_states["quick_sync"]["enabled"] else "준비 필요"),
            "detail": "최근 10건만 가져와 연결, 분류, 엑셀 반영 흐름을 먼저 점검합니다.",
        },
        {
            "step": "4",
            "title": "전체 동기화와 리뷰",
            "status": "done" if full_done else ("current" if action_states["full_sync"]["enabled"] else "blocked"),
            "status_label": "완료" if full_done else ("가능" if action_states["full_sync"]["enabled"] else "준비 필요"),
            "detail": "새 메일만 증분으로 가져오고, 리뷰센터에서 결과를 확인합니다.",
        },
    ]


def _workspace_page_context(session: WorkspaceSession) -> dict[str, Any]:
    workspace, secrets_store, state_store = _workspace_objects(session)
    shared_settings = secrets_store.masked_summary()
    device_secrets = load_local_device_secrets()
    template_status = _template_status(workspace=workspace, shared_settings=shared_settings)
    state_counts = state_store.summary_counts()
    latest_sync_run = state_store.latest_sync_run()
    action_states = _sync_action_states(
        session=session,
        shared_settings=shared_settings,
        template_status=template_status,
        state_counts=state_counts,
    )
    mailbox = dict(shared_settings.get("mailbox") or {})
    connection_tone = (
        "pass"
        if mailbox.get("connection_status") == "connected"
        else ("fail" if mailbox.get("connection_status") == "failed" else "warn")
    )
    return {
        "workspace_open": True,
        "session": session,
        "workspace": workspace,
        "shared_settings": shared_settings,
        "state_counts": state_counts,
        "latest_sync_run": latest_sync_run,
        "latest_feature_runs": state_store.latest_feature_runs(),
        "feature_spec_count": len(list_feature_specs()),
        "recent_workspaces": load_local_app_settings().recent_workspaces,
        "recent_workspace_items": _recent_workspace_items(),
        "local_settings_path": str(default_local_settings_path()),
        "device_secrets_path": str(default_device_secrets_path()),
        "last_open_workspace": load_local_app_settings().last_open_workspace,
        "default_workspace_parent_dir": str(default_workspace_parent_dir()),
        "default_openai_api_key": device_secrets.default_openai_api_key,
        "template_status": template_status,
        "action_states": action_states,
        "model_options": list(MODEL_OPTIONS),
        "mailbox_folder_options": list(mailbox.get("available_folders") or []),
        "onboarding_steps": _build_onboarding_steps(
            shared_settings=shared_settings,
            latest_sync_run=latest_sync_run,
            action_states=action_states,
        ),
        "connection_tone": connection_tone,
    }


def _session_context() -> dict[str, Any]:
    _try_restore_last_workspace_session()
    local_settings = load_local_app_settings()
    device_secrets = load_local_device_secrets()
    session = SERVER_STATE.current_session
    if session is None:
        return {
            "workspace_open": False,
            "recent_workspaces": local_settings.recent_workspaces,
            "recent_workspace_items": _recent_workspace_items(),
            "local_settings_path": str(default_local_settings_path()),
            "device_secrets_path": str(default_device_secrets_path()),
            "last_open_workspace": local_settings.last_open_workspace,
            "default_workspace_parent_dir": str(default_workspace_parent_dir()),
            "default_openai_api_key": device_secrets.default_openai_api_key,
            "last_workspace_with_saved_password": device_secrets.last_workspace_root,
        }

    return _workspace_page_context(session)


def _friendly_mailbox_error_message(exc: Exception) -> str:
    text = str(exc).strip()
    lowered = text.lower()
    if "authenticationfailed" in lowered or "invalid credentials" in lowered:
        return "로그인 정보가 맞지 않거나 앱 비밀번호가 필요합니다."
    if "app password" in lowered:
        return "일반 비밀번호 대신 앱 비밀번호가 필요할 수 있습니다."
    if "timeout" in lowered:
        return "메일 서버 응답이 지연되었습니다. 잠시 후 다시 시도해 주세요."
    return text or "메일 계정 연결 확인 중 오류가 발생했습니다."


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


def _parse_imap_folder_name(raw_line: bytes | str) -> str:
    text = raw_line.decode("utf-8", errors="replace") if isinstance(raw_line, bytes) else str(raw_line)
    quoted_match = re.search(r'"((?:[^"\\\\]|\\\\.)*)"\s*$', text)
    if quoted_match is not None:
        return quoted_match.group(1).replace('\\"', '"').strip()
    parts = text.strip().split()
    return parts[-1].strip('"') if parts else ""


def _list_imap_folders(
    *,
    candidate: MailServerCandidate,
    login_username: str,
    password: str,
    timeout_seconds: float,
) -> list[str]:
    client = _open_logged_in_imap_client(
        candidate=candidate,
        login_username=login_username,
        password=password,
        timeout_seconds=timeout_seconds,
    )
    try:
        status, data = client.list()
        if status != "OK":
            return []
        names: list[str] = []
        seen: set[str] = set()
        for item in data or []:
            folder_name = _parse_imap_folder_name(item)
            if not folder_name or folder_name in seen:
                continue
            seen.add(folder_name)
            names.append(folder_name)
        inbox_like = sorted(
            [name for name in names if name.upper() == "INBOX" or "받은" in name],
            key=lambda name: (name.upper() != "INBOX", name.lower()),
        )
        remaining = sorted(
            [name for name in names if name not in inbox_like],
            key=lambda name: name.lower(),
        )
        return inbox_like + remaining
    finally:
        try:
            client.logout()
        except Exception:
            pass


def _recommended_default_folder(folder_names: list[str]) -> str:
    if not folder_names:
        return "INBOX"
    exact_inbox = next((name for name in folder_names if name.upper() == "INBOX"), "")
    if exact_inbox:
        return exact_inbox
    for token in ("받은편지함", "받은 편지함", "inbox"):
        match = next((name for name in folder_names if token.lower() in name.lower()), "")
        if match:
            return match
    return folder_names[0]


def _resolve_template_workbook_path_for_workspace(
    *,
    workspace,
    export_settings: dict[str, Any],
) -> Path:
    relative_path = str(export_settings.get("template_workbook_relative_path") or "")
    if relative_path:
        return workspace.from_workspace_relative(relative_path)
    return workspace.profile_paths().template_workbook_path()


def _start_mailbox_check_job(
    *,
    session: WorkspaceSession,
    resolved_email: str,
    resolved_login_username: str,
    resolved_password: str,
    llm_model: str,
    resolved_api_key: str,
    default_folder: str,
    resolved_template_path: str,
) -> None:
    if session.job_state.status == "running":
        return

    _set_job_state(
        session,
        status="running",
        feature_id="mailbox.connection_check",
        message="이메일 계정 연결을 확인하고 있습니다.",
        stage_id="validate",
        stage_label="입력 확인",
        progress_current=1,
        progress_total=5,
        next_action="잠시만 기다려 주세요.",
        details=["입력값을 저장하고 계정 연결 확인을 준비하고 있습니다."],
    )

    def _run() -> None:
        try:
            result = run_mailbox_connection_check_service(
                workspace_root=session.workspace_root,
                workspace_password=session.workspace_password,
                llm_model=llm_model,
                llm_api_key=resolved_api_key,
                email_address=resolved_email,
                login_username=resolved_login_username,
                mailbox_password=resolved_password,
                default_folder=default_folder,
                template_workbook_relative_path=resolved_template_path,
                on_stage=lambda payload: _set_job_state(
                    session,
                    status="running",
                    feature_id="mailbox.connection_check",
                    message=str(payload.get("message") or "계정 연결을 확인하고 있습니다."),
                    stage_id=str(payload.get("stage_id") or "running"),
                    stage_label=str(payload.get("stage_label") or "실행 중"),
                    progress_current=int(payload.get("progress_current") or 0),
                    progress_total=int(payload.get("progress_total") or 0),
                    next_action=str(payload.get("next_action") or ""),
                    details=list(payload.get("details") or []),
                    preserve_started_at=True,
                ),
            )
            if result.success:
                _set_job_state(
                    session,
                    status="completed",
                    feature_id="mailbox.connection_check",
                    message="계정 연결 확인이 완료되었습니다.",
                    stage_id="complete",
                    stage_label="완료",
                    progress_current=5,
                    progress_total=5,
                    next_action="다음으로 빠른 테스트 동기화를 실행해 보세요.",
                    details=[
                        f"추천 기본 받은편지함: {result.recommended_folder or 'INBOX'}",
                        result.friendly_error or "폴더 목록도 정상적으로 읽었습니다.",
                    ],
                    last_result={
                        "success": True,
                        "available_folders": result.available_folders,
                        "recommended_folder": result.recommended_folder,
                        "login_username_kind": result.login_username_kind,
                    },
                    preserve_started_at=True,
                )
                return

            _set_job_state(
                session,
                status="failed",
                feature_id="mailbox.connection_check",
                message="계정 연결 확인에 실패했습니다.",
                stage_id="failed",
                stage_label="실패",
                progress_current=5,
                progress_total=5,
                next_action="설정에서 이메일 주소, 비밀번호 또는 로그인 ID를 다시 확인한 뒤 재시도해 주세요.",
                details=[result.friendly_error or "계정 연결 확인 중 오류가 발생했습니다."],
                last_result={
                    "success": False,
                    "available_folders": result.available_folders,
                    "recommended_folder": result.recommended_folder,
                    "login_username_kind": result.login_username_kind,
                },
                preserve_started_at=True,
            )
        except Exception as exc:
            _set_job_state(
                session,
                status="failed",
                feature_id="mailbox.connection_check",
                message="계정 연결 확인 중 오류가 발생했습니다.",
                stage_id="failed",
                stage_label="실패",
                progress_current=5,
                progress_total=5,
                next_action="설정 값을 확인하고 다시 시도해 주세요.",
                details=[_friendly_mailbox_error_message(exc)],
                last_result={"success": False},
                preserve_started_at=True,
            )

    threading.Thread(target=_run, daemon=True).start()


def _start_sync_job(
    *,
    session: WorkspaceSession,
    sync_mode: str,
    scope: str = "recent",
    limit: int | None = None,
) -> None:
    if session.job_state.status == "running":
        return

    effective_scope = "all" if sync_mode == "incremental_full" and scope != "recent" else scope
    effective_limit = 10 if sync_mode == "quick_smoke" and limit is None else limit
    feature_id = (
        "runtime.workspace.sync.quick_smoke"
        if effective_scope == "recent" and effective_limit == 10
        else "runtime.workspace.sync"
    )
    _set_job_state(
        session,
        status="running",
        feature_id=feature_id,
        message="동기화 준비를 시작합니다.",
        stage_id="prepare",
        stage_label="준비 중",
        progress_current=0,
        progress_total=3,
        next_action="잠시만 기다려 주세요.",
        details=["세이브 파일 설정과 권한을 확인하고 있습니다."],
    )

    def _run() -> None:
        try:
            result = run_pipeline_sync_service(
                workspace_root=session.workspace_root,
                workspace_password=session.workspace_password,
                scope=effective_scope,
                limit=effective_limit,
                app_kind=session.app_kind,
                on_stage=lambda payload: _set_job_state(
                    session,
                    status="running",
                    feature_id=feature_id,
                    message=str(payload.get("message") or "동기화를 진행하고 있습니다."),
                    stage_id=str(payload.get("stage_id") or "running"),
                    stage_label=str(payload.get("stage_label") or "실행 중"),
                    progress_current=int(payload.get("progress_current") or 0),
                    progress_total=int(payload.get("progress_total") or 0),
                    next_action=str(payload.get("next_action") or ""),
                    details=list(payload.get("details") or []),
                    preserve_started_at=True,
                ),
            )
            if session.lock_handle is not None:
                session.lock_handle.refresh()
            _set_job_state(
                session,
                status=result.status,
                feature_id=feature_id,
                message=result.message,
                stage_id=result.stage_id,
                stage_label=result.stage_label,
                progress_current=3,
                progress_total=3,
                next_action=result.next_action,
                details=result.details,
                last_result={
                    "scope": result.scope,
                    "limit": result.limit,
                    "fetched_count": result.fetched_count,
                    "skipped_existing_count": result.skipped_existing_count,
                    "analysis_reused_count": result.analysis_reused_count,
                    "analysis_rerun_count": result.analysis_rerun_count,
                    "reuse_counts": result.reuse_counts,
                    "review_json_path": result.review_json_path,
                    "review_html_path": result.review_html_path,
                    "operating_workbook_path": result.operating_workbook_path,
                },
                preserve_started_at=True,
            )
        except Exception as exc:
            _set_job_state(
                session,
                status="failed",
                feature_id=feature_id,
                message="동기화에 실패했습니다.",
                stage_id="failed",
                stage_label="실패",
                progress_current=3,
                progress_total=3,
                next_action="설정을 다시 확인하고 재시도해 주세요.",
                details=[f"{exc.__class__.__name__}: {exc}"],
                preserve_started_at=True,
            )

    threading.Thread(target=_run, daemon=True).start()


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    context = _session_context()
    return TEMPLATES.TemplateResponse(
        "home.html",
        {
            "request": request,
            "auto_open_modal": "save-guide-modal" if request.query_params.get("guide") == "1" else "",
            **context,
            **_page_feedback(request),
            **_dialog_context(workspace=context.get("workspace")),
        },
    )


@app.get("/workspace/guide")
def workspace_guide(request: Request):
    return RedirectResponse(url="/?guide=1", status_code=303)


@app.get("/workspace/inspect-path")
def inspect_workspace_path(
    path_text: str,
    selection_kind: str,
    workspace_root: str = "",
):
    assessment = assess_workspace_path(
        path_text=path_text,
        selection_kind=selection_kind,
        workspace_root=workspace_root or None,
    )
    return JSONResponse(assessment.to_dict())


@app.get("/diagnostics/picker-bridge")
def picker_bridge_status():
    shell_context = SERVER_STATE.shell_context or _default_shell_context()
    diagnostics = picker_bridge_self_test(
        shell_mode=shell_context.shell_mode,
        window_attached=shell_context.native_dialog_expected,
    )
    shell_context.native_dialog_state = (
        "desktop_ready" if diagnostics.native_dialog_supported else "desktop_failed"
    )
    SERVER_STATE.shell_context = shell_context
    return JSONResponse(diagnostics.to_dict())


@app.post("/diagnostics/pick-folder")
def pick_folder_route(
    current_path: str = Form(""),
    workspace_root: str = Form(""),
):
    result = pick_folder_native(
        current_path=current_path,
        workspace_root=workspace_root,
    )
    return JSONResponse(result.to_dict())


@app.post("/diagnostics/pick-file")
def pick_file_route(
    current_path: str = Form(""),
    workspace_root: str = Form(""),
):
    result = pick_file_native(
        current_path=current_path,
        workspace_root=workspace_root,
    )
    return JSONResponse(result.to_dict())


@app.post("/workspace/create")
def create_workspace(
    save_parent_dir: str = Form(...),
    workspace_password: str = Form(...),
    workspace_label: str = Form(""),
):
    try:
        create_result = create_workspace_entry(
            save_parent_dir=save_parent_dir,
            workspace_password=workspace_password,
            workspace_label=workspace_label,
        )
        workspace = load_shared_workspace(create_result.workspace_root)
        lock_handle = acquire_workspace_write_lock(
            lock_path=workspace.lock_path(),
            workspace_id=workspace.manifest.workspace_id,
            app_kind="desktop-app",
        )
        _replace_current_session(
            WorkspaceSession(
                workspace_root=str(workspace.root()),
                workspace_password=workspace_password,
                readonly=False,
                app_kind="desktop-app",
                lock_handle=lock_handle,
            )
        )
        _remember_session_locally(SERVER_STATE.current_session)
    except Exception as exc:
        return _redirect_with_message("/", error=f"새 세이브 파일을 만들지 못했습니다: {exc}")
    return _redirect_with_message(
        "/settings",
        notice="새 세이브 파일을 만들었습니다. 다음으로 계정 연결을 확인해 주세요.",
        extra_params={"next": "check_connection"},
    )


@app.post("/workspace/open")
def open_workspace(
    workspace_root: str = Form(...),
    workspace_password: str = Form(...),
    readonly: bool = Form(False),
):
    try:
        open_result = open_workspace_entry(
            workspace_root=workspace_root,
            workspace_password=workspace_password,
            readonly_requested=readonly,
        )
        workspace = assert_supported_workspace(load_shared_workspace(open_result.workspace_root))
    except Exception as exc:
        detail = str(exc).strip() or "암호가 맞지 않거나 세이브 파일이 손상되었습니다."
        return _redirect_with_message("/", error=f"세이브 파일을 열지 못했습니다: {detail}")

    _, notice = _open_workspace_session(
        workspace=workspace,
        workspace_password=workspace_password,
        readonly_requested=readonly,
    )
    return _redirect_with_message(
        "/settings",
        notice=f"{notice} 다음으로 계정 연결을 확인해 주세요.",
        extra_params={"next": "check_connection"},
    )


@app.post("/workspace/close")
def close_workspace():
    SERVER_STATE.auto_restore_suppressed = True
    _replace_current_session(None)
    close_workspace_entry()
    return _redirect_with_message("/", notice="현재 세이브 파일을 닫았습니다.")


@app.post("/workspace/recent/remove")
def remove_recent_workspace(workspace_root: str = Form(...)):
    forget_workspace(workspace_root)
    device_secrets = load_local_device_secrets()
    if device_secrets.last_workspace_root == workspace_root:
        clear_last_workspace_secret()
    return _redirect_with_message("/", notice="최근 세이브 파일 목록에서 정리했습니다.")


@app.post("/workspace/recent/open")
def open_recent_workspace(workspace_root: str = Form(...)):
    device_secrets = load_local_device_secrets()
    if device_secrets.last_workspace_root != workspace_root or not device_secrets.last_workspace_password:
        return _redirect_with_message(
            "/",
            error="이 PC에 저장된 암호가 없어 바로 열 수 없습니다. 경로를 채운 뒤 암호를 입력해 열어 주세요.",
        )
    assessment = assess_workspace_path(
        path_text=workspace_root,
        selection_kind="workspace_open",
    )
    if assessment.status != "pass":
        return _redirect_with_message(
            "/",
            error=f"최근 세이브 파일을 바로 열지 못했습니다: {assessment.message}",
        )
    try:
        workspace = assert_supported_workspace(load_shared_workspace(workspace_root))
        _validate_workspace_password(workspace, device_secrets.last_workspace_password)
    except Exception as exc:
        detail = str(exc).strip() or "저장된 암호로 세이브 파일을 다시 열지 못했습니다."
        return _redirect_with_message(
            "/",
            error=f"최근 세이브 파일을 바로 열지 못했습니다: {detail}",
        )
    _, notice = _open_workspace_session(
        workspace=workspace,
        workspace_password=device_secrets.last_workspace_password,
        readonly_requested=False,
    )
    return _redirect_with_message(
        "/settings",
        notice=f"{notice} 이 PC에 저장된 암호로 바로 다시 열었습니다.",
        extra_params={"next": "check_connection"},
    )


@app.get("/settings", response_class=HTMLResponse)
def settings_page(request: Request):
    if SERVER_STATE.current_session is None:
        return _redirect_with_message("/", error="먼저 세이브 파일을 열어야 설정을 볼 수 있다.")
    context = _workspace_page_context(SERVER_STATE.current_session)
    return TEMPLATES.TemplateResponse(
        "settings.html",
        {
            "request": request,
            **context,
            "readonly": SERVER_STATE.current_session.readonly,
            **_page_feedback(request),
            **_dialog_context(workspace=context["workspace"]),
        },
    )


@app.post("/settings/save")
def save_settings(
    llm_model: str = Form("gpt-5.4"),
    llm_api_key: str = Form(""),
    email_address: str = Form(""),
    login_username: str = Form(""),
    mailbox_password: str = Form(""),
    default_folder: str = Form(""),
    template_workbook_relative_path: str = Form(""),
):
    session = SERVER_STATE.current_session
    if session is None:
        return _redirect_with_message("/", error="워크스페이스가 열려 있지 않아 설정을 저장할 수 없다.")
    if session.readonly:
        return _redirect_with_message("/settings", error="읽기 전용으로 열린 세이브 파일은 설정을 저장할 수 없다.")
    try:
        save_workspace_settings(
            workspace_root=session.workspace_root,
            workspace_password=session.workspace_password,
            llm_model=llm_model,
            llm_api_key=llm_api_key,
            email_address=email_address,
            login_username=login_username,
            mailbox_password=mailbox_password,
            default_folder=default_folder,
            template_workbook_relative_path=template_workbook_relative_path,
        )
    except HTTPException as exc:
        return _redirect_with_message("/settings", error=str(exc.detail))
    except Exception as exc:
        return _redirect_with_message("/settings", error=f"설정을 저장하지 못했습니다: {exc}")
    if session.lock_handle is not None:
        session.lock_handle.refresh()
    return _redirect_with_message(
        "/settings",
        notice="설정을 저장했습니다. 다음으로 계정 연결을 확인해 주세요.",
        extra_params={"saved": "1", "next": "check_connection"},
    )


@app.post("/settings/check-mailbox")
def check_mailbox_settings(
    llm_model: str = Form("gpt-5.4"),
    llm_api_key: str = Form(""),
    email_address: str = Form(""),
    login_username: str = Form(""),
    mailbox_password: str = Form(""),
    default_folder: str = Form(""),
    template_workbook_relative_path: str = Form(""),
):
    session = SERVER_STATE.current_session
    if session is None:
        return _redirect_with_message("/", error="워크스페이스가 열려 있지 않아 계정 연결 확인을 실행할 수 없다.")
    if session.readonly:
        return _redirect_with_message("/settings", error="읽기 전용으로 열린 세이브 파일은 계정 연결 확인을 실행할 수 없다.")

    workspace, secrets_store, _ = _workspace_objects(session)
    device_secrets = load_local_device_secrets()
    try:
        payload = secrets_store.read()
        current_llm = dict(payload.get("llm") or {})
        current_mailbox = dict(payload.get("mailbox") or {})
        current_exports = dict(payload.get("exports") or {})
        resolved_email = email_address.strip() or str(current_mailbox.get("email_address") or "")
        resolved_login_username = (
            login_username.strip() or str(current_mailbox.get("login_username") or "")
        )
        resolved_password = mailbox_password.strip() or str(current_mailbox.get("password") or "")
        resolved_api_key = (
            llm_api_key.strip()
            or str(current_llm.get("api_key") or "")
            or device_secrets.default_openai_api_key
        )
        if not resolved_email:
            raise RuntimeError("이메일 주소를 먼저 입력해 주세요.")
        if not resolved_password:
            raise RuntimeError("비밀번호 또는 앱 비밀번호를 먼저 입력해 주세요.")

        resolved_template_path = normalize_workspace_relative_input(
            workspace_root=str(workspace.root()),
            path_text=(
                template_workbook_relative_path.strip()
                or str(current_exports.get("template_workbook_relative_path") or "")
            ),
        )
    except HTTPException as exc:
        return _redirect_with_message("/settings", error=str(exc.detail))
    except Exception as exc:
        return _redirect_with_message("/settings", error=_friendly_mailbox_error_message(exc))
    if session.lock_handle is not None:
        session.lock_handle.refresh()
    _start_mailbox_check_job(
        session=session,
        resolved_email=resolved_email,
        resolved_login_username=resolved_login_username,
        resolved_password=resolved_password,
        llm_model=llm_model,
        resolved_api_key=resolved_api_key,
        default_folder=default_folder,
        resolved_template_path=resolved_template_path,
    )
    return _redirect_with_message(
        "/settings",
        notice="계정 연결 확인을 시작했습니다. 이 화면에서 진행 상태를 확인할 수 있습니다.",
        extra_params={"checked": "1"},
    )


@app.get("/review", response_class=HTMLResponse)
def review_center(
    request: Request,
):
    session = SERVER_STATE.current_session
    if session is None:
        return _redirect_with_message("/", error="먼저 세이브 파일을 열어야 리뷰센터를 볼 수 있다.")
    workspace, _, state_store = _workspace_objects(session)
    query = _review_query_from_request(request)
    page_result = load_review_center_page_service(
        workspace_root=session.workspace_root,
        search=str(query["search"]),
        triage_label=str(query["triage_label"]),
        export_only=bool(query["export_only"]),
        page=int(query["page"]),
        page_size=int(query["page_size"]),
        sort=str(query["sort"]),
        selected_bundle_id=str(query["selected_bundle_id"]),
    )
    resolved_query = {
        **query,
        "page": page_result.page,
        "page_size": page_result.page_size,
        "sort": page_result.sort,
        "selected_bundle_id": page_result.selected_bundle_id,
    }
    detail_result = load_review_detail_service(
        workspace_root=session.workspace_root,
        bundle_id=page_result.selected_bundle_id,
    )
    if detail_result.item is None and page_result.items:
        fallback_bundle_id = str(page_result.items[0].get("bundle_id") or "")
        if fallback_bundle_id:
            page_result.selected_bundle_id = fallback_bundle_id
            detail_result = load_review_detail_service(
                workspace_root=session.workspace_root,
                bundle_id=fallback_bundle_id,
            )
            resolved_query["selected_bundle_id"] = fallback_bundle_id
    display_items: list[dict[str, Any]] = []
    for item in page_result.items:
        bundle_id = str(item.get("bundle_id") or "")
        display_items.append(
            {
                **item,
                "selected": bundle_id == page_result.selected_bundle_id,
                "select_url": _review_url(
                    resolved_query,
                    selected_bundle_id=bundle_id,
                    artifact_kind="preview",
                ),
            }
        )
    artifact_preview = _load_review_artifact_preview(
        workspace=workspace,
        item=detail_result.item,
        kind=str(query["artifact_kind"]),
    )
    exports_summary = load_exports_summary_service(workspace_root=session.workspace_root)
    current_review_url = _review_url(resolved_query)
    base_hidden_fields = _review_hidden_fields(resolved_query)
    detail_base = {
        "selected_bundle_id": page_result.selected_bundle_id,
        "page": page_result.page,
        "page_size": page_result.page_size,
        "sort": page_result.sort,
    }
    artifact_tabs = [
        {
            "key": "preview",
            "label": "메일 미리보기",
            "url": _review_url(resolved_query, artifact_kind="preview", **detail_base),
            "active": str(query["artifact_kind"]) == "preview",
            "available": bool(detail_result.item and detail_result.item.get("preview_relpath")),
        },
        {
            "key": "raw",
            "label": "원본 메일 파일",
            "url": _review_url(resolved_query, artifact_kind="raw", **detail_base),
            "active": str(query["artifact_kind"]) == "raw",
            "available": bool(detail_result.item and detail_result.item.get("raw_eml_relpath")),
        },
        {
            "key": "summary",
            "label": "요약 메모",
            "url": _review_url(resolved_query, artifact_kind="summary", **detail_base),
            "active": str(query["artifact_kind"]) == "summary",
            "available": bool(detail_result.item and detail_result.item.get("summary_relpath")),
        },
        {
            "key": "record",
            "label": "추출 결과 원본",
            "url": _review_url(resolved_query, artifact_kind="record", **detail_base),
            "active": str(query["artifact_kind"]) == "record",
            "available": bool(detail_result.item and detail_result.item.get("extracted_record_relpath")),
        },
        {
            "key": "projected",
            "label": "엑셀 반영 미리보기",
            "url": _review_url(resolved_query, artifact_kind="projected", **detail_base),
            "active": str(query["artifact_kind"]) == "projected",
            "available": bool(detail_result.item and detail_result.item.get("projected_row_relpath")),
        },
    ]
    pagination = {
        "page": page_result.page,
        "page_count": page_result.page_count,
        "filtered_total_count": page_result.filtered_total_count,
        "has_previous": page_result.page > 1,
        "has_next": page_result.page < page_result.page_count,
        "previous_url": _review_url(resolved_query, page=page_result.page - 1) if page_result.page > 1 else "",
        "next_url": _review_url(resolved_query, page=page_result.page + 1) if page_result.page < page_result.page_count else "",
    }
    return TEMPLATES.TemplateResponse(
        "review.html",
        {
            "request": request,
            **_workspace_page_context(session),
            "items": display_items,
            "counts": state_store.summary_counts(),
            "readonly": session.readonly,
            "query": resolved_query,
            "review_page": page_result,
            "selected_item": detail_result.item,
            "artifact_preview": artifact_preview,
            "artifact_tabs": artifact_tabs,
            "exports_summary": exports_summary,
            "pagination": pagination,
            "current_review_url": current_review_url,
            "base_hidden_fields": base_hidden_fields,
            "page_size_options": [25, 50, 100],
            "sort_options": [
                ("received_desc", _review_sort_label("received_desc")),
                ("company_asc", _review_sort_label("company_asc")),
                ("sender_asc", _review_sort_label("sender_asc")),
            ],
            **_page_feedback(request),
            **_dialog_context(workspace=workspace),
        },
    )


@app.get("/admin/features", response_class=HTMLResponse)
def admin_features(request: Request):
    session = SERVER_STATE.current_session
    if session is None:
        return _redirect_with_message("/", error="먼저 세이브 파일을 열어야 관리도구를 볼 수 있다.")
    workspace, _, state_store = _workspace_objects(session)
    latest_runs = {
        item["feature_id"]: item
        for item in state_store.latest_feature_runs()
    }
    feature_entries: list[dict[str, Any]] = []
    for spec in list_feature_specs():
        try:
            checks = check_feature(
                feature_id=spec.feature_id,
                workspace_root=session.workspace_root if spec.requires_workspace else None,
                workspace_password=session.workspace_password if spec.requires_workspace else None,
            )
        except Exception as exc:
            checks = [
                {
                    "label": "feature_check_exception",
                    "status": "fail",
                    "detail": f"{exc.__class__.__name__}: {exc}",
                }
            ]
        normalized_checks = [
            item.to_dict() if hasattr(item, "to_dict") else item
            for item in checks
        ]
        feature_entries.append(
            {
                "spec": spec,
                "checks": normalized_checks,
                "latest_run": latest_runs.get(spec.feature_id),
                "run_disabled": session.readonly and spec.requires_write_lock,
            }
        )
    return TEMPLATES.TemplateResponse(
        "admin_features.html",
        {
            "request": request,
            "workspace": workspace,
            "feature_entries": feature_entries,
            "job_state": session.job_state,
            "feature_catalog_rows": feature_catalog_rows(),
            "readonly": session.readonly,
            **_page_feedback(request),
            **_dialog_context(workspace=workspace),
        },
    )


@app.post("/review/override/triage")
def save_triage_override(
    bundle_id: str = Form(...),
    triage_label: str = Form(...),
    return_to: str = Form("/review"),
):
    session = SERVER_STATE.current_session
    if session is None:
        return _redirect_with_message("/", error="먼저 세이브 파일을 열어야 분류를 저장할 수 있다.")
    if session.readonly:
        return _redirect_with_message(return_to, error="읽기 전용 세션에서는 분류 override를 저장할 수 없다.")
    workspace, secrets_store, state_store = _workspace_objects(session)
    state_store.save_user_override(
        bundle_id=bundle_id,
        override_triage_label=triage_label,
        override_notes="desktop-app triage override",
    )
    _reapply_latest_review_state(workspace=workspace, secrets_store=secrets_store, state_store=state_store)
    return _redirect_with_message(return_to, notice="분류 변경을 저장했습니다.")


@app.post("/review/override/representative")
def save_representative_override(
    bundle_id: str = Form(...),
    return_to: str = Form("/review"),
):
    session = SERVER_STATE.current_session
    if session is None:
        return _redirect_with_message("/", error="먼저 세이브 파일을 열어야 대표 메일을 지정할 수 있다.")
    if session.readonly:
        return _redirect_with_message(return_to, error="읽기 전용 세션에서는 대표 메일 override를 저장할 수 없다.")
    workspace, secrets_store, state_store = _workspace_objects(session)
    state_store.save_user_override(
        bundle_id=bundle_id,
        override_is_representative=True,
        override_notes="desktop-app representative override",
    )
    _reapply_latest_review_state(workspace=workspace, secrets_store=secrets_store, state_store=state_store)
    return _redirect_with_message(return_to, notice="엑셀 반영 대상을 저장했습니다.")


@app.post("/review/rebuild")
def rebuild_review_workbook(return_to: str = Form("/review")):
    session = SERVER_STATE.current_session
    if session is None:
        return _redirect_with_message("/", error="먼저 세이브 파일을 열어야 workbook을 재반영할 수 있다.")
    if session.readonly:
        return _redirect_with_message(return_to, error="읽기 전용 세션에서는 workbook을 재반영할 수 없다.")
    _start_feature_job(
        session=session,
        feature_id="exports.operating_workbook.rebuild",
        success_message="운영 엑셀을 다시 반영했습니다.",
    )
    return _redirect_with_message(return_to, notice="운영 엑셀 재반영을 시작했습니다.")


@app.get("/sync", response_class=HTMLResponse)
def sync_page(request: Request):
    session = SERVER_STATE.current_session
    if session is None:
        return _redirect_with_message("/", error="먼저 세이브 파일을 열어야 동기화 화면을 볼 수 있다.")
    context = _workspace_page_context(session)
    return TEMPLATES.TemplateResponse(
        "sync.html",
        {
            "request": request,
            **context,
            **_page_feedback(request),
            **_dialog_context(workspace=context["workspace"]),
        },
    )


@app.post("/sync")
def start_sync(
    sync_mode: str = Form("incremental_full"),
    scope: str = Form("recent"),
    limit: str = Form(""),
    preset_limit: str = Form("10"),
):
    session = SERVER_STATE.current_session
    if session is None:
        return _redirect_with_message("/", error="먼저 세이브 파일을 열어야 동기화를 시작할 수 있다.")
    if session.readonly:
        return _redirect_with_message("/sync", error="읽기 전용 세션에서는 동기화를 실행할 수 없다.")
    normalized_sync_mode = (sync_mode or "").strip() or "incremental_full"
    normalized_scope = (scope or "").strip().lower() or "recent"
    requested_limit: int | None = None
    if normalized_sync_mode == "quick_smoke":
        normalized_scope = "recent"
        requested_limit = 10
    elif normalized_scope == "all":
        requested_limit = None
    else:
        normalized_preset = (preset_limit or "").strip().lower()
        candidate_limit = (limit or "").strip()
        if not candidate_limit:
            if normalized_preset in {"", "custom"}:
                candidate_limit = "10"
            else:
                candidate_limit = normalized_preset
        try:
            requested_limit = int(candidate_limit)
        except ValueError:
            return _redirect_with_message("/sync", error="동기화 개수는 숫자로 입력해야 합니다.")
        if requested_limit <= 0:
            return _redirect_with_message("/sync", error="동기화 개수는 1 이상의 숫자여야 합니다.")

    _start_sync_job(
        session=session,
        sync_mode=normalized_sync_mode,
        scope=normalized_scope,
        limit=requested_limit,
    )
    if normalized_scope == "all":
        notice = "전체 동기화를 시작했습니다. 진행 상황과 결과 요약이 이 화면에 표시됩니다."
    elif requested_limit == 10:
        notice = "빠른 테스트 동기화를 시작했습니다. 최근 10건 기준 진행 상태가 이 화면에 표시됩니다."
    else:
        notice = f"최근 {requested_limit}건 동기화를 시작했습니다. 진행 상황과 결과 요약이 이 화면에 표시됩니다."
    return _redirect_with_message("/sync", notice=notice)


@app.post("/admin/features/run")
def run_admin_feature(feature_id: str = Form(...)):
    session = SERVER_STATE.current_session
    if session is None:
        return _redirect_with_message("/", error="먼저 세이브 파일을 열어야 관리도구 feature를 실행할 수 있다.")
    spec = next((item for item in list_feature_specs() if item.feature_id == feature_id), None)
    if spec is None:
        return _redirect_with_message("/admin/features", error=f"알 수 없는 feature다: {feature_id}")
    if session.readonly and spec.requires_write_lock:
        return _redirect_with_message("/admin/features", error="읽기 전용 세션에서는 이 feature를 실행할 수 없다.")
    _start_feature_job(
        session=session,
        feature_id=feature_id,
        success_message=f"{spec.title} 실행이 완료되었다.",
    )
    return _redirect_with_message("/admin/features", notice=f"{spec.title} 실행을 시작했습니다.")


@app.get("/jobs/current")
def current_job():
    session = SERVER_STATE.current_session
    if session is None:
        return JSONResponse({"status": "no_workspace", "message": "세이브 파일이 열려 있지 않습니다."})
    return JSONResponse(session.job_state.to_dict())


@app.post("/actions/open-path")
def open_relative_path(
    relative_path: str = Form(...),
    return_to: str = Form("/review"),
):
    session = SERVER_STATE.current_session
    if session is None:
        return _redirect_with_message("/", error="먼저 세이브 파일을 열어야 원본 경로를 열 수 있다.")
    workspace, _, _ = _workspace_objects(session)
    target = workspace.from_workspace_relative(relative_path).resolve()
    if not target.is_relative_to(workspace.root().resolve()):
        return _redirect_with_message(return_to, error="워크스페이스 밖 경로는 열 수 없다.")
    _open_path_in_os(target)
    return _redirect_with_message(return_to, notice="선택한 파일 또는 폴더를 열었습니다.")


@app.get("/review/artifact", response_class=HTMLResponse)
def review_artifact_preview(bundle_id: str, kind: str = "preview"):
    session = SERVER_STATE.current_session
    if session is None:
        raise HTTPException(status_code=400, detail="먼저 세이브 파일을 열어야 합니다.")
    workspace, _, _ = _workspace_objects(session)
    detail_result = load_review_detail_service(
        workspace_root=session.workspace_root,
        bundle_id=bundle_id,
    )
    artifact = _load_review_artifact_preview(
        workspace=workspace,
        item=detail_result.item,
        kind=kind,
    )
    if artifact is None:
        return HTMLResponse(
            "<div style='padding:20px;font-family:Segoe UI,Malgun Gothic,sans-serif;color:#5b6678'>표시할 내용을 찾지 못했습니다.</div>"
        )
    if artifact["content_type"] == "html":
        return HTMLResponse(str(artifact["content"]))
    return HTMLResponse(
        "<!doctype html><html lang='ko'><head><meta charset='utf-8'>"
        "<style>body{margin:0;padding:20px;font-family:'Segoe UI','Malgun Gothic',sans-serif;background:#fff;color:#111827}"
        "pre{white-space:pre-wrap;word-break:break-word;font:13px/1.65 Consolas,'SFMono-Regular',monospace}"
        "</style></head><body><pre>"
        + escape(str(artifact["content"]))
        + "</pre></body></html>"
    )


def _reapply_latest_review_state(*, workspace, secrets_store, state_store) -> None:
    latest_json = workspace.review_logs_root() / "latest_inbox_review_board.json"
    if not latest_json.exists():
        return
    ingest_review_report_into_state(
        workspace=workspace,
        state_store=state_store,
        report_path=latest_json,
    )
    payload = secrets_store.read()
    wrapper = OpenAIResponsesWrapper(
        OpenAIResponsesConfig(
            model=str((payload.get("llm") or {}).get("model") or "gpt-5.4"),
            api_key=str((payload.get("llm") or {}).get("api_key") or ""),
            usage_log_path=str(workspace.profile_paths().llm_usage_log_path()),
        )
    )
    template_relpath = str((payload.get("exports") or {}).get("template_workbook_relative_path") or "")
    if not template_relpath:
        return
    rebuild_operating_workbook(
        workspace=workspace,
        state_store=state_store,
        template_path=workspace.from_workspace_relative(template_relpath),
        wrapper=wrapper,
    )


def _start_feature_job(
    *,
    session: WorkspaceSession,
    feature_id: str,
    success_message: str,
) -> None:
    if session.job_state.status == "running":
        return

    _set_job_state(
        session,
        status="running",
        feature_id=feature_id,
        message="작업을 시작했습니다.",
        stage_id="running",
        stage_label="실행 중",
        progress_current=0,
        progress_total=1,
        next_action="잠시만 기다려 주세요.",
        details=[f"{feature_id} 실행을 준비하고 있습니다."],
    )

    def _run() -> None:
        try:
            result = run_feature(
                feature_id=feature_id,
                workspace_root=session.workspace_root,
                workspace_password=session.workspace_password,
                app_kind=session.app_kind,
                trigger_source="desktop-admin" if feature_id != "runtime.workspace.sync" else "desktop-home",
                existing_lock_handle=session.lock_handle,
            )
            _set_job_state(
                session,
                status=result.status,
                message=success_message,
                feature_id=feature_id,
                stage_id="complete",
                stage_label="완료",
                progress_current=1,
                progress_total=1,
                next_action="결과 화면이나 로그를 확인해 주세요.",
                details=list(result.notes),
                last_result=result.to_dict(),
                preserve_started_at=True,
            )
        except Exception as exc:
            _set_job_state(
                session,
                status="failed",
                message="작업 실행 중 오류가 발생했습니다.",
                feature_id=feature_id,
                stage_id="failed",
                stage_label="실패",
                progress_current=1,
                progress_total=1,
                next_action="설정이나 로그를 확인한 뒤 다시 시도해 주세요.",
                details=[f"{exc.__class__.__name__}: {exc}"],
                last_result=None,
                preserve_started_at=True,
            )

    threading.Thread(target=_run, daemon=True).start()


def _open_path_in_os(target: Path) -> None:
    if os.name == "nt":
        os.startfile(str(target))  # type: ignore[attr-defined]
        return
    if os.name == "posix":
        command = ["open" if sys.platform == "darwin" else "xdg-open", str(target)]
        subprocess.Popen(command)
        return
    raise RuntimeError(f"지원하지 않는 OS 경로 열기 방식이다: {os.name}")
