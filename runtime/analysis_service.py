"""리뷰보드 재생성과 분석 재사용 통계를 위한 service."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

from analysis import run_inbox_review_board_smoke
from llm import OpenAIResponsesConfig, OpenAIResponsesWrapper
from runtime.review_state import ingest_review_report_into_state
from runtime.secrets_store import WorkspaceSecretsStore
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


def _resolve_template_workbook_path(*, workspace: str, export_settings: dict[str, object]) -> str:
    shared_workspace = load_shared_workspace(workspace)
    relative_path = str(export_settings.get("template_workbook_relative_path") or "").strip()
    if relative_path:
        return str(shared_workspace.from_workspace_relative(relative_path))
    default_template = shared_workspace.profile_paths().template_workbook_path()
    if default_template.exists():
        return str(default_template)
    raise RuntimeError("세이브 파일에 엑셀 양식 경로가 없습니다.")
