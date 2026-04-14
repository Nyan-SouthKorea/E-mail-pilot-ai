"""운영 workbook 재구성 service."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime

from llm import OpenAIResponsesConfig, OpenAIResponsesWrapper
from runtime.device_secret_store import sanitize_openai_api_key
from runtime.secrets_store import WorkspaceSecretsStore
from runtime.state_store import WorkspaceStateStore
from runtime.sync_service import rebuild_operating_workbook
from runtime.workspace import load_shared_workspace


@dataclass(slots=True)
class WorkbookRebuildServiceResult:
    operating_workbook_path: str
    export_included_count: int

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(slots=True)
class ExportsSummaryServiceResult:
    operating_workbook_relpath: str
    operating_workbook_exists: bool
    operating_workbook_updated_at: str
    export_included_count: int
    workbook_row_count: int
    snapshot_items: list[dict[str, str]]

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
            api_key=sanitize_openai_api_key(str(llm_settings.get("api_key") or "")),
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
        export_included_count=int(result["export_included_count"]),
    )


def load_exports_summary_service(*, workspace_root: str) -> ExportsSummaryServiceResult:
    workspace = load_shared_workspace(workspace_root)
    state_store = WorkspaceStateStore(workspace.state_db_path())
    state_store.ensure_schema()
    operating_path = workspace.operating_workbook_path()
    snapshot_root = workspace.operating_snapshot_root()
    snapshot_items: list[dict[str, str]] = []
    if snapshot_root.exists():
        for path in sorted(snapshot_root.glob("*.xlsx"), key=lambda item: item.stat().st_mtime, reverse=True)[:20]:
            snapshot_items.append(
                {
                    "name": path.name,
                    "relative_path": workspace.to_workspace_relative(path),
                    "updated_at": datetime.fromtimestamp(path.stat().st_mtime).isoformat(timespec="seconds"),
                }
            )
    counts = state_store.summary_counts()
    export_included_items = state_store.list_review_items(export_only=True)
    updated_at = ""
    if operating_path.exists():
        updated_at = datetime.fromtimestamp(operating_path.stat().st_mtime).isoformat(timespec="seconds")
    return ExportsSummaryServiceResult(
        operating_workbook_relpath=workspace.to_workspace_relative(operating_path),
        operating_workbook_exists=operating_path.exists(),
        operating_workbook_updated_at=updated_at,
        export_included_count=int(counts.get("export_included_application") or 0),
        workbook_row_count=len([item for item in export_included_items if item.get("workbook_row_index")]),
        snapshot_items=snapshot_items,
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
