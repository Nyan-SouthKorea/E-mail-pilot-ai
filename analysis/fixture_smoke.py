"""Fixture 기반 첫 분석 smoke를 위한 입력 loader와 실행기."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from mailbox import (
    extract_fixture_body,
    extract_fixture_header,
    find_fixture_attachment_dir,
    read_fixture_email_text,
)

from llm import OpenAIResponsesWrapper

from .artifact_summary import ArtifactSummary, summarize_attachment_directory
from .llm_extraction import (
    build_extracted_record_text_config,
    build_extraction_instructions,
    parse_extracted_record_payload,
)
from .multimodal_input import build_email_analysis_input_payload
from .schema import ExtractedRecord


@dataclass(slots=True)
class FixtureEmailInput:
    """기능: fixture 이메일 1건의 분석 입력을 표현한다."""

    fixture_id: str
    subject: str
    sender: str
    recipient: str
    body_text: str
    artifacts: list[ArtifactSummary] = field(default_factory=list)
    attachment_paths: list[str] = field(default_factory=list)

    def message_key(self) -> str:
        return self.fixture_id

    def bundle_id(self) -> str:
        return f"fixture:{self.fixture_id}"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def load_fixture_email_input(fixture_dir: str) -> FixtureEmailInput:
    """기능: profile fixture 디렉토리에서 이메일 분석 입력을 만든다.

    입력:
    - fixture_dir: `수신 이메일 1` 같은 fixture 디렉토리 경로

    반환:
    - `FixtureEmailInput`
    """

    root = Path(fixture_dir)
    raw_text = read_fixture_email_text(root)
    subject = extract_fixture_header(raw_text, "제목")
    sender = extract_fixture_header(raw_text, "보낸사람")
    recipient = extract_fixture_header(raw_text, "받는사람")
    body_text = extract_fixture_body(raw_text)

    attachment_dir = find_fixture_attachment_dir(root)
    artifacts: list[ArtifactSummary] = []

    attachment_paths: list[str] = []
    if attachment_dir is not None and attachment_dir.exists():
        artifacts = summarize_attachment_directory(attachment_dir)
        attachment_paths = [
            str(path)
            for path in sorted(attachment_dir.iterdir())
            if path.is_file()
        ]

    return FixtureEmailInput(
        fixture_id=root.name,
        subject=subject,
        sender=sender,
        recipient=recipient,
        body_text=body_text,
        artifacts=artifacts,
        attachment_paths=attachment_paths,
    )


def build_fixture_analysis_input_payload(fixture: FixtureEmailInput) -> list[dict[str, object]]:
    """기능: fixture 이메일 입력을 LLM용 멀티모달 payload로 만든다.

    입력:
    - fixture: fixture 이메일 입력

    반환:
    - Responses API `input` payload
    """

    return build_email_analysis_input_payload(
        subject=fixture.subject,
        sender=fixture.sender,
        recipient=fixture.recipient,
        body_text=fixture.body_text,
        artifact_summaries=fixture.artifacts,
        attachment_paths=fixture.attachment_paths,
    )


def build_fixture_analysis_request(fixture_dir: str) -> dict[str, Any]:
    """기능: fixture 분석용 OpenAI 래퍼 요청 dict를 만든다.

    입력:
    - fixture_dir: fixture 디렉토리 경로

    반환:
    - wrapper에 넘길 요청 dict
    """

    fixture = load_fixture_email_input(fixture_dir)
    return {
        "fixture": fixture,
        "wrapper_request": {
            "operation": "fixture_analysis_smoke",
            "instructions": build_extraction_instructions(),
            "input_payload": build_fixture_analysis_input_payload(fixture),
            "text": build_extracted_record_text_config(),
            "metadata": {
                "fixture_id": fixture.fixture_id,
                "bundle_id": fixture.bundle_id(),
                "message_key": fixture.message_key(),
            },
        },
    }


def run_fixture_analysis_smoke(
    fixture_dir: str,
    wrapper: OpenAIResponsesWrapper,
    *,
    dry_run: bool = False,
) -> dict[str, Any] | ExtractedRecord:
    """기능: fixture 이메일 1건에 대한 첫 분석 smoke를 실행한다.

    입력:
    - fixture_dir: fixture 디렉토리 경로
    - wrapper: OpenAI 공용 래퍼
    - dry_run: True면 실제 호출 없이 요청 payload만 반환

    반환:
    - dry_run이면 요청 dict, 아니면 `ExtractedRecord`
    """

    request = build_fixture_analysis_request(fixture_dir)
    if dry_run:
        return {
            "fixture": request["fixture"].to_dict(),
            "wrapper_request": request["wrapper_request"],
        }

    fixture: FixtureEmailInput = request["fixture"]
    envelope = wrapper.create_response(**request["wrapper_request"])
    parsed = envelope.parsed_output
    if parsed is not None:
        if hasattr(parsed, "model_dump"):
            payload = parsed.model_dump()
        elif hasattr(parsed, "to_dict"):
            payload = parsed.to_dict()
        else:
            payload = dict(parsed)
    else:
        try:
            payload = json.loads(envelope.output_text)
        except json.JSONDecodeError as exc:
            raise RuntimeError("structured output JSON을 파싱하지 못했습니다.") from exc

    return parse_extracted_record_payload(
        bundle_id=fixture.bundle_id(),
        message_key=fixture.message_key(),
        payload=payload,
    )
