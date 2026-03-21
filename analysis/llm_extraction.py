"""LLM 기반 `ExtractedRecord` 추출 계약을 정의한다."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .schema import ExtractedField, ExtractedRecord

EXTRACTED_RECORD_RESPONSE_SCHEMA_NAME = "email_extracted_record"


def build_extracted_record_response_schema() -> dict[str, Any]:
    """기능: `ExtractedRecord`용 structured output JSON schema를 반환한다.

    입력:
    - 없음

    반환:
    - Responses API `json_schema` dict
    """

    return {
        "name": EXTRACTED_RECORD_RESPONSE_SCHEMA_NAME,
        "type": "json_schema",
        "strict": True,
        "schema": {
            "type": "object",
            "additionalProperties": False,
            "required": [
                "record_type",
                "category",
                "summary_one_line",
                "summary_short",
                "overall_confidence",
                "fields",
                "action_hints",
                "unresolved_questions",
            ],
            "properties": {
                "record_type": {"type": "string"},
                "category": {"type": "string"},
                "summary_one_line": {"type": "string"},
                "summary_short": {"type": "string"},
                "overall_confidence": {"type": "number"},
                "fields": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": [
                            "field_name",
                            "value",
                            "normalized_value",
                            "confidence",
                            "evidence_ids",
                            "notes",
                        ],
                        "properties": {
                            "field_name": {"type": "string"},
                            "value": {"type": "string"},
                            "normalized_value": {
                                "type": ["string", "null"]
                            },
                            "confidence": {"type": ["number", "null"]},
                            "evidence_ids": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                            "notes": {"type": ["string", "null"]},
                        },
                    },
                },
                "action_hints": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "unresolved_questions": {
                    "type": "array",
                    "items": {"type": "string"},
                },
            },
        },
    }


def build_extracted_record_text_config() -> dict[str, Any]:
    """기능: structured output용 text 설정을 반환한다.

    입력:
    - 없음

    반환:
    - Responses API `text` 설정 dict
    """

    return {
        "format": build_extracted_record_response_schema(),
        "verbosity": "low",
    }


def build_extraction_instructions() -> str:
    """기능: 이메일/첨부 분석용 시스템 지시문을 반환한다.

    입력:
    - 없음

    반환:
    - 지시문 문자열
    """

    return (
        "당신은 이메일 신청 접수 문서를 읽고 구조화된 업무 레코드를 만드는 분석기다.\n"
        "주어진 자료는 이메일 메타데이터, 이메일 본문, ZIP 첨부 내부 파일 목록, "
        "그리고 일부 문서에서 추출한 표/텍스트 스니펫이다.\n"
        "반드시 JSON schema에 맞춰 응답하고, 사실로 확인되지 않은 내용은 추측하지 마라.\n"
        "fields[].field_name은 가능한 한 공통 의미 키에 가깝게 쓴다. 예: "
        "company_name, contact_name, phone_number, email_address, website_or_social, "
        "industry, product_or_service, target_region, application_purpose, "
        "company_intro_one_line, business_summary, request_summary.\n"
        "evidence_ids에는 자료 섹션에 표시된 근거 id만 넣는다.\n"
        "summary_one_line은 매우 짧은 한 줄, summary_short는 운영자가 읽기 좋은 2~3문장 요약으로 작성한다.\n"
        "내부 관리용 human-only 필드(예: internal_status, internal_notes)는 자동으로 채우지 마라."
    )


def parse_extracted_record_payload(
    *,
    bundle_id: str,
    message_key: str,
    payload: dict[str, Any],
) -> ExtractedRecord:
    """기능: LLM JSON payload를 `ExtractedRecord`로 바꾼다.

    입력:
    - bundle_id: 메일 번들 식별자
    - message_key: 메일 식별 키
    - payload: structured output dict

    반환:
    - `ExtractedRecord`
    """

    fields = [
        ExtractedField(
            field_name=item["field_name"],
            value=item["value"],
            normalized_value=item.get("normalized_value"),
            confidence=item.get("confidence"),
            evidence_ids=list(item.get("evidence_ids") or []),
            notes=item.get("notes"),
        )
        for item in payload.get("fields", [])
    ]

    return ExtractedRecord(
        bundle_id=bundle_id,
        message_key=message_key,
        record_type=payload.get("record_type", "unknown"),
        category=payload.get("category", "unknown"),
        fields=fields,
        summary_one_line=payload.get("summary_one_line", ""),
        summary_short=payload.get("summary_short", ""),
        overall_confidence=payload.get("overall_confidence"),
        action_hints=list(payload.get("action_hints") or []),
        unresolved_questions=list(payload.get("unresolved_questions") or []),
    )
