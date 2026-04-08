"""real bundle 품질과 export handoff 상태를 한 번에 점검하는 smoke."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from llm import OpenAIResponsesConfig, OpenAIResponsesWrapper
from project_paths import ProfilePaths, default_example_profile_root

if __package__ in (None, ""):
    from analysis.materialized_bundle_pipeline_smoke import (
        default_template_path,
        run_materialized_bundle_pipeline_smoke,
    )
    from analysis.materialized_bundle_smoke import (
        run_materialized_bundle_analysis_smoke,
    )
    from analysis.schema import ExtractedRecord
else:
    from .materialized_bundle_pipeline_smoke import (
        default_template_path,
        run_materialized_bundle_pipeline_smoke,
    )
    from .materialized_bundle_smoke import run_materialized_bundle_analysis_smoke
    from .schema import ExtractedRecord


@dataclass(slots=True)
class RealBundleQualitySmokeReport:
    """기능: real bundle 품질 smoke 결과를 표현한다."""

    bundle_root: str
    bundle_id: str
    extracted_record_path: str
    projected_row_path: str
    output_workbook_path: str
    appended_row_index: int
    expected_semantic_keys: list[str] = field(default_factory=list)
    missing_expected_fields: list[str] = field(default_factory=list)
    unresolved_columns: list[str] = field(default_factory=list)
    summary_one_line_present: bool = False
    summary_short_present: bool = False
    passed: bool = False
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def default_profile_root() -> Path:
    """기능: 현재 예시 사용자 프로필 루트 기본 경로를 반환한다."""

    return default_example_profile_root()


def run_real_bundle_quality_smoke(
    *,
    profile_root: str,
    bundle_root: str,
    profile_id: str,
    template_path: str,
    expected_semantic_keys: list[str],
    max_unresolved_columns: int = 0,
    reuse_existing_analysis: bool = False,
) -> RealBundleQualitySmokeReport:
    """기능: real bundle 1건에 대한 analysis/export 품질 smoke를 실행한다."""

    profile_paths = ProfilePaths(profile_root)
    wrapper = OpenAIResponsesWrapper(
        OpenAIResponsesConfig(
            usage_log_path=str(profile_paths.llm_usage_log_path()),
        )
    )

    analysis_results = run_materialized_bundle_analysis_smoke(
        profile_root=profile_root,
        bundle_root=bundle_root,
        reuse_existing_analysis=reuse_existing_analysis,
        wrapper=wrapper,
    )
    if not analysis_results:
        raise RuntimeError("real bundle analysis smoke 결과를 만들지 못했다.")
    analysis_result = analysis_results[0]

    pipeline_results = run_materialized_bundle_pipeline_smoke(
        profile_id=profile_id,
        profile_root=profile_root,
        template_path=template_path,
        bundle_root=bundle_root,
        reuse_existing_analysis=True,
        wrapper=wrapper,
    )
    if not pipeline_results:
        raise RuntimeError("real bundle pipeline smoke 결과를 만들지 못했다.")
    pipeline_result = pipeline_results[0]

    record = ExtractedRecord.from_dict(
        json.loads(Path(analysis_result.extracted_record_path).read_text(encoding="utf-8"))
    )
    projected_row = json.loads(Path(pipeline_result.projected_row_path).read_text(encoding="utf-8"))

    field_map = record.field_map()
    missing_expected_fields = [
        field_name
        for field_name in expected_semantic_keys
        if field_name not in field_map or not field_map[field_name].value.strip()
    ]
    unresolved_columns = list(projected_row.get("unresolved_columns") or [])
    summary_one_line_present = bool(record.summary_one_line.strip())
    summary_short_present = bool(record.summary_short.strip())
    passed = (
        not missing_expected_fields
        and len(unresolved_columns) <= max_unresolved_columns
        and summary_one_line_present
        and summary_short_present
    )

    notes = list(analysis_result.notes) + list(pipeline_result.notes)
    if missing_expected_fields:
        notes.append("일부 기대 semantic key가 아직 비어 있다.")
    if unresolved_columns:
        notes.append("일부 템플릿 열이 아직 unresolved 상태다.")

    return RealBundleQualitySmokeReport(
        bundle_root=bundle_root,
        bundle_id=record.bundle_id,
        extracted_record_path=analysis_result.extracted_record_path,
        projected_row_path=pipeline_result.projected_row_path,
        output_workbook_path=pipeline_result.output_workbook_path,
        appended_row_index=pipeline_result.appended_row_index,
        expected_semantic_keys=expected_semantic_keys,
        missing_expected_fields=missing_expected_fields,
        unresolved_columns=unresolved_columns,
        summary_one_line_present=summary_one_line_present,
        summary_short_present=summary_short_present,
        passed=passed,
        notes=notes,
    )


def main() -> None:
    """기능: CLI에서 real bundle 품질 smoke를 실행한다."""

    parser = argparse.ArgumentParser(description="real bundle quality smoke")
    parser.add_argument("--profile-id", default="kim-jm")
    parser.add_argument("--profile-root", default=str(default_profile_root()))
    parser.add_argument("--template-path", default=str(default_template_path()))
    parser.add_argument("--bundle-root", required=True)
    parser.add_argument(
        "--expected-semantic-keys",
        default="company_name,contact_name,phone_number,email_address,website_or_social,industry,product_or_service,application_purpose,company_intro_one_line,business_summary,request_summary",
    )
    parser.add_argument("--max-unresolved-columns", type=int, default=0)
    parser.add_argument(
        "--reuse-existing-analysis",
        action="store_true",
        help="이미 저장된 extracted_record JSON이 있으면 재사용한다.",
    )
    args = parser.parse_args()

    expected_semantic_keys = [
        item.strip()
        for item in args.expected_semantic_keys.split(",")
        if item.strip()
    ]

    report = run_real_bundle_quality_smoke(
        profile_root=args.profile_root,
        bundle_root=args.bundle_root,
        profile_id=args.profile_id,
        template_path=args.template_path,
        expected_semantic_keys=expected_semantic_keys,
        max_unresolved_columns=args.max_unresolved_columns,
        reuse_existing_analysis=args.reuse_existing_analysis,
    )
    print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
    if not report.passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
