"""전용 데스크톱 창 안에서 쓰는 로컬 Web UI 서버."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
import os
from pathlib import Path
import subprocess
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
    LockedWorkspaceError,
    WorkspaceSecretsStore,
    WorkspaceStateStore,
    acquire_workspace_write_lock,
    assess_workspace_path,
    check_feature,
    create_shared_workspace,
    default_local_portable_exe_path,
    default_local_portable_bundle_root,
    default_local_settings_path,
    default_startup_log_path,
    feature_catalog_rows,
    ingest_review_report_into_state,
    list_feature_specs,
    load_local_app_settings,
    load_shared_workspace,
    remember_workspace,
    rebuild_operating_workbook,
    run_feature,
)


TEMPLATES = Jinja2Templates(directory=str(Path(__file__).resolve().parent / "templates"))
STATIC_ROOT = Path(__file__).resolve().parent / "static"


@dataclass(slots=True)
class BackgroundJobState:
    status: str = "idle"
    message: str = ""
    feature_id: str = ""
    last_result: dict[str, Any] | None = None


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


def _workspace_objects(session: WorkspaceSession):
    workspace = load_shared_workspace(session.workspace_root)
    secrets_store = WorkspaceSecretsStore(
        path=str(workspace.secure_blob_path()),
        password=session.workspace_password,
    )
    state_store = WorkspaceStateStore(workspace.state_db_path())
    state_store.ensure_schema()
    return workspace, secrets_store, state_store


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
    return {
        "notice": str(request.query_params.get("notice") or ""),
        "error": str(request.query_params.get("error") or ""),
        "current_path": request.url.path,
    }


def _dialog_context(*, workspace=None) -> dict[str, Any]:
    shell_context = SERVER_STATE.shell_context or _default_shell_context()
    return {
        "native_dialog_supported": True,
        "dialog_workspace_root": str(workspace.root()) if workspace is not None else "",
        "shell_context": shell_context.to_template_dict(),
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


def _template_status(*, workspace, shared_settings: dict[str, Any]) -> dict[str, str]:
    relative_path = str((shared_settings.get("exports") or {}).get("template_workbook_relative_path") or "")
    if not relative_path:
        return {
            "status": "warn",
            "message": "아직 템플릿 경로가 저장되지 않았다.",
            "relative_path": "",
            "resolved_path": "",
        }
    assessment = assess_workspace_path(
        path_text=relative_path,
        selection_kind="template_file",
        workspace_root=workspace.root(),
    )
    resolved = ""
    if assessment.normalized_path:
        try:
            resolved = str(workspace.from_workspace_relative(relative_path).resolve(strict=False))
        except Exception:
            resolved = assessment.normalized_path
    return {
        "status": assessment.status,
        "message": assessment.message,
        "relative_path": relative_path,
        "resolved_path": resolved,
    }


def _session_context() -> dict[str, Any]:
    local_settings = load_local_app_settings()
    session = SERVER_STATE.current_session
    if session is None:
        return {
            "workspace_open": False,
            "recent_workspaces": local_settings.recent_workspaces,
            "local_settings_path": str(default_local_settings_path()),
            "last_open_workspace": local_settings.last_open_workspace,
        }

    workspace, secrets_store, state_store = _workspace_objects(session)
    shared_settings = secrets_store.masked_summary()
    return {
        "workspace_open": True,
        "session": session,
        "workspace": workspace,
        "shared_settings": shared_settings,
        "state_counts": state_store.summary_counts(),
        "latest_sync_run": state_store.latest_sync_run(),
        "latest_feature_runs": state_store.latest_feature_runs(),
        "feature_spec_count": len(list_feature_specs()),
        "recent_workspaces": load_local_app_settings().recent_workspaces,
        "local_settings_path": str(default_local_settings_path()),
        "last_open_workspace": load_local_app_settings().last_open_workspace,
        "template_status": _template_status(workspace=workspace, shared_settings=shared_settings),
    }


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    context = _session_context()
    return TEMPLATES.TemplateResponse(
        "home.html",
        {"request": request, **context, **_page_feedback(request), **_dialog_context(workspace=context.get("workspace"))},
    )


@app.get("/workspace/guide", response_class=HTMLResponse)
def workspace_guide(request: Request):
    context = _session_context()
    return TEMPLATES.TemplateResponse(
        "workspace_guide.html",
        {
            "request": request,
            **context,
            **_page_feedback(request),
            **_dialog_context(workspace=context.get("workspace")),
        },
    )


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


@app.post("/workspace/create")
def create_workspace(
    workspace_root: str = Form(...),
    workspace_password: str = Form(...),
    workspace_label: str = Form(""),
    import_profile_root: str = Form(""),
):
    try:
        workspace = create_shared_workspace(
            workspace_root=workspace_root,
            workspace_password=workspace_password,
            workspace_label=workspace_label,
            import_profile_root=import_profile_root.strip() or None,
        )
        lock_handle = acquire_workspace_write_lock(
            lock_path=workspace.lock_path(),
            workspace_id=workspace.manifest.workspace_id,
            app_kind="desktop-app",
        )
        _replace_current_session(WorkspaceSession(
            workspace_root=str(workspace.root()),
            workspace_password=workspace_password,
            readonly=False,
            app_kind="desktop-app",
            lock_handle=lock_handle,
        ))
        remember_workspace(str(workspace.root()))
    except Exception as exc:
        return _redirect_with_message("/", error=f"새 세이브 파일을 만들지 못했다: {exc}")
    return _redirect_with_message("/", notice="새 세이브 파일을 만들고 바로 열었다.")


@app.post("/workspace/open")
def open_workspace(
    workspace_root: str = Form(...),
    workspace_password: str = Form(...),
    readonly: bool = Form(False),
):
    try:
        workspace = load_shared_workspace(workspace_root)
        _validate_workspace_password(workspace, workspace_password)
    except Exception as exc:
        detail = str(exc).strip() or "암호가 맞지 않거나 세이브 파일이 손상되었다."
        return _redirect_with_message("/", error=f"세이브 파일을 열지 못했다: {detail}")

    lock_handle = None
    notice = "세이브 파일을 열었다."
    if not readonly:
        try:
            lock_handle = acquire_workspace_write_lock(
                lock_path=workspace.lock_path(),
                workspace_id=workspace.manifest.workspace_id,
                app_kind="desktop-app",
            )
        except LockedWorkspaceError:
            readonly = True
            notice = "잠금 때문에 읽기 전용으로 세이브 파일을 열었다."
    _replace_current_session(WorkspaceSession(
        workspace_root=str(workspace.root()),
        workspace_password=workspace_password,
        readonly=readonly,
        app_kind="desktop-app",
        lock_handle=lock_handle,
    ))
    remember_workspace(str(workspace.root()))
    return _redirect_with_message("/", notice=notice)


@app.post("/workspace/close")
def close_workspace():
    _replace_current_session(None)
    return _redirect_with_message("/", notice="세이브 파일을 닫았다.")


@app.get("/settings", response_class=HTMLResponse)
def settings_page(request: Request):
    if SERVER_STATE.current_session is None:
        return _redirect_with_message("/", error="먼저 세이브 파일을 열어야 설정을 볼 수 있다.")
    workspace, secrets_store, _ = _workspace_objects(SERVER_STATE.current_session)
    shared_settings = secrets_store.masked_summary()
    return TEMPLATES.TemplateResponse(
        "settings.html",
        {
            "request": request,
            "workspace": workspace,
            "shared_settings": shared_settings,
            "readonly": SERVER_STATE.current_session.readonly,
            "template_status": _template_status(workspace=workspace, shared_settings=shared_settings),
            **_page_feedback(request),
            **_dialog_context(workspace=workspace),
        },
    )


@app.post("/settings/save")
def save_settings(
    llm_model: str = Form("gpt-5.4"),
    llm_api_key: str = Form(""),
    email_address: str = Form(""),
    login_username: str = Form(""),
    mailbox_password: str = Form(""),
    default_folder: str = Form("INBOX"),
    template_workbook_relative_path: str = Form(""),
):
    session = SERVER_STATE.current_session
    if session is None:
        return _redirect_with_message("/", error="워크스페이스가 열려 있지 않아 설정을 저장할 수 없다.")
    if session.readonly:
        return _redirect_with_message("/settings", error="읽기 전용으로 열린 세이브 파일은 설정을 저장할 수 없다.")

    workspace, secrets_store, _ = _workspace_objects(session)
    try:
        payload = secrets_store.read()
        current_llm = dict(payload.get("llm") or {})
        current_mailbox = dict(payload.get("mailbox") or {})
        current_exports = dict(payload.get("exports") or {})
        resolved_template_path = _normalize_workspace_relative_input(
            workspace=workspace,
            path_text=(
                template_workbook_relative_path.strip()
                or str(current_exports.get("template_workbook_relative_path") or "")
            ),
        )
        payload["workspace"] = {
            **dict(payload.get("workspace") or {}),
            "settings_saved_at": datetime.now().isoformat(timespec="seconds"),
        }
        payload["llm"] = {
            "api_key": llm_api_key.strip() or str(current_llm.get("api_key") or ""),
            "model": llm_model.strip() or "gpt-5.4",
        }
        payload["mailbox"] = {
            "email_address": email_address.strip() or str(current_mailbox.get("email_address") or ""),
            "login_username": login_username.strip() or str(current_mailbox.get("login_username") or ""),
            "password": mailbox_password.strip() or str(current_mailbox.get("password") or ""),
            "default_folder": default_folder.strip() or "INBOX",
        }
        payload["exports"] = {
            "template_workbook_relative_path": resolved_template_path,
            "operating_workbook_relative_path": workspace.to_workspace_relative(
                workspace.operating_workbook_path()
            ),
        }
        secrets_store.write(payload)
    except HTTPException as exc:
        return _redirect_with_message("/settings", error=str(exc.detail))
    except Exception as exc:
        return _redirect_with_message("/settings", error=f"설정을 저장하지 못했다: {exc}")
    if session.lock_handle is not None:
        session.lock_handle.refresh()
    return _redirect_with_message("/settings", notice="설정을 저장했다.", extra_params={"saved": "1"})


@app.get("/review", response_class=HTMLResponse)
def review_center(
    request: Request,
    search: str = "",
    triage_label: str = "",
    export_only: bool = False,
):
    session = SERVER_STATE.current_session
    if session is None:
        return _redirect_with_message("/", error="먼저 세이브 파일을 열어야 리뷰센터를 볼 수 있다.")
    workspace, _, state_store = _workspace_objects(session)
    local_settings = load_local_app_settings()
    local_settings.last_review_filters = {
        "search": search,
        "triage_label": triage_label,
        "export_only": "true" if export_only else "false",
    }
    from runtime import save_local_app_settings

    save_local_app_settings(local_settings)
    items = state_store.list_review_items(
        search=search,
        triage_label=triage_label,
        export_only=export_only,
    )
    return TEMPLATES.TemplateResponse(
        "review.html",
        {
            "request": request,
            "workspace": workspace,
            "items": items,
            "counts": state_store.summary_counts(),
            "readonly": session.readonly,
            "query": {
                "search": search,
                "triage_label": triage_label,
                "export_only": export_only,
            },
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
def save_triage_override(bundle_id: str = Form(...), triage_label: str = Form(...)):
    session = SERVER_STATE.current_session
    if session is None:
        return _redirect_with_message("/", error="먼저 세이브 파일을 열어야 분류를 저장할 수 있다.")
    if session.readonly:
        return _redirect_with_message("/review", error="읽기 전용 세션에서는 분류 override를 저장할 수 없다.")
    workspace, secrets_store, state_store = _workspace_objects(session)
    state_store.save_user_override(
        bundle_id=bundle_id,
        override_triage_label=triage_label,
        override_notes="desktop-app triage override",
    )
    _reapply_latest_review_state(workspace=workspace, secrets_store=secrets_store, state_store=state_store)
    return _redirect_with_message("/review", notice="분류 override를 저장했다.")


@app.post("/review/override/representative")
def save_representative_override(bundle_id: str = Form(...)):
    session = SERVER_STATE.current_session
    if session is None:
        return _redirect_with_message("/", error="먼저 세이브 파일을 열어야 대표 메일을 지정할 수 있다.")
    if session.readonly:
        return _redirect_with_message("/review", error="읽기 전용 세션에서는 대표 메일 override를 저장할 수 없다.")
    workspace, secrets_store, state_store = _workspace_objects(session)
    state_store.save_user_override(
        bundle_id=bundle_id,
        override_is_representative=True,
        override_notes="desktop-app representative override",
    )
    _reapply_latest_review_state(workspace=workspace, secrets_store=secrets_store, state_store=state_store)
    return _redirect_with_message("/review", notice="대표 메일 override를 저장했다.")


@app.post("/review/rebuild")
def rebuild_review_workbook():
    session = SERVER_STATE.current_session
    if session is None:
        return _redirect_with_message("/", error="먼저 세이브 파일을 열어야 workbook을 재반영할 수 있다.")
    if session.readonly:
        return _redirect_with_message("/review", error="읽기 전용 세션에서는 workbook을 재반영할 수 없다.")
    _start_feature_job(
        session=session,
        feature_id="exports.operating_workbook.rebuild",
        success_message="운영 workbook 재반영이 완료되었다.",
    )
    return _redirect_with_message("/review", notice="운영 workbook 재반영 작업을 시작했다.")


@app.post("/sync")
def start_sync():
    session = SERVER_STATE.current_session
    if session is None:
        return _redirect_with_message("/", error="먼저 세이브 파일을 열어야 동기화를 시작할 수 있다.")
    if session.readonly:
        return _redirect_with_message("/", error="읽기 전용 세션에서는 동기화를 실행할 수 없다.")
    _start_feature_job(
        session=session,
        feature_id="runtime.workspace.sync",
        success_message="동기화가 완료되었다.",
    )
    return _redirect_with_message("/", notice="동기화 작업을 시작했다.")


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
    return _redirect_with_message("/admin/features", notice=f"{spec.title} 실행을 시작했다.")


@app.get("/jobs/current")
def current_job():
    session = SERVER_STATE.current_session
    if session is None:
        return JSONResponse({"status": "no_workspace"})
    return JSONResponse(
        {
            "status": session.job_state.status,
            "message": session.job_state.message,
            "feature_id": session.job_state.feature_id,
            "last_result": session.job_state.last_result,
        }
    )


@app.get("/open-path")
def open_relative_path(relative_path: str):
    session = SERVER_STATE.current_session
    if session is None:
        return _redirect_with_message("/", error="먼저 세이브 파일을 열어야 원본 경로를 열 수 있다.")
    workspace, _, _ = _workspace_objects(session)
    target = workspace.from_workspace_relative(relative_path).resolve()
    if not target.is_relative_to(workspace.root().resolve()):
        return _redirect_with_message("/review", error="워크스페이스 밖 경로는 열 수 없다.")
    _open_path_in_os(target)
    return _redirect_with_message("/review", notice="선택한 원본 경로를 열었다.")


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

    session.job_state = BackgroundJobState(
        status="running",
        message=f"{feature_id} 실행을 시작했다.",
        feature_id=feature_id,
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
            session.job_state = BackgroundJobState(
                status=result.status,
                message=success_message,
                feature_id=feature_id,
                last_result=result.to_dict(),
            )
        except Exception as exc:
            session.job_state = BackgroundJobState(
                status="failed",
                message=f"{exc.__class__.__name__}: {exc}",
                feature_id=feature_id,
                last_result=None,
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


def _normalize_workspace_relative_input(*, workspace, path_text: str) -> str:
    text = path_text.strip()
    if not text:
        return ""
    candidate = Path(text)
    if candidate.is_absolute():
        resolved = candidate.resolve()
        if not resolved.is_relative_to(workspace.root().resolve()):
            raise HTTPException(
                status_code=400,
                detail="공유 워크스페이스 밖 절대경로는 저장할 수 없다.",
            )
        return workspace.to_workspace_relative(resolved)
    return candidate.as_posix()
