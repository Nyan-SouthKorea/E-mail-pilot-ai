"""세이브 파일 설정의 공용 service를 모은다."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

from runtime.device_secret_store import (
    load_local_device_secrets,
    remember_default_openai_api_key,
    sanitize_openai_api_key,
)
from runtime.secrets_store import WorkspaceSecretsStore
from runtime.workspace import assess_workspace_path, load_shared_workspace


@dataclass(slots=True)
class WorkspaceSettingsSummary:
    workspace_root: str
    shared_settings: dict[str, object]
    template_status: dict[str, str]
    default_openai_api_key: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def load_workspace_settings_summary(
    *,
    workspace_root: str,
    workspace_password: str,
) -> WorkspaceSettingsSummary:
    workspace = load_shared_workspace(workspace_root)
    secrets_store = WorkspaceSecretsStore(
        path=str(workspace.secure_blob_path()),
        password=workspace_password,
    )
    shared_settings = secrets_store.masked_summary()
    device_secrets = load_local_device_secrets()
    return WorkspaceSettingsSummary(
        workspace_root=str(workspace.root()),
        shared_settings=shared_settings,
        template_status=template_status_for_workspace(
            workspace_root=str(workspace.root()),
            shared_settings=shared_settings,
        ),
        default_openai_api_key=device_secrets.default_openai_api_key,
    )


def save_workspace_settings(
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
    classification_guidance: str = "",
) -> WorkspaceSettingsSummary:
    workspace = load_shared_workspace(workspace_root)
    secrets_store = WorkspaceSecretsStore(
        path=str(workspace.secure_blob_path()),
        password=workspace_password,
    )
    device_secrets = load_local_device_secrets()
    payload = secrets_store.read()
    current_llm = dict(payload.get("llm") or {})
    current_mailbox = dict(payload.get("mailbox") or {})
    current_exports = dict(payload.get("exports") or {})
    current_analysis = dict(payload.get("analysis") or {})
    resolved_api_key = (
        sanitize_openai_api_key(llm_api_key)
        or sanitize_openai_api_key(str(current_llm.get("api_key") or ""))
        or sanitize_openai_api_key(device_secrets.default_openai_api_key)
    )
    resolved_template_path = normalize_workspace_relative_input(
        workspace_root=str(workspace.root()),
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
        "api_key": resolved_api_key,
        "model": llm_model.strip() or "gpt-5.4",
    }
    payload["mailbox"] = {
        **current_mailbox,
        "email_address": email_address.strip() or str(current_mailbox.get("email_address") or ""),
        "login_username": login_username.strip() or str(current_mailbox.get("login_username") or ""),
        "password": mailbox_password.strip() or str(current_mailbox.get("password") or ""),
        "default_folder": default_folder.strip() or str(current_mailbox.get("default_folder") or ""),
    }
    payload["exports"] = {
        **current_exports,
        "template_workbook_relative_path": resolved_template_path,
        "operating_workbook_relative_path": workspace.to_workspace_relative(
            workspace.profile_paths().operating_export_workbook_path()
        ),
    }
    payload["analysis"] = {
        **current_analysis,
        "classification_guidance": (
            classification_guidance.strip()
            or str(current_analysis.get("classification_guidance") or "")
        ),
    }
    secrets_store.write(payload)
    if resolved_api_key:
        remember_default_openai_api_key(api_key=resolved_api_key)
    return load_workspace_settings_summary(
        workspace_root=str(workspace.root()),
        workspace_password=workspace_password,
    )


def normalize_workspace_relative_input(
    *,
    workspace_root: str,
    path_text: str,
) -> str:
    text = path_text.strip()
    if not text:
        return ""
    workspace = load_shared_workspace(workspace_root)
    candidate = Path(text)
    if candidate.is_absolute():
        resolved = candidate.resolve()
        if not resolved.is_relative_to(workspace.root().resolve()):
            raise RuntimeError("세이브 파일 밖 절대경로는 저장할 수 없습니다.")
        return workspace.to_workspace_relative(resolved)
    return candidate.as_posix()


def template_status_for_workspace(
    *,
    workspace_root: str,
    shared_settings: dict[str, object],
) -> dict[str, str]:
    workspace = load_shared_workspace(workspace_root)
    relative_path = str((shared_settings.get("exports") or {}).get("template_workbook_relative_path") or "")
    if not relative_path:
        return {
            "status": "warn",
            "message": "아직 엑셀 양식 경로가 저장되지 않았습니다.",
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
