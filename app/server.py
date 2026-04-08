"""전용 데스크톱 창 안에서 쓰는 로컬 Web UI 서버."""

from __future__ import annotations

from dataclasses import dataclass, field
import os
from pathlib import Path
import subprocess
import sys
import threading
from typing import Any

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from llm import OpenAIResponsesConfig, OpenAIResponsesWrapper
from runtime import (
    LockedWorkspaceError,
    WorkspaceSecretsStore,
    WorkspaceStateStore,
    acquire_workspace_write_lock,
    create_shared_workspace,
    default_local_settings_path,
    ingest_review_report_into_state,
    load_local_app_settings,
    load_shared_workspace,
    remember_workspace,
    rebuild_operating_workbook,
    run_workspace_sync,
)


TEMPLATES = Jinja2Templates(directory=str(Path(__file__).resolve().parent / "templates"))


@dataclass(slots=True)
class BackgroundJobState:
    status: str = "idle"
    message: str = ""
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


SERVER_STATE = ServerState()
app = FastAPI(title="Email Pilot AI Desktop")


def _workspace_objects(session: WorkspaceSession):
    workspace = load_shared_workspace(session.workspace_root)
    secrets_store = WorkspaceSecretsStore(
        path=str(workspace.secure_blob_path()),
        password=session.workspace_password,
    )
    state_store = WorkspaceStateStore(workspace.state_db_path())
    state_store.ensure_schema()
    return workspace, secrets_store, state_store


def _session_context() -> dict[str, Any]:
    local_settings = load_local_app_settings()
    session = SERVER_STATE.current_session
    if session is None:
        return {
            "workspace_open": False,
            "recent_workspaces": local_settings.recent_workspaces,
            "local_settings_path": str(default_local_settings_path()),
        }

    workspace, secrets_store, state_store = _workspace_objects(session)
    return {
        "workspace_open": True,
        "session": session,
        "workspace": workspace,
        "shared_settings": secrets_store.masked_summary(),
        "state_counts": state_store.summary_counts(),
        "latest_sync_run": state_store.latest_sync_run(),
        "recent_workspaces": load_local_app_settings().recent_workspaces,
        "local_settings_path": str(default_local_settings_path()),
    }


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    context = _session_context()
    return TEMPLATES.TemplateResponse(
        "home.html",
        {"request": request, **context},
    )


@app.post("/workspace/create")
def create_workspace(
    workspace_root: str = Form(...),
    workspace_password: str = Form(...),
    workspace_label: str = Form(""),
    import_profile_root: str = Form(""),
):
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
    SERVER_STATE.current_session = WorkspaceSession(
        workspace_root=str(workspace.root()),
        workspace_password=workspace_password,
        readonly=False,
        app_kind="desktop-app",
        lock_handle=lock_handle,
    )
    remember_workspace(str(workspace.root()))
    return RedirectResponse(url="/", status_code=303)


@app.post("/workspace/open")
def open_workspace(
    workspace_root: str = Form(...),
    workspace_password: str = Form(...),
    readonly: bool = Form(False),
):
    workspace = load_shared_workspace(workspace_root)
    lock_handle = None
    if not readonly:
        try:
            lock_handle = acquire_workspace_write_lock(
                lock_path=workspace.lock_path(),
                workspace_id=workspace.manifest.workspace_id,
                app_kind="desktop-app",
            )
        except LockedWorkspaceError:
            readonly = True
    SERVER_STATE.current_session = WorkspaceSession(
        workspace_root=str(workspace.root()),
        workspace_password=workspace_password,
        readonly=readonly,
        app_kind="desktop-app",
        lock_handle=lock_handle,
    )
    remember_workspace(str(workspace.root()))
    return RedirectResponse(url="/", status_code=303)


@app.post("/workspace/close")
def close_workspace():
    session = SERVER_STATE.current_session
    if session and session.lock_handle is not None:
        session.lock_handle.release()
    SERVER_STATE.current_session = None
    return RedirectResponse(url="/", status_code=303)


@app.get("/settings", response_class=HTMLResponse)
def settings_page(request: Request):
    if SERVER_STATE.current_session is None:
        return RedirectResponse(url="/", status_code=303)
    workspace, secrets_store, _ = _workspace_objects(SERVER_STATE.current_session)
    return TEMPLATES.TemplateResponse(
        "settings.html",
        {
            "request": request,
            "workspace": workspace,
            "shared_settings": secrets_store.masked_summary(),
            "readonly": SERVER_STATE.current_session.readonly,
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
        raise HTTPException(status_code=400, detail="워크스페이스가 열려 있지 않다.")
    if session.readonly:
        raise HTTPException(status_code=409, detail="읽기 전용으로 열린 워크스페이스는 저장할 수 없다.")

    workspace, secrets_store, _ = _workspace_objects(session)
    payload = secrets_store.read()
    current_llm = dict(payload.get("llm") or {})
    current_mailbox = dict(payload.get("mailbox") or {})
    current_exports = dict(payload.get("exports") or {})
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
        "template_workbook_relative_path": _normalize_workspace_relative_input(
            workspace=workspace,
            path_text=(
                template_workbook_relative_path.strip()
                or str(current_exports.get("template_workbook_relative_path") or "")
            ),
        ),
        "operating_workbook_relative_path": workspace.to_workspace_relative(
            workspace.operating_workbook_path()
        ),
    }
    secrets_store.write(payload)
    if session.lock_handle is not None:
        session.lock_handle.refresh()
    return RedirectResponse(url="/settings", status_code=303)


@app.get("/review", response_class=HTMLResponse)
def review_center(
    request: Request,
    search: str = "",
    triage_label: str = "",
    export_only: bool = False,
):
    session = SERVER_STATE.current_session
    if session is None:
        return RedirectResponse(url="/", status_code=303)
    workspace, _, state_store = _workspace_objects(session)
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
            "query": {
                "search": search,
                "triage_label": triage_label,
                "export_only": export_only,
            },
        },
    )


@app.post("/review/override/triage")
def save_triage_override(bundle_id: str = Form(...), triage_label: str = Form(...)):
    session = SERVER_STATE.current_session
    if session is None:
        raise HTTPException(status_code=400, detail="워크스페이스가 열려 있지 않다.")
    if session.readonly:
        raise HTTPException(status_code=409, detail="읽기 전용 세션에서는 override를 저장할 수 없다.")
    workspace, secrets_store, state_store = _workspace_objects(session)
    state_store.save_user_override(
        bundle_id=bundle_id,
        override_triage_label=triage_label,
        override_notes="desktop-app triage override",
    )
    _reapply_latest_review_state(workspace=workspace, secrets_store=secrets_store, state_store=state_store)
    return RedirectResponse(url="/review", status_code=303)


@app.post("/review/override/representative")
def save_representative_override(bundle_id: str = Form(...)):
    session = SERVER_STATE.current_session
    if session is None:
        raise HTTPException(status_code=400, detail="워크스페이스가 열려 있지 않다.")
    if session.readonly:
        raise HTTPException(status_code=409, detail="읽기 전용 세션에서는 override를 저장할 수 없다.")
    workspace, secrets_store, state_store = _workspace_objects(session)
    state_store.save_user_override(
        bundle_id=bundle_id,
        override_is_representative=True,
        override_notes="desktop-app representative override",
    )
    _reapply_latest_review_state(workspace=workspace, secrets_store=secrets_store, state_store=state_store)
    return RedirectResponse(url="/review", status_code=303)


@app.post("/sync")
def start_sync():
    session = SERVER_STATE.current_session
    if session is None:
        raise HTTPException(status_code=400, detail="워크스페이스가 열려 있지 않다.")
    if session.job_state.status == "running":
        return RedirectResponse(url="/", status_code=303)

    session.job_state = BackgroundJobState(status="running", message="동기화를 시작했다.")

    def _run() -> None:
        try:
            result = run_workspace_sync(
                workspace_root=session.workspace_root,
                workspace_password=session.workspace_password,
                app_kind=session.app_kind,
            )
            session.job_state = BackgroundJobState(
                status="completed",
                message="동기화가 완료되었다.",
                last_result=result.to_dict(),
            )
        except Exception as exc:
            session.job_state = BackgroundJobState(
                status="failed",
                message=f"{exc.__class__.__name__}: {exc}",
                last_result=None,
            )

    threading.Thread(target=_run, daemon=True).start()
    return RedirectResponse(url="/", status_code=303)


@app.get("/jobs/current")
def current_job():
    session = SERVER_STATE.current_session
    if session is None:
        return JSONResponse({"status": "no_workspace"})
    return JSONResponse(
        {
            "status": session.job_state.status,
            "message": session.job_state.message,
            "last_result": session.job_state.last_result,
        }
    )


@app.get("/open-path")
def open_relative_path(relative_path: str):
    session = SERVER_STATE.current_session
    if session is None:
        raise HTTPException(status_code=400, detail="워크스페이스가 열려 있지 않다.")
    workspace, _, _ = _workspace_objects(session)
    target = workspace.from_workspace_relative(relative_path).resolve()
    if not target.is_relative_to(workspace.root().resolve()):
        raise HTTPException(status_code=400, detail="워크스페이스 밖 경로는 열 수 없다.")
    _open_path_in_os(target)
    return RedirectResponse(url="/review", status_code=303)


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
