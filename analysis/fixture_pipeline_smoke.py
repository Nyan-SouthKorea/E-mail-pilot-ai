"""Fixture 이메일에서 workbook append까지 한 번에 도는 smoke."""

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
    project_record_to_template,
    read_template_profile,
)
from llm import OpenAIResponsesConfig, OpenAIResponsesWrapper
from project_paths import ProfilePaths, default_example_profile_root

if __package__ in (None, ""):
    from analysis.fixture_smoke import load_fixture_email_input, run_fixture_analysis_smoke
    from analysis.schema import ExtractedRecord
else:
    from .fixture_smoke import load_fixture_email_input, run_fixture_analysis_smoke
    from .schema import ExtractedRecord


@dataclass(slots=True)
class FixturePipelineRunResult:
    """기능: fixture 1건의 end-to-end smoke 결과를 표현한다.

    입력:
    - fixture_id: 처리한 fixture 식별자
    - extracted_record_path: 저장한 분석 결과 JSON 경로
    - projected_row_path: 저장한 projection JSON 경로
    - output_workbook_path: 결과 workbook 경로
    - appended_row_index: append된 행 번호
    - notes: 추가 메모

    반환:
    - dataclass 인스턴스
    """

    fixture_id: str
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


def default_analysis_results_dir(profile_root: str) -> Path:
    """기능: 분석 smoke 산출물 기본 저장 경로를 반환한다.

    입력:
    - profile_root: 사용자 프로필 루트 경로

    반환:
    - `실행결과/로그/analysis_smoke`
    """

    profile_paths = ProfilePaths(profile_root)
    return profile_paths.runtime_analysis_logs_root()


def default_exports_results_dir(profile_root: str) -> Path:
    """기능: export workbook 기본 저장 경로를 반환한다.

    입력:
    - profile_root: 사용자 프로필 루트 경로

    반환:
    - `실행결과/엑셀 산출물`
    """

    profile_paths = ProfilePaths(profile_root)
    return profile_paths.runtime_exports_root()


def list_fixture_directories(profile_root: str) -> list[Path]:
    """기능: 프로필 루트 아래의 fixture 이메일 디렉토리 목록을 반환한다.

    입력:
    - profile_root: 사용자 프로필 루트 경로

    반환:
    - `수신 이메일*` 디렉토리 목록
    """

    root = ProfilePaths(profile_root).fixture_examples_root()
    directories = [
        path
        for path in sorted(root.iterdir())
        if path.is_dir() and path.name.startswith("수신 이메일")
    ]
    return directories


def run_fixture_pipeline_smoke(
    *,
    profile_id: str,
    profile_root: str,
    template_path: str,
    output_workbook_path: str | None = None,
    reuse_existing_analysis: bool = False,
    wrapper: OpenAIResponsesWrapper | None = None,
) -> list[FixturePipelineRunResult]:
    """기능: fixture 이메일들을 분석해 workbook에 append하는 smoke를 실행한다.

    입력:
    - profile_id: 템플릿 프로필 식별자
    - profile_root: fixture와 reference가 있는 사용자 프로필 루트
    - template_path: reference workbook 경로
    - output_workbook_path: 결과 workbook 경로
    - reuse_existing_analysis: 기존 분석 JSON이 있으면 재사용할지 여부
    - wrapper: OpenAI 공용 래퍼. 없으면 기본 설정으로 생성

    반환:
    - fixture별 실행 결과 목록
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

    analysis_results_dir = default_analysis_results_dir(profile_root)
    exports_results_dir = default_exports_results_dir(profile_root)
    analysis_results_dir.mkdir(parents=True, exist_ok=True)
    exports_results_dir.mkdir(parents=True, exist_ok=True)

    workbook_output = Path(output_workbook_path) if output_workbook_path else (
        exports_results_dir / f"{Path(template_path).stem}_fixture_pipeline.xlsx"
    )
    if workbook_output.exists():
        workbook_output.unlink()

    results: list[FixturePipelineRunResult] = []
    for index, fixture_dir in enumerate(list_fixture_directories(profile_root), start=1):
        fixture = load_fixture_email_input(str(fixture_dir))
        extracted_record_path = analysis_results_dir / f"fixture{index}_extracted_record.json"
        projected_row_path = analysis_results_dir / f"fixture{index}_projected_row.json"

        if reuse_existing_analysis and extracted_record_path.exists():
            extracted_record = ExtractedRecord.from_dict(
                json.loads(extracted_record_path.read_text(encoding="utf-8"))
            )
            notes = ["기존 분석 결과 JSON을 재사용했다."]
        else:
            extracted_record = run_fixture_analysis_smoke(
                fixture_dir=str(fixture_dir),
                wrapper=wrapper,
                dry_run=False,
            )
            extracted_record_path.write_text(
                json.dumps(extracted_record.to_dict(), ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            notes = []

        projected_row = project_record_to_template(mapped_profile, extracted_record)
        projected_row_path.write_text(
            json.dumps(projected_row.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        append_result = append_projected_row_to_workbook(
            profile=mapped_profile,
            projected_row=projected_row,
            output_workbook_path=str(workbook_output),
        )

        if mapping.unresolved_headers:
            notes.append("일부 템플릿 헤더는 아직 rule 기반으로 확정되지 않았다.")
        notes.extend(append_result.notes)

        results.append(
            FixturePipelineRunResult(
                fixture_id=fixture.fixture_id,
                extracted_record_path=str(extracted_record_path),
                projected_row_path=str(projected_row_path),
                output_workbook_path=str(workbook_output),
                appended_row_index=append_result.appended_row_index,
                notes=notes,
            )
        )

    return results


def main() -> None:
    """기능: CLI에서 fixture pipeline smoke를 실행한다.

    입력:
    - 없음

    반환:
    - 없음
    """

    parser = argparse.ArgumentParser(description="fixture pipeline smoke 실행")
    parser.add_argument("--profile-id", default="kim-jm")
    parser.add_argument("--profile-root", default=str(default_profile_root()))
    parser.add_argument("--template-path", default=str(default_template_path()))
    parser.add_argument("--output-workbook-path", default="")
    parser.add_argument(
        "--reuse-existing-analysis",
        action="store_true",
        help="이미 저장된 extracted_record JSON이 있으면 재사용한다.",
    )
    args = parser.parse_args()

    results = run_fixture_pipeline_smoke(
        profile_id=args.profile_id,
        profile_root=args.profile_root,
        template_path=args.template_path,
        output_workbook_path=args.output_workbook_path or None,
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
