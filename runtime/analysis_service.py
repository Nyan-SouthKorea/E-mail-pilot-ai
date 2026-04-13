"""리뷰보드 재생성과 리뷰센터 조회를 위한 service."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from math import ceil

from analysis import run_inbox_review_board_smoke
from llm import OpenAIResponsesConfig, OpenAIResponsesWrapper
from runtime.review_state import ingest_review_report_into_state
from runtime.secrets_store import WorkspaceSecretsStore
from runtime.state_store import WorkspaceStateStore
from runtime.sync_service import update_latest_review_pointers
from runtime.workspace import load_shared_workspace


@dataclass(slots=True)
class ReviewRefreshServiceResult:
    review_json_path: str
    review_html_path: str
    total_bundle_count: int
    application_count: int
    not_application_count: int
    needs_human_review_count: int
    exported_count: int
    failed_count: int
    state_item_count: int
    analysis_reused_count: int
    analysis_rerun_count: int
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(slots=True)
class ReviewCenterPageServiceResult:
    items: list[dict[str, object]]
    page: int
    page_size: int
    page_count: int
    filtered_total_count: int
    selected_bundle_id: str
    sort: str
    search: str
    triage_label: str
    export_only: bool

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(slots=True)
class ReviewDetailServiceResult:
    item: dict[str, object] | None
    bundle_id: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def refresh_review_board_service(
    *,
    workspace_root: str,
    workspace_password: str,
    limit: int | None,
    reuse_existing_analysis: bool = True,
) -> ReviewRefreshServiceResult:
    workspace = load_shared_workspace(workspace_root)
    secrets_store = WorkspaceSecretsStore(
        path=str(workspace.secure_blob_path()),
        password=workspace_password,
    )
    payload = secrets_store.read()
    llm_settings = dict(payload.get("llm") or {})
    export_settings = dict(payload.get("exports") or {})
    template_path = _resolve_template_workbook_path(
        workspace=workspace_root,
        export_settings=export_settings,
    )
    wrapper = OpenAIResponsesWrapper(
        OpenAIResponsesConfig(
            model=str(llm_settings.get("model") or "gpt-5.4"),
            api_key=str(llm_settings.get("api_key") or ""),
            usage_log_path=str(workspace.profile_paths().llm_usage_log_path()),
        )
    )
    report = run_inbox_review_board_smoke(
        profile_id="shared-workspace",
        profile_root=str(workspace.profile_root()),
        template_path=template_path,
        bundle_limit=limit,
        reuse_existing_analysis=reuse_existing_analysis,
        wrapper=wrapper,
    )
    update_latest_review_pointers(workspace=workspace, review_report=report)
    from runtime.state_store import WorkspaceStateStore

    state_store = WorkspaceStateStore(workspace.state_db_path())
    state_store.ensure_schema()
    items = ingest_review_report_into_state(
        workspace=workspace,
        state_store=state_store,
        report_path=report.review_json_path,
    )
    reused_count = sum(
        1
        for item in report.items
        if any("재사용" in note for note in item.notes)
    )
    rerun_count = sum(1 for item in report.items if item.analysis_source == "llm_full_analysis") - reused_count
    return ReviewRefreshServiceResult(
        review_json_path=workspace.to_workspace_relative(report.review_json_path),
        review_html_path=workspace.to_workspace_relative(report.review_html_path),
        total_bundle_count=report.total_bundle_count,
        application_count=report.application_count,
        not_application_count=report.not_application_count,
        needs_human_review_count=report.needs_human_review_count,
        exported_count=report.exported_count,
        failed_count=report.failed_count,
        state_item_count=len(items),
        analysis_reused_count=max(0, reused_count),
        analysis_rerun_count=max(0, rerun_count),
        notes=list(report.notes),
    )


def load_review_center_page_service(
    *,
    workspace_root: str,
    search: str = "",
    triage_label: str = "",
    export_only: bool = False,
    page: int = 1,
    page_size: int = 50,
    sort: str = "received_desc",
    selected_bundle_id: str = "",
) -> ReviewCenterPageServiceResult:
    workspace = load_shared_workspace(workspace_root)
    state_store = WorkspaceStateStore(workspace.state_db_path())
    state_store.ensure_schema()
    resolved_page_size = _normalize_review_page_size(page_size)
    resolved_page = max(1, int(page or 1))
    filtered_total_count = state_store.count_review_items(
        search=search,
        triage_label=triage_label,
        export_only=export_only,
    )
    page_count = max(1, ceil(filtered_total_count / resolved_page_size)) if filtered_total_count else 1
    resolved_page = min(resolved_page, page_count)
    items = state_store.list_review_items(
        search=search,
        triage_label=triage_label,
        export_only=export_only,
        limit=resolved_page_size,
        offset=(resolved_page - 1) * resolved_page_size,
        sort=sort,
    )
    selected_id = selected_bundle_id.strip()
    if not selected_id and items:
        selected_id = str(items[0]["bundle_id"])
    return ReviewCenterPageServiceResult(
        items=items,
        page=resolved_page,
        page_size=resolved_page_size,
        page_count=page_count,
        filtered_total_count=filtered_total_count,
        selected_bundle_id=selected_id,
        sort=sort or "received_desc",
        search=search,
        triage_label=triage_label,
        export_only=export_only,
    )


def load_review_detail_service(
    *,
    workspace_root: str,
    bundle_id: str,
) -> ReviewDetailServiceResult:
    workspace = load_shared_workspace(workspace_root)
    state_store = WorkspaceStateStore(workspace.state_db_path())
    state_store.ensure_schema()
    return ReviewDetailServiceResult(
        item=state_store.get_review_item(bundle_id.strip()) if bundle_id.strip() else None,
        bundle_id=bundle_id.strip(),
    )


def _resolve_template_workbook_path(*, workspace: str, export_settings: dict[str, object]) -> str:
    shared_workspace = load_shared_workspace(workspace)
    relative_path = str(export_settings.get("template_workbook_relative_path") or "").strip()
    if relative_path:
        return str(shared_workspace.from_workspace_relative(relative_path))
    default_template = shared_workspace.profile_paths().template_workbook_path()
    if default_template.exists():
        return str(default_template)
    raise RuntimeError("세이브 파일에 엑셀 양식 경로가 없습니다.")


def _normalize_review_page_size(page_size: int) -> int:
    try:
        normalized = int(page_size)
    except (TypeError, ValueError):
        normalized = 50
    if normalized not in {25, 50, 100}:
        return 50
    return normalized
