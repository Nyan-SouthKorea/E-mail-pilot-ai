"""공유 워크스페이스 기준 기능 하네스를 반복 검증한다."""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass, field
from datetime import datetime
import json
import os
from pathlib import Path
import sqlite3
import socket
import tempfile

from analysis.inbox_review_board_smoke import run_inbox_review_board_smoke
from app.ui_smoke import run_app_ui_smoke
from runtime.analysis_service import (
    load_review_center_page_service,
    load_review_detail_service,
    refresh_review_board_service,
)
from runtime.diagnostics_service import pick_folder_native, picker_bridge_self_test
from runtime.exports_service import load_exports_summary_service, rebuild_operating_workbook_service
from runtime.feature_registry import check_feature, list_feature_specs, run_feature
from runtime.lockfile import WorkspaceLockData, _is_local_dead_process
from runtime.review_state import ingest_review_report_into_state
from runtime.state_store import WorkspaceStateStore
from runtime.settings_service import load_workspace_settings_summary
from runtime.sample_workspace import create_sample_workspace
from runtime.workspace_service import inspect_workspace_entry, list_recent_workspaces
from runtime.workspace import WORKSPACE_MANIFEST_FILENAME, load_shared_workspace


@dataclass(slots=True)
class FeatureHarnessSmokeReport:
    """기능: 샘플/공유 워크스페이스 전체 smoke 결과를 표현한다."""

    generated_at: str
    workspace_root: str
    report_relpath: str
    created_sample_workspace: bool
    feature_checks: dict[str, list[dict[str, object]]] = field(default_factory=dict)
    executed_feature_runs: list[dict[str, object]] = field(default_factory=list)
    service_smokes: dict[str, dict[str, object]] = field(default_factory=dict)
    ui_smoke: dict[str, object] | None = None
    quick_review_regression: dict[str, object] | None = None
    canonical_selection_smoke: dict[str, object] | None = None
    schema_upgrade_smoke: dict[str, object] | None = None
    lockfile_windows_safety_smoke: dict[str, object] | None = None
    review_performance_smoke: dict[str, object] | None = None
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def run_feature_harness_smoke(
    *,
    workspace_root: str | Path,
    workspace_password: str,
    create_sample_if_missing: bool = False,
) -> FeatureHarnessSmokeReport:
    """기능: 공유 워크스페이스에서 비live 기능을 반복 검증하는 smoke를 돌린다."""

    workspace_path = Path(workspace_root)
    created_sample_workspace = False
    manifest_path = workspace_path / WORKSPACE_MANIFEST_FILENAME
    if create_sample_if_missing and not manifest_path.exists():
        create_sample_workspace(
            workspace_root=workspace_path,
            workspace_password=workspace_password,
        )
        created_sample_workspace = True

    workspace = load_shared_workspace(workspace_path)
    harness_root = workspace.profile_paths().runtime_logs_root() / "runtime"
    harness_root.mkdir(parents=True, exist_ok=True)
    report_path = harness_root / f"{datetime.now().strftime('%y%m%d_%H%M')}_feature_harness_smoke.json"

    feature_checks: dict[str, list[dict[str, object]]] = {}
    for spec in list_feature_specs():
        checks = check_feature(
            feature_id=spec.feature_id,
            workspace_root=str(workspace.root()),
            workspace_password=workspace_password,
        )
        feature_checks[spec.feature_id] = [item.to_dict() for item in checks]

    executed_feature_runs: list[dict[str, object]] = []
    for feature_id in [
        "runtime.workspace.inspect",
        "exports.operating_workbook.rebuild",
    ]:
        result = run_feature(
            feature_id=feature_id,
            workspace_root=str(workspace.root()),
            workspace_password=workspace_password,
            app_kind="feature-harness-smoke",
            trigger_source="feature-harness-smoke",
            force_lock_takeover=True,
        )
        executed_feature_runs.append(result.to_dict())

    previous_picker_test_response = os.environ.get("EPA_PICKER_TEST_RESPONSE")
    os.environ["EPA_PICKER_TEST_RESPONSE"] = str(workspace.root())
    try:
        review_page = load_review_center_page_service(
            workspace_root=str(workspace.root()),
            page=1,
            page_size=50,
            sort="received_desc",
        )
        review_detail = load_review_detail_service(
            workspace_root=str(workspace.root()),
            bundle_id=review_page.selected_bundle_id,
        )
        service_smokes = {
            "workspace_status": inspect_workspace_entry(
                workspace_root=str(workspace.root()),
                workspace_password=workspace_password,
            ).to_dict(),
            "settings_show": load_workspace_settings_summary(
                workspace_root=str(workspace.root()),
                workspace_password=workspace_password,
            ).to_dict(),
            "recent_workspaces": {
                "items": [item.to_dict() for item in list_recent_workspaces()],
            },
            "picker_bridge": picker_bridge_self_test(
                shell_mode="desktop_window",
                window_attached=True,
            ).to_dict(),
            "picker_folder": pick_folder_native(
                current_path="",
                workspace_root=str(workspace.root()),
            ).to_dict(),
            "analysis_review_refresh": refresh_review_board_service(
                workspace_root=str(workspace.root()),
                workspace_password=workspace_password,
                limit=10,
                reuse_existing_analysis=True,
            ).to_dict(),
            "analysis_review_list": review_page.to_dict(),
            "analysis_review_item": review_detail.to_dict(),
            "exports_rebuild": rebuild_operating_workbook_service(
                workspace_root=str(workspace.root()),
                workspace_password=workspace_password,
            ).to_dict(),
            "exports_summary": load_exports_summary_service(
                workspace_root=str(workspace.root()),
            ).to_dict(),
        }
    finally:
        if previous_picker_test_response is None:
            os.environ.pop("EPA_PICKER_TEST_RESPONSE", None)
        else:
            os.environ["EPA_PICKER_TEST_RESPONSE"] = previous_picker_test_response

    ui_smoke = run_app_ui_smoke(
        workspace_root=str(workspace.root()),
        workspace_password=workspace_password,
    )
    quick_review_regression = run_quick_review_regression_smoke(
        workspace_root=str(workspace.root()),
    )
    canonical_selection_smoke = run_canonical_selection_smoke(
        workspace_root=str(workspace.root()),
    )
    schema_upgrade_smoke = run_schema_upgrade_smoke()
    lockfile_windows_safety_smoke = run_lockfile_windows_safety_smoke()
    review_performance_smoke = run_review_performance_smoke(
        workspace_password=workspace_password,
    )

    report = FeatureHarnessSmokeReport(
        generated_at=datetime.now().isoformat(timespec="seconds"),
        workspace_root=str(workspace.root()),
        report_relpath=workspace.to_workspace_relative(report_path),
        created_sample_workspace=created_sample_workspace,
        feature_checks=feature_checks,
        executed_feature_runs=executed_feature_runs,
        service_smokes=service_smokes,
        ui_smoke=ui_smoke.to_dict(),
        quick_review_regression=quick_review_regression,
        canonical_selection_smoke=canonical_selection_smoke,
        schema_upgrade_smoke=schema_upgrade_smoke,
        lockfile_windows_safety_smoke=lockfile_windows_safety_smoke,
        review_performance_smoke=review_performance_smoke,
        notes=[
            "live credential와 API key가 없는 기능은 prerequisite check만 수행하고 직접 run하지 않는다.",
            "샘플 워크스페이스만으로도 review center, workbook rebuild, admin route 접근을 반복 검증할 수 있다.",
            "quick review board 회귀는 빈 bundle 프로필 + bundle_limit=10 경로로 `notes` 초기화 버그를 다시 잡는다.",
            "workspace/settings/diagnostics/analysis/exports 공용 service를 직접 호출해 결과 계약도 함께 검증한다.",
            "자동 canonical selection smoke는 같은 회사 신청 메일 2건 중 더 완전한 수정본을 export 기준으로 고르는지 확인한다.",
            "schema upgrade smoke는 오래된 state.sqlite를 현재 bundle_review_state / feature_runs 스키마로 자동 승격할 수 있는지 확인한다.",
            "lockfile Windows safety smoke는 local stale lock 확인 중 예외가 나도 홈 화면 전체가 500으로 죽지 않도록 보장한다.",
            "review performance smoke는 synthetic 1200건 상태에서 paged / all_virtual review 조회 계약이 무너지지 않는지 확인한다.",
        ],
    )
    report_path.write_text(
        json.dumps(report.to_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return report


def run_quick_review_regression_smoke(*, workspace_root: str | Path) -> dict[str, object]:
    """기능: bundle_limit 경로의 review board 회귀를 실제 LLM 없이 점검한다."""

    workspace = load_shared_workspace(workspace_root)
    template_path = workspace.profile_paths().template_workbook_path()
    with tempfile.TemporaryDirectory(prefix="epa_quick_review_empty_") as empty_profile_root:
        report = run_inbox_review_board_smoke(
            profile_id="feature-harness-empty-profile",
            profile_root=empty_profile_root,
            template_path=str(template_path),
            bundle_limit=10,
            reuse_existing_analysis=True,
        )
    return {
        "status": "pass",
        "total_bundle_count": report.total_bundle_count,
        "notes": list(report.notes),
    }


def run_canonical_selection_smoke(*, workspace_root: str | Path) -> dict[str, object]:
    """기능: 같은 신청 흐름 후보 2건에서 canonical export 대상을 자동 선택하는지 확인한다."""

    workspace = load_shared_workspace(workspace_root)
    with tempfile.TemporaryDirectory(prefix="epa_canonical_smoke_") as temp_root:
        report_path = Path(temp_root) / "canonical_selection_report.json"
        state_db_path = Path(temp_root) / "state.sqlite"
        payload = {
            "items": [
                {
                    "bundle_id": "20260405_091500_msg_ba92c71f",
                    "bundle_root": "mail/bundles/20260405_091500_msg_ba92c71f",
                    "received_at": "2026-04-05T09:15:00+09:00",
                    "sender": "박서연 <seoyeon@acralight.co.kr>",
                    "subject": "[샘플] 아크라이트 참가 신청",
                    "attachment_count": 1,
                    "triage_label": "application",
                    "triage_reason": "신청 내용이 포함된 메일이다.",
                    "triage_confidence": 0.92,
                    "analysis_source": "smoke_canonical_selection",
                    "export_status": "pending",
                    "company_name": "아크라이트",
                    "contact_name": "박서연",
                    "email_address": "seoyeon@acralight.co.kr",
                    "application_purpose": "전시 참가 신청",
                    "request_summary": "초기 신청서 본문이다.",
                    "unresolved_columns": [],
                    "notes": [],
                },
                {
                    "bundle_id": "20260406_142500_msg_b170ce32",
                    "bundle_root": "mail/bundles/20260406_142500_msg_b170ce32",
                    "received_at": "2026-04-06T14:25:00+09:00",
                    "sender": "박서연 <seoyeon@acralight.co.kr>",
                    "subject": "[샘플] 아크라이트 참가 신청서 수정본",
                    "attachment_count": 1,
                    "triage_label": "application",
                    "triage_reason": "수정된 신청 내용이 포함된 메일이다.",
                    "triage_confidence": 0.95,
                    "analysis_source": "smoke_canonical_selection",
                    "export_status": "pending",
                    "company_name": "아크라이트",
                    "contact_name": "박서연",
                    "email_address": "seoyeon@acralight.co.kr",
                    "application_purpose": "전시 참가 신청 수정본",
                    "request_summary": "최신 수정본 신청서다.",
                    "unresolved_columns": [],
                    "notes": [],
                },
            ]
        }
        report_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        state_store = WorkspaceStateStore(state_db_path)
        state_store.ensure_schema()
        items = ingest_review_report_into_state(
            workspace=workspace,
            state_store=state_store,
            report_path=report_path,
            wrapper=None,
        )
        selected = [item for item in items if item.included_in_export]
        held = [item for item in items if item.application_group_id and not item.included_in_export]
        expected_bundle_id = "20260406_142500_msg_b170ce32"
        if len(selected) != 1 or selected[0].bundle_id != expected_bundle_id:
            return {
                "status": "fail",
                "selected_bundle_ids": [item.bundle_id for item in selected],
                "held_bundle_ids": [item.bundle_id for item in held],
                "expected_bundle_id": expected_bundle_id,
            }
        return {
            "status": "pass",
            "selected_bundle_id": selected[0].bundle_id,
            "held_bundle_ids": [item.bundle_id for item in held],
            "canonical_selection_reason": selected[0].canonical_selection_reason,
            "application_group_id": selected[0].application_group_id,
        }


def run_schema_upgrade_smoke() -> dict[str, object]:
    """기능: 오래된 state DB도 현재 스키마로 자동 승격되는지 확인한다."""

    with tempfile.TemporaryDirectory(prefix="epa_schema_upgrade_") as temp_root:
        db_path = Path(temp_root) / "state.sqlite"
        connection = sqlite3.connect(db_path)
        try:
            connection.executescript(
                """
                CREATE TABLE bundle_review_state (
                    bundle_id TEXT PRIMARY KEY,
                    received_at TEXT,
                    sender TEXT NOT NULL DEFAULT '',
                    subject TEXT NOT NULL DEFAULT '',
                    attachment_count INTEGER NOT NULL DEFAULT 0,
                    triage_label TEXT NOT NULL DEFAULT 'needs_human_review',
                    triage_reason TEXT NOT NULL DEFAULT '',
                    triage_confidence REAL,
                    analysis_source TEXT NOT NULL DEFAULT '',
                    export_status TEXT NOT NULL DEFAULT '',
                    company_name TEXT NOT NULL DEFAULT '',
                    contact_name TEXT NOT NULL DEFAULT '',
                    email_address TEXT NOT NULL DEFAULT '',
                    application_purpose TEXT NOT NULL DEFAULT '',
                    request_summary TEXT NOT NULL DEFAULT '',
                    unresolved_columns_json TEXT NOT NULL DEFAULT '[]',
                    notes_json TEXT NOT NULL DEFAULT '[]',
                    bundle_root_relpath TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE feature_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    feature_id TEXT NOT NULL,
                    app_kind TEXT NOT NULL,
                    started_at TEXT NOT NULL,
                    finished_at TEXT,
                    status TEXT NOT NULL,
                    metadata_json TEXT NOT NULL DEFAULT '{}',
                    notes_json TEXT NOT NULL DEFAULT '[]'
                );
                """
            )
            connection.commit()
        finally:
            connection.close()

        store = WorkspaceStateStore(db_path)
        store.ensure_schema()

        connection = sqlite3.connect(db_path)
        try:
            bundle_columns = {
                row[1] for row in connection.execute("PRAGMA table_info(bundle_review_state)")
            }
            feature_columns = {
                row[1] for row in connection.execute("PRAGMA table_info(feature_runs)")
            }
            bundle_indexes = {
                row[1] for row in connection.execute("PRAGMA index_list(bundle_review_state)")
            }
        finally:
            connection.close()

    required_bundle_columns = {
        "application_group_id",
        "canonical_bundle_id",
        "included_in_export",
        "canonical_selection_reason",
        "canonical_selection_confidence",
        "dedupe_group_key",
        "is_export_representative",
        "duplicate_of_bundle_id",
        "workbook_row_index",
        "user_override_state",
    }
    required_feature_columns = {
        "trigger_source",
        "outputs_json",
        "error_summary",
    }
    missing_bundle_columns = sorted(required_bundle_columns - bundle_columns)
    missing_feature_columns = sorted(required_feature_columns - feature_columns)
    index_present = "idx_bundle_review_state_group" in bundle_indexes

    if missing_bundle_columns or missing_feature_columns or not index_present:
        return {
            "status": "fail",
            "missing_bundle_columns": missing_bundle_columns,
            "missing_feature_columns": missing_feature_columns,
            "idx_bundle_review_state_group_present": index_present,
        }
    return {
        "status": "pass",
        "bundle_column_count": len(bundle_columns),
        "feature_column_count": len(feature_columns),
        "idx_bundle_review_state_group_present": True,
    }


def run_lockfile_windows_safety_smoke() -> dict[str, object]:
    """기능: local stale lock pid 확인 중 예외가 나도 안전하게 False로 끝나는지 확인한다."""

    original_kill = os.kill
    lock_data = WorkspaceLockData(
        lock_id="lock-smoke",
        workspace_id="workspace-smoke",
        host=socket.gethostname(),
        user="smoke",
        process_id=max(1, os.getpid()),
        app_kind="feature-harness-smoke",
        opened_at=datetime.now().isoformat(timespec="seconds"),
        heartbeat_at=datetime.now().isoformat(timespec="seconds"),
    )
    try:
        def _raise_system_error(*args, **kwargs):
            raise SystemError("simulated os.kill failure")

        os.kill = _raise_system_error  # type: ignore[assignment]
        is_dead = _is_local_dead_process(lock_data)
    finally:
        os.kill = original_kill  # type: ignore[assignment]

    return {
        "status": "pass" if is_dead is False else "fail",
        "is_dead": is_dead,
    }


def run_review_performance_smoke(*, workspace_password: str) -> dict[str, object]:
    """기능: synthetic 대량 리뷰 상태에서 paged/all_virtual 조회 계약을 점검한다."""

    with tempfile.TemporaryDirectory(prefix="epa_review_perf_") as temp_root:
        create_sample_workspace(
            workspace_root=temp_root,
            workspace_password=workspace_password,
        )
        workspace = load_shared_workspace(temp_root)
        state_store = WorkspaceStateStore(workspace.state_db_path())
        state_store.ensure_schema()
        now = datetime.now().isoformat(timespec="seconds")
        synthetic_rows: list[tuple[object, ...]] = []
        for index in range(1200):
            triage_label = "application" if index % 3 == 0 else ("not_application" if index % 3 == 1 else "needs_human_review")
            included_in_export = 1 if triage_label == "application" and index % 5 == 0 else 0
            export_status = "included" if included_in_export else ("held" if triage_label == "application" else "")
            unresolved_columns = [] if triage_label != "needs_human_review" else ["company_name", "contact_name"]
            synthetic_rows.append(
                (
                    f"synthetic_{index:04d}",
                    f"2026-04-14T{(index % 24):02d}:{(index % 60):02d}:00+09:00",
                    f"sender{index}@example.com",
                    f"[synthetic] 테스트 메일 {index}",
                    0,
                    triage_label,
                    "synthetic review item",
                    0.8,
                    "synthetic_smoke",
                    export_status,
                    f"테스트업체 {index % 40}",
                    f"담당자 {index % 30}",
                    f"contact{index}@example.com",
                    "테스트 신청",
                    f"synthetic summary {index}",
                    json.dumps(unresolved_columns, ensure_ascii=False),
                    "[]",
                    f"mail/bundles/synthetic_{index:04d}",
                    f"mail/bundles/synthetic_{index:04d}/raw.eml",
                    f"mail/bundles/synthetic_{index:04d}/attachments",
                    f"logs/analysis/synthetic_{index:04d}_summary.txt",
                    f"logs/review/synthetic_{index:04d}_preview.html",
                    f"logs/analysis/synthetic_{index:04d}_record.json",
                    f"exports/output/synthetic_{index:04d}_projected.json",
                    f"group_{index % 90}",
                    f"synthetic_{index - (index % 5):04d}",
                    included_in_export,
                    "synthetic canonical selection",
                    0.72,
                    f"group_{index % 90}",
                    included_in_export,
                    None,
                    (index % 150) + 1 if included_in_export else None,
                    "",
                    now,
                )
            )
        with state_store.connect() as connection:
            connection.execute("DELETE FROM bundle_review_state")
            connection.executemany(
                """
                INSERT INTO bundle_review_state (
                    bundle_id,
                    received_at,
                    sender,
                    subject,
                    attachment_count,
                    triage_label,
                    triage_reason,
                    triage_confidence,
                    analysis_source,
                    export_status,
                    company_name,
                    contact_name,
                    email_address,
                    application_purpose,
                    request_summary,
                    unresolved_columns_json,
                    notes_json,
                    bundle_root_relpath,
                    raw_eml_relpath,
                    attachments_dir_relpath,
                    summary_relpath,
                    preview_relpath,
                    extracted_record_relpath,
                    projected_row_relpath,
                    application_group_id,
                    canonical_bundle_id,
                    included_in_export,
                    canonical_selection_reason,
                    canonical_selection_confidence,
                    dedupe_group_key,
                    is_export_representative,
                    duplicate_of_bundle_id,
                    workbook_row_index,
                    user_override_state,
                    updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                synthetic_rows,
            )
        paged = load_review_center_page_service(
            workspace_root=str(workspace.root()),
            page=1,
            page_size=50,
            sort="received_desc",
            view_mode="paged",
        )
        all_virtual = load_review_center_page_service(
            workspace_root=str(workspace.root()),
            page=1,
            page_size=200,
            sort="received_desc",
            view_mode="all_virtual",
        )
        detail = load_review_detail_service(
            workspace_root=str(workspace.root()),
            bundle_id=paged.selected_bundle_id,
        )
        return {
            "status": "pass" if paged.filtered_total_count == 1200 and len(paged.items) == 50 and len(all_virtual.items) == 1200 and bool(detail.item) else "fail",
            "paged_count": len(paged.items),
            "paged_total": paged.filtered_total_count,
            "all_virtual_count": len(all_virtual.items),
            "selected_bundle_id": paged.selected_bundle_id,
            "detail_loaded": bool(detail.item),
        }


def main() -> None:
    parser = argparse.ArgumentParser(description="feature harness smoke")
    parser.add_argument("--workspace-root", required=True)
    parser.add_argument("--workspace-password", required=True)
    parser.add_argument("--create-sample-if-missing", action="store_true")
    args = parser.parse_args()

    result = run_feature_harness_smoke(
        workspace_root=args.workspace_root,
        workspace_password=args.workspace_password,
        create_sample_if_missing=args.create_sample_if_missing,
    )
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
