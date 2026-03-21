"""materialized MailBundle을 직접 읽어 분석하는 smoke."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from llm import OpenAIResponsesConfig, OpenAIResponsesWrapper
from mailbox.bundle_reader import (
    list_bundle_attachment_files,
    list_valid_runtime_bundle_directories,
    load_normalized_message_from_bundle,
)
from project_paths import ProfilePaths, default_example_profile_root

from .artifact_summary import ArtifactSummary, summarize_attachment_paths
from .llm_extraction import (
    build_extracted_record_text_config,
    build_extraction_instructions,
    parse_extracted_record_payload,
)


@dataclass(slots=True)
class MaterializedBundleAnalysisResult:
    """기능: bundle 1건 분석 smoke 결과를 표현한다.

    입력:
    - bundle_id: 처리한 bundle id
    - extracted_record_path: 저장된 분석 결과 JSON 경로
    - artifact_count: 분석에 사용한 첨부 자산 수
    - notes: 보조 메모

    반환:
    - dataclass 인스턴스
    """

    bundle_id: str
    extracted_record_path: str
    artifact_count: int
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        """기능: 결과를 JSON 직렬화용 dict로 바꾼다.

        입력:
        - 없음

        반환:
        - dict
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


def run_materialized_bundle_analysis_smoke(
    *,
    profile_root: str,
    bundle_root: str | None = None,
    reuse_existing_analysis: bool = False,
    wrapper: OpenAIResponsesWrapper | None = None,
) -> list[MaterializedBundleAnalysisResult]:
    """기능: materialized bundle을 직접 읽어 LLM 분석 smoke를 실행한다.

    입력:
    - profile_root: 사용자 프로필 루트 경로
    - bundle_root: 특정 bundle만 돌리고 싶을 때의 경로
    - reuse_existing_analysis: 기존 JSON을 재사용할지 여부
    - wrapper: OpenAI 공용 래퍼

    반환:
    - bundle별 분석 결과 목록
    """

    profile_paths = ProfilePaths(profile_root)
    profile_paths.ensure_runtime_dirs()

    wrapper = wrapper or OpenAIResponsesWrapper(
        OpenAIResponsesConfig(
            usage_log_path=str(profile_paths.llm_usage_log_path()),
        )
    )

    if bundle_root:
        bundle_directories = [Path(bundle_root)]
    else:
        bundle_directories = list_valid_runtime_bundle_directories(profile_root)

    results: list[MaterializedBundleAnalysisResult] = []
    for directory in bundle_directories:
        results.append(
            _analyze_single_bundle(
                bundle_root=directory,
                profile_paths=profile_paths,
                wrapper=wrapper,
                reuse_existing_analysis=reuse_existing_analysis,
            )
        )
    return results


def _analyze_single_bundle(
    *,
    bundle_root: Path,
    profile_paths: ProfilePaths,
    wrapper: OpenAIResponsesWrapper,
    reuse_existing_analysis: bool,
) -> MaterializedBundleAnalysisResult:
    normalized = load_normalized_message_from_bundle(bundle_root)
    artifact_summaries = summarize_attachment_paths(
        list_bundle_attachment_files(bundle_root),
        artifact_ids=normalized.attachment_artifact_ids,
    )

    output_path = (
        profile_paths.runtime_analysis_logs_root()
        / f"{normalized.bundle_id}_extracted_record.json"
    )
    notes: list[str] = []

    if reuse_existing_analysis and output_path.exists():
        notes.append("기존 bundle 분석 결과 JSON을 재사용했다.")
        return MaterializedBundleAnalysisResult(
            bundle_id=normalized.bundle_id,
            extracted_record_path=str(output_path),
            artifact_count=len(artifact_summaries),
            notes=notes,
        )

    envelope = wrapper.create_response(
        operation="materialized_bundle_analysis_smoke",
        instructions=build_extraction_instructions(),
        input_payload=build_materialized_bundle_analysis_input_payload(
            normalized_message=normalized,
            artifact_summaries=artifact_summaries,
        ),
        text=build_extracted_record_text_config(),
        metadata={
            "bundle_id": normalized.bundle_id,
            "message_key": normalized.message_key,
            "source": "materialized_bundle",
        },
    )

    parsed = envelope.parsed_output
    if parsed is not None:
        if hasattr(parsed, "model_dump"):
            payload = parsed.model_dump()
        elif hasattr(parsed, "to_dict"):
            payload = parsed.to_dict()
        else:
            payload = dict(parsed)
    else:
        payload = json.loads(envelope.output_text)

    extracted_record = parse_extracted_record_payload(
        bundle_id=normalized.bundle_id,
        message_key=normalized.message_key,
        payload=payload,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(extracted_record.to_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return MaterializedBundleAnalysisResult(
        bundle_id=normalized.bundle_id,
        extracted_record_path=str(output_path),
        artifact_count=len(artifact_summaries),
        notes=notes,
    )


def build_materialized_bundle_analysis_input_payload(
    *,
    normalized_message,
    artifact_summaries: list[ArtifactSummary],
) -> str:
    """기능: `NormalizedMessage` 기반 분석용 LLM 입력 문자열을 만든다.

    입력:
    - normalized_message: 공통 메일 입력
    - artifact_summaries: 첨부 자산 요약 목록

    반환:
    - LLM 입력 문자열
    """

    sender_text = _format_address(normalized_message.sender)
    recipient_text = ", ".join(_format_address(item) for item in normalized_message.to) or ""

    lines = [
        "[email_metadata]",
        "evidence_id: header_subject",
        f"subject: {normalized_message.subject}",
        "evidence_id: header_sender",
        f"sender: {sender_text}",
        "evidence_id: header_recipient",
        f"recipient: {recipient_text}",
        "",
        "[email_body]",
        "evidence_id: body_text",
        normalized_message.body_text.strip(),
        "",
        "[attachment_artifacts]",
    ]

    if not artifact_summaries:
        lines.append("첨부 없음")
    else:
        for artifact in artifact_summaries:
            lines.append(f"evidence_id: {artifact.evidence_id}")
            lines.append(f"name: {artifact.artifact_name}")
            lines.append(f"kind: {artifact.artifact_kind}")
            lines.append(artifact.summary_text)
            lines.append("")

    return "\n".join(lines).strip()


def _format_address(address) -> str:
    if address.name:
        return f"{address.name} <{address.email}>"
    return address.email


def main() -> None:
    """기능: CLI에서 materialized bundle 분석 smoke를 실행한다.

    입력:
    - 없음

    반환:
    - 없음
    """

    parser = argparse.ArgumentParser(description="materialized bundle analysis smoke")
    parser.add_argument("--profile-root", default=str(default_profile_root()))
    parser.add_argument("--bundle-root", default="")
    parser.add_argument(
        "--reuse-existing-analysis",
        action="store_true",
        help="이미 저장된 extracted_record JSON이 있으면 재사용한다.",
    )
    args = parser.parse_args()

    results = run_materialized_bundle_analysis_smoke(
        profile_root=args.profile_root,
        bundle_root=args.bundle_root or None,
        reuse_existing_analysis=args.reuse_existing_analysis,
    )
    print(json.dumps([item.to_dict() for item in results], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
