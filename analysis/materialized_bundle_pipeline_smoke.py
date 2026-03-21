"""runtime bundle 분석 결과를 workbook append까지 연결하는 smoke."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from exports import (
    append_projected_row_to_workbook,
    apply_hybrid_template_mapping,
    build_timestamped_export_workbook_path,
    cleanup_legacy_export_workbooks,
    find_latest_runtime_export_workbook,
    project_record_to_template,
    read_template_profile,
)
from llm import OpenAIResponsesConfig, OpenAIResponsesWrapper
from mailbox.bundle_reader import list_valid_runtime_bundle_directories
from project_paths import ProfilePaths, default_example_profile_root

if __package__ in (None, ""):
    from analysis.materialized_bundle_smoke import run_materialized_bundle_analysis_smoke
    from analysis.schema import ExtractedRecord
else:
    from .materialized_bundle_smoke import run_materialized_bundle_analysis_smoke
    from .schema import ExtractedRecord


@dataclass(slots=True)
class MaterializedBundlePipelineRunResult:
    """기능: bundle 1건의 end-to-end smoke 결과를 표현한다.

    입력:
    - bundle_id: 처리한 bundle 식별자
    - extracted_record_path: 사용한 분석 결과 JSON 경로
    - projected_row_path: 저장한 projection JSON 경로
    - output_workbook_path: 결과 workbook 경로
    - appended_row_index: append된 행 번호
    - notes: 추가 메모

    반환:
    - dataclass 인스턴스
    """

    bundle_id: str
    extracted_record_path: str
    projected_row_path: str
    output_workbook_path: str
    appended_row_index: int
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        """기능: 결과를 JSON 직렬화용 dict로 바꾼다.

        입력:
        - 없음

        반환:
        - dataclass가 풀린 dict
        """

        return asdict(self)


def default_profile_root() -> Path:
    """기능: 현재 예시 사용자 프로필 루트 기본 경로를 반환한다.

    입력:
    - 없음

    반환:
    - `secrets/사용자 설정/김정민`
    """

    return default_example_profile_root()


def default_template_path() -> Path:
    """기능: 현재 예시 템플릿 workbook 기본 경로를 반환한다.

    입력:
    - 없음

    반환:
    - 기대 산출물 workbook 경로
    """

    profile_paths = ProfilePaths(str(default_profile_root()))
    return profile_paths.template_workbook_path()


def _load_extracted_record(extracted_record_path: Path) -> ExtractedRecord:
    """기능: 저장된 `ExtractedRecord` JSON을 객체로 복원한다.

    입력:
    - extracted_record_path: 저장된 분석 결과 JSON 경로

    반환:
    - `ExtractedRecord`
    """

    return ExtractedRecord.from_dict(
        json.loads(extracted_record_path.read_text(encoding="utf-8"))
    )


def run_materialized_bundle_pipeline_smoke(
    *,
    profile_id: str,
    profile_root: str,
    template_path: str,
    output_workbook_path: str | None = None,
    bundle_root: str | None = None,
    reuse_existing_analysis: bool = False,
    wrapper: OpenAIResponsesWrapper | None = None,
) -> list[MaterializedBundlePipelineRunResult]:
    """기능: runtime bundle들을 분석해 workbook에 append하는 smoke를 실행한다.

    입력:
    - profile_id: 템플릿 프로필 식별자
    - profile_root: 사용자 프로필 루트
    - template_path: reference workbook 경로
    - output_workbook_path: 결과 workbook 경로
    - bundle_root: 특정 bundle만 대상으로 돌릴 때의 경로
    - reuse_existing_analysis: 저장된 분석 JSON을 재사용할지 여부
    - wrapper: OpenAI 공용 래퍼

    반환:
    - bundle별 실행 결과 목록
    """

    profile_paths = ProfilePaths(profile_root)
    profile_paths.ensure_runtime_dirs()

    wrapper = wrapper or OpenAIResponsesWrapper(
        OpenAIResponsesConfig(
            usage_log_path=str(profile_paths.llm_usage_log_path()),
        )
    )

    template_profile = read_template_profile(
        workbook_path=template_path,
        profile_id=profile_id,
        template_id=Path(template_path).stem,
    )
    mapped_profile, mapping = apply_hybrid_template_mapping(
        template_profile,
        wrapper=wrapper,
    )

    workbook_output = Path(output_workbook_path) if output_workbook_path else (
        build_timestamped_export_workbook_path(
            profile_root=profile_root,
            template_workbook_path=template_path,
        )
    )
    source_workbook_path = find_latest_runtime_export_workbook(
        profile_root=profile_root,
        exclude_paths=[workbook_output],
    )
    if workbook_output.exists():
        workbook_output.unlink()

    if bundle_root:
        bundle_directories = [Path(bundle_root)]
    else:
        bundle_directories = list_valid_runtime_bundle_directories(profile_root)

    results: list[MaterializedBundlePipelineRunResult] = []
    for directory in bundle_directories:
        bundle_id = directory.name
        extracted_record_path = (
            profile_paths.runtime_analysis_logs_root()
            / f"{bundle_id}_extracted_record.json"
        )
        projected_row_path = (
            profile_paths.runtime_exports_logs_root()
            / f"{bundle_id}_projected_row.json"
        )

        notes: list[str] = []
        if reuse_existing_analysis and extracted_record_path.exists():
            extracted_record = _load_extracted_record(extracted_record_path)
            notes.append("기존 bundle 분석 결과 JSON을 재사용했다.")
        else:
            analysis_results = run_materialized_bundle_analysis_smoke(
                profile_root=profile_root,
                bundle_root=str(directory),
                reuse_existing_analysis=False,
                wrapper=wrapper,
            )
            if not analysis_results:
                raise RuntimeError(f"bundle `{bundle_id}` 분석 결과를 만들지 못했다.")
            analysis_result = analysis_results[0]
            extracted_record_path = Path(analysis_result.extracted_record_path)
            extracted_record = _load_extracted_record(extracted_record_path)
            notes.extend(analysis_result.notes)

        projected_row = project_record_to_template(mapped_profile, extracted_record)
        projected_row_path.parent.mkdir(parents=True, exist_ok=True)
        projected_row_path.write_text(
            json.dumps(projected_row.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        append_result = append_projected_row_to_workbook(
            profile=mapped_profile,
            projected_row=projected_row,
            output_workbook_path=str(workbook_output),
            source_workbook_path=str(source_workbook_path or template_path),
        )

        if mapping.unresolved_headers:
            notes.append("일부 템플릿 헤더는 아직 rule 기반으로 확정되지 않았다.")
        notes.extend(append_result.notes)

        results.append(
            MaterializedBundlePipelineRunResult(
                bundle_id=bundle_id,
                extracted_record_path=str(extracted_record_path),
                projected_row_path=str(projected_row_path),
                output_workbook_path=str(workbook_output),
                appended_row_index=append_result.appended_row_index,
                notes=notes,
            )
        )

    removed_legacy_files = cleanup_legacy_export_workbooks(
        profile_root=profile_root,
        keep_paths=[workbook_output],
    )
    if removed_legacy_files:
        cleanup_note = (
            "기존 파일명 규칙과 맞지 않는 legacy 엑셀 산출물을 정리했다: "
            + ", ".join(path.name for path in removed_legacy_files)
        )
        for result in results:
            result.notes.append(cleanup_note)

    return results


def main() -> None:
    """기능: CLI에서 materialized bundle pipeline smoke를 실행한다.

    입력:
    - 없음

    반환:
    - 없음
    """

    parser = argparse.ArgumentParser(
        description="runtime bundle -> analysis -> exports smoke 실행"
    )
    parser.add_argument("--profile-id", default="kim-jm")
    parser.add_argument("--profile-root", default=str(default_profile_root()))
    parser.add_argument("--template-path", default=str(default_template_path()))
    parser.add_argument("--output-workbook-path", default="")
    parser.add_argument("--bundle-root", default="")
    parser.add_argument(
        "--reuse-existing-analysis",
        action="store_true",
        help="이미 저장된 bundle extracted_record JSON이 있으면 재사용한다.",
    )
    args = parser.parse_args()

    results = run_materialized_bundle_pipeline_smoke(
        profile_id=args.profile_id,
        profile_root=args.profile_root,
        template_path=args.template_path,
        output_workbook_path=args.output_workbook_path or None,
        bundle_root=args.bundle_root or None,
        reuse_existing_analysis=args.reuse_existing_analysis,
    )
    print(
        json.dumps(
            [result.to_dict() for result in results],
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
