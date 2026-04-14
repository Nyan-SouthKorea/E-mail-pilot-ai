"""materialized MailBundle을 직접 읽어 분석하는 smoke."""

from __future__ import annotations

import argparse
from hashlib import sha256
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

if __package__ in (None, ""):
    from analysis.artifact_summary import ArtifactSummary, summarize_attachment_paths
    from analysis.llm_extraction import (
        build_extracted_record_text_config,
        build_extraction_instructions,
        parse_extracted_record_payload,
    )
    from analysis.multimodal_input import build_email_analysis_input_payload
else:
    from .artifact_summary import ArtifactSummary, summarize_attachment_paths
    from .llm_extraction import (
        build_extracted_record_text_config,
        build_extraction_instructions,
        parse_extracted_record_payload,
    )
    from .multimodal_input import build_email_analysis_input_payload


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


ANALYSIS_REVISION = "analysis.materialized_bundle.v2"


def run_materialized_bundle_analysis_smoke(
    *,
    profile_root: str,
    bundle_root: str | None = None,
    reuse_existing_analysis: bool = False,
    wrapper: OpenAIResponsesWrapper | None = None,
    custom_guidance: str = "",
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
                custom_guidance=custom_guidance,
            )
        )
    return results


def _analyze_single_bundle(
    *,
    bundle_root: Path,
    profile_paths: ProfilePaths,
    wrapper: OpenAIResponsesWrapper,
    reuse_existing_analysis: bool,
    custom_guidance: str,
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
    meta_path = output_path.with_suffix(".meta.json")
    summary_path = bundle_root / "summary.md"
    notes: list[str] = []
    current_fingerprint = build_bundle_analysis_fingerprint(bundle_root)
    current_guidance_fingerprint = sha256(custom_guidance.strip().encode("utf-8")).hexdigest()

    if reuse_existing_analysis and output_path.exists() and _can_reuse_existing_analysis(
        output_path=output_path,
        meta_path=meta_path,
        current_fingerprint=current_fingerprint,
        current_guidance_fingerprint=current_guidance_fingerprint,
    ):
        _ensure_summary_markdown_from_record(
            output_path=output_path,
            summary_path=summary_path,
        )
        notes.append("기존 bundle 분석 결과 JSON을 fingerprint 기준으로 재사용했다.")
        return MaterializedBundleAnalysisResult(
            bundle_id=normalized.bundle_id,
            extracted_record_path=str(output_path),
            artifact_count=len(artifact_summaries),
            notes=notes,
        )

    envelope = wrapper.create_response(
        operation="materialized_bundle_analysis_smoke",
        instructions=build_extraction_instructions(custom_guidance=custom_guidance),
        input_payload=build_materialized_bundle_analysis_input_payload(
            normalized_message=normalized,
            artifact_summaries=artifact_summaries,
            attachment_paths=list_bundle_attachment_files(bundle_root),
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
    summary_path.write_text(
        _build_summary_markdown(extracted_record),
        encoding="utf-8",
    )
    meta_path.write_text(
        json.dumps(
            {
                "analysis_revision": ANALYSIS_REVISION,
                "bundle_fingerprint": current_fingerprint,
                "guidance_fingerprint": current_guidance_fingerprint,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    return MaterializedBundleAnalysisResult(
        bundle_id=normalized.bundle_id,
        extracted_record_path=str(output_path),
        artifact_count=len(artifact_summaries),
        notes=notes,
    )


def build_bundle_analysis_fingerprint(bundle_root: Path) -> str:
    digest = sha256()
    for path in sorted(bundle_root.rglob("*")):
        if not path.is_file():
            continue
        relative_path = path.relative_to(bundle_root).as_posix()
        stat = path.stat()
        digest.update(relative_path.encode("utf-8"))
        digest.update(str(stat.st_size).encode("ascii"))
        digest.update(str(stat.st_mtime_ns).encode("ascii"))
    return digest.hexdigest()


def _can_reuse_existing_analysis(
    *,
    output_path: Path,
    meta_path: Path,
    current_fingerprint: str,
    current_guidance_fingerprint: str,
) -> bool:
    if not output_path.exists() or not meta_path.exists():
        return False
    try:
        payload = json.loads(meta_path.read_text(encoding="utf-8"))
    except Exception:
        return False
    return (
        str(payload.get("analysis_revision") or "") == ANALYSIS_REVISION
        and str(payload.get("bundle_fingerprint") or "") == current_fingerprint
        and str(payload.get("guidance_fingerprint") or "") == current_guidance_fingerprint
    )


def _ensure_summary_markdown_from_record(*, output_path: Path, summary_path: Path) -> None:
    if summary_path.exists():
        return
    try:
        payload = json.loads(output_path.read_text(encoding="utf-8"))
    except Exception:
        return
    extracted_record = parse_extracted_record_payload(
        bundle_id=str(payload.get("bundle_id") or ""),
        message_key=str(payload.get("message_key") or ""),
        payload=payload,
    )
    summary_path.write_text(
        _build_summary_markdown(extracted_record),
        encoding="utf-8",
    )


def _build_summary_markdown(extracted_record) -> str:
    summary_lines = [
        "# 요약 메모",
        "",
        f"- 한 줄 요약: {extracted_record.summary_one_line or '(없음)'}",
        f"- 짧은 요약: {extracted_record.summary_short or '(없음)'}",
        f"- 분류: {extracted_record.triage_label or '(없음)'}",
        f"- 분류 근거: {extracted_record.triage_reason or '(없음)'}",
    ]
    request_summary = ""
    for field in extracted_record.fields:
        if getattr(field, "field_name", "") == "request_summary":
            request_summary = (getattr(field, "normalized_value", None) or getattr(field, "value", "") or "").strip()
            break
    if request_summary:
        summary_lines.append(f"- 요청 요약: {request_summary}")
    return "\n".join(summary_lines).strip() + "\n"


def build_materialized_bundle_analysis_input_payload(
    *,
    normalized_message,
    artifact_summaries: list[ArtifactSummary],
    attachment_paths: list[Path],
) -> list[dict[str, object]]:
    """기능: `NormalizedMessage` 기반 분석용 멀티모달 LLM 입력 payload를 만든다.

    입력:
    - normalized_message: 공통 메일 입력
    - artifact_summaries: 첨부 자산 요약 목록
    - attachment_paths: 실제 첨부 파일 경로 목록

    반환:
    - Responses API `input` payload
    """

    sender_text = _format_address(normalized_message.sender)
    recipient_text = ", ".join(_format_address(item) for item in normalized_message.to) or ""
    return build_email_analysis_input_payload(
        subject=normalized_message.subject,
        sender=sender_text,
        recipient=recipient_text,
        body_text=normalized_message.body_text,
        artifact_summaries=artifact_summaries,
        attachment_paths=attachment_paths,
        artifact_ids=normalized_message.attachment_artifact_ids,
    )


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
