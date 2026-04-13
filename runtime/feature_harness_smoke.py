"""공유 워크스페이스 기준 기능 하네스를 반복 검증한다."""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass, field
from datetime import datetime
import json
import os
from pathlib import Path
import tempfile

from analysis.inbox_review_board_smoke import run_inbox_review_board_smoke
from app.ui_smoke import run_app_ui_smoke
from runtime.analysis_service import refresh_review_board_service
from runtime.diagnostics_service import pick_folder_native, picker_bridge_self_test
from runtime.exports_service import rebuild_operating_workbook_service
from runtime.feature_registry import check_feature, list_feature_specs, run_feature
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
            "exports_rebuild": rebuild_operating_workbook_service(
                workspace_root=str(workspace.root()),
                workspace_password=workspace_password,
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
        notes=[
            "live credential와 API key가 없는 기능은 prerequisite check만 수행하고 직접 run하지 않는다.",
            "샘플 워크스페이스만으로도 review center, workbook rebuild, admin route 접근을 반복 검증할 수 있다.",
            "quick review board 회귀는 빈 bundle 프로필 + bundle_limit=10 경로로 `notes` 초기화 버그를 다시 잡는다.",
            "workspace/settings/diagnostics/analysis/exports 공용 service를 직접 호출해 결과 계약도 함께 검증한다.",
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
