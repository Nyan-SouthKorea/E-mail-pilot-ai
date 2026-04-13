"""운영 workbook 재구성 service."""

from __future__ import annotations

from dataclasses import asdict, dataclass

from llm import OpenAIResponsesConfig, OpenAIResponsesWrapper
from runtime.secrets_store import WorkspaceSecretsStore
from runtime.state_store import WorkspaceStateStore
from runtime.sync_service import rebuild_operating_workbook
from runtime.workspace import load_shared_workspace


@dataclass(slots=True)
class WorkbookRebuildServiceResult:
    operating_workbook_path: str
    representative_count: int

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def rebuild_operating_workbook_service(
    *,
    workspace_root: str,
    workspace_password: str,
) -> WorkbookRebuildServiceResult:
    workspace = load_shared_workspace(workspace_root)
    secrets_store = WorkspaceSecretsStore(
        path=str(workspace.secure_blob_path()),
        password=workspace_password,
    )
    payload = secrets_store.read()
    llm_settings = dict(payload.get("llm") or {})
    export_settings = dict(payload.get("exports") or {})
    template_path = _resolve_template_workbook_path(
        workspace_root=workspace_root,
        export_settings=export_settings,
    )
    state_store = WorkspaceStateStore(workspace.state_db_path())
    state_store.ensure_schema()
    wrapper = OpenAIResponsesWrapper(
        OpenAIResponsesConfig(
            model=str(llm_settings.get("model") or "gpt-5.4"),
            api_key=str(llm_settings.get("api_key") or ""),
            usage_log_path=str(workspace.profile_paths().llm_usage_log_path()),
        )
    )
    result = rebuild_operating_workbook(
        workspace=workspace,
        state_store=state_store,
        template_path=template_path,
        wrapper=wrapper,
    )
    return WorkbookRebuildServiceResult(
        operating_workbook_path=str(result["operating_workbook_relpath"]),
        representative_count=int(result["representative_count"]),
    )


def _resolve_template_workbook_path(*, workspace_root: str, export_settings: dict[str, object]):
    workspace = load_shared_workspace(workspace_root)
    relative_path = str(export_settings.get("template_workbook_relative_path") or "").strip()
    if relative_path:
        return workspace.from_workspace_relative(relative_path)
    default_template = workspace.profile_paths().template_workbook_path()
    if default_template.exists():
        return default_template
    raise RuntimeError("세이브 파일에 엑셀 양식 경로가 없습니다.")
