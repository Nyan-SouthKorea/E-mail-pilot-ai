"""fetch -> review -> workbook 재구성을 묶는 상위 pipeline service."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Callable

from runtime.analysis_service import ReviewRefreshServiceResult, refresh_review_board_service
from runtime.exports_service import WorkbookRebuildServiceResult, rebuild_operating_workbook_service
from runtime.mailbox_service import MailboxFetchResult, run_mailbox_fetch_service
from runtime.state_store import WorkspaceStateStore
from runtime.workspace import load_shared_workspace


StageCallback = Callable[[dict[str, object]], None]


@dataclass(slots=True)
class WorkspacePipelineSyncResult:
    workspace_root: str
    scope: str
    limit: int | None
    status: str
    stage_id: str
    stage_label: str
    message: str
    next_action: str
    backfill_report_path: str
    review_json_path: str
    review_html_path: str
    operating_workbook_path: str
    fetched_count: int
    skipped_existing_count: int
    analysis_reused_count: int
    analysis_rerun_count: int
    total_review_item_count: int
    export_included_count: int
    reuse_counts: dict[str, int]
    details: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def run_pipeline_sync_service(
    *,
    workspace_root: str,
    workspace_password: str,
    scope: str,
    limit: int | None,
    app_kind: str = "server-tool",
    on_stage: StageCallback | None = None,
) -> WorkspacePipelineSyncResult:
    workspace = load_shared_workspace(workspace_root)
    state_store = WorkspaceStateStore(workspace.state_db_path())
    state_store.ensure_schema()
    effective_scope, effective_limit = _normalize_scope(scope=scope, limit=limit)
    sync_run_id = state_store.start_sync_run(
        run_kind="workspace_sync",
        app_kind=app_kind,
        metadata={
            "workspace_id": workspace.manifest.workspace_id,
            "scope": effective_scope,
            "limit": effective_limit,
        },
    )
    backfill_result: MailboxFetchResult | None = None
    review_result: ReviewRefreshServiceResult | None = None
    workbook_result: WorkbookRebuildServiceResult | None = None
    try:
        _emit_stage(
            on_stage,
            stage_id="fetch",
            stage_label="메일 가져오는 중",
            progress_current=1,
            progress_total=3,
            message="메일을 가져오고 있습니다.",
            next_action="이미 받은 메일은 건너뜁니다.",
            details=[
                _scope_label(effective_scope, effective_limit),
            ],
        )
        backfill_result = run_mailbox_fetch_service(
            workspace_root=workspace_root,
            workspace_password=workspace_password,
            limit=effective_limit,
            app_kind_note="공유 세이브 파일 sync service에서 메일 fetch를 실행했습니다.",
        )

        _emit_stage(
            on_stage,
            stage_id="analysis",
            stage_label="분석 중",
            progress_current=2,
            progress_total=3,
            message="메일 내용을 분석하고 있습니다.",
            next_action="기존 분석은 재사용하고, 바뀐 항목만 다시 계산합니다.",
            details=[
                f"새로 가져온 메일: {backfill_result.fetched_count}",
                f"건너뛴 메일: {backfill_result.skipped_existing_count}",
            ],
        )
        review_result = refresh_review_board_service(
            workspace_root=workspace_root,
            workspace_password=workspace_password,
            limit=effective_limit,
            reuse_existing_analysis=True,
        )

        _emit_stage(
            on_stage,
            stage_id="export",
            stage_label="엑셀 반영 중",
            progress_current=3,
            progress_total=3,
            message="엑셀 결과를 반영하고 있습니다.",
            next_action="엑셀 반영 대상으로 선택된 메일만 운영 엑셀에 반영합니다.",
            details=[
                f"분석 재사용: {review_result.analysis_reused_count}",
                f"분석 재실행: {review_result.analysis_rerun_count}",
            ],
        )
        workbook_result = rebuild_operating_workbook_service(
            workspace_root=workspace_root,
            workspace_password=workspace_password,
        )
        result = WorkspacePipelineSyncResult(
            workspace_root=str(workspace.root()),
            scope=effective_scope,
            limit=effective_limit,
            status="completed",
            stage_id="complete",
            stage_label="완료",
            message="동기화가 완료되었습니다.",
            next_action="리뷰 화면에서 결과를 확인하거나 운영 workbook을 열어 보세요.",
            backfill_report_path=backfill_result.backfill_report_path,
            review_json_path=review_result.review_json_path,
            review_html_path=review_result.review_html_path,
            operating_workbook_path=workbook_result.operating_workbook_path,
            fetched_count=backfill_result.fetched_count,
            skipped_existing_count=backfill_result.skipped_existing_count,
            analysis_reused_count=review_result.analysis_reused_count,
            analysis_rerun_count=review_result.analysis_rerun_count,
            total_review_item_count=review_result.state_item_count,
            export_included_count=workbook_result.export_included_count,
            reuse_counts={
                "analysis_reused_count": review_result.analysis_reused_count,
                "analysis_rerun_count": review_result.analysis_rerun_count,
            },
            details=[
                f"새로 가져온 메일: {backfill_result.fetched_count}",
                f"이미 있던 메일 건너뜀: {backfill_result.skipped_existing_count}",
                f"분석 재사용: {review_result.analysis_reused_count}",
                f"분석 재실행: {review_result.analysis_rerun_count}",
            ],
            notes=[
                f"scope={effective_scope}",
                f"limit={effective_limit}",
            ] + list(backfill_result.notes) + list(review_result.notes),
        )
        state_store.finish_sync_run(
            sync_run_id,
            status="completed",
            notes=result.notes,
            metadata=result.to_dict(),
        )
        return result
    except Exception as exc:
        status = "failed"
        stage_id = "failed"
        stage_label = "실패"
        message = "동기화에 실패했습니다."
        next_action = "설정을 다시 확인하고 재시도해 주세요."
        details = [f"{exc.__class__.__name__}: {exc}"]
        if backfill_result is not None:
            status = "partial_success"
            stage_id = "partial"
            stage_label = "부분 완료"
            message = "메일 저장은 완료됐지만 다음 처리 단계에서 확인이 필요한 문제가 생겼습니다."
            next_action = "로그를 확인하거나 설정을 다시 확인한 뒤 다시 시도해 주세요."
            details = [
                f"메일 저장 완료: {backfill_result.fetched_count}건",
                f"이미 있던 메일 건너뜀: {backfill_result.skipped_existing_count}건",
                f"실패 단계: {'분석 중' if review_result is None else '엑셀 반영 중'}",
                "다음 행동: 로그 보기 또는 설정 확인 뒤 다시 시도",
                f"기술 상세: {exc.__class__.__name__}: {exc}",
            ]
        state_store.finish_sync_run(
            sync_run_id,
            status=status,
            notes=[f"{exc.__class__.__name__}: {exc}"],
            metadata={
                "workspace_root": str(workspace.root()),
                "scope": effective_scope,
                "limit": effective_limit,
                "fetched_count": backfill_result.fetched_count if backfill_result else 0,
                "skipped_existing_count": backfill_result.skipped_existing_count if backfill_result else 0,
            },
        )
        return WorkspacePipelineSyncResult(
            workspace_root=str(workspace.root()),
            scope=effective_scope,
            limit=effective_limit,
            status=status,
            stage_id=stage_id,
            stage_label=stage_label,
            message=message,
            next_action=next_action,
            backfill_report_path=backfill_result.backfill_report_path if backfill_result else "",
            review_json_path=review_result.review_json_path if review_result else "",
            review_html_path=review_result.review_html_path if review_result else "",
            operating_workbook_path=(
                workbook_result.operating_workbook_path if workbook_result else ""
            ),
            fetched_count=backfill_result.fetched_count if backfill_result else 0,
            skipped_existing_count=backfill_result.skipped_existing_count if backfill_result else 0,
            analysis_reused_count=review_result.analysis_reused_count if review_result else 0,
            analysis_rerun_count=review_result.analysis_rerun_count if review_result else 0,
            total_review_item_count=review_result.state_item_count if review_result else 0,
            export_included_count=workbook_result.export_included_count if workbook_result else 0,
            reuse_counts={
                "analysis_reused_count": review_result.analysis_reused_count if review_result else 0,
                "analysis_rerun_count": review_result.analysis_rerun_count if review_result else 0,
            },
            details=details,
            notes=[f"{exc.__class__.__name__}: {exc}"],
        )


def _normalize_scope(*, scope: str, limit: int | None) -> tuple[str, int | None]:
    normalized = (scope or "recent").strip().lower()
    if normalized not in {"recent", "all"}:
        raise RuntimeError(f"지원하지 않는 동기화 범위입니다: {normalized}")
    if normalized == "all":
        return "all", None
    resolved_limit = 10 if limit is None else int(limit)
    if resolved_limit <= 0:
        raise RuntimeError("최근 N개 동기화는 1 이상의 개수를 입력해야 합니다.")
    return "recent", resolved_limit


def _scope_label(scope: str, limit: int | None) -> str:
    if scope == "all":
        return "전체 동기화를 실행합니다."
    return f"최근 {limit}건만 먼저 확인합니다."


def _emit_stage(callback: StageCallback | None, **payload: object) -> None:
    if callback is None:
        return
    callback(payload)
