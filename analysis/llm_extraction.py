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
        "주어진 자료는 이메일 메타데이터, 이메일 본문, 첨부 요약, "
        "그리고 필요할 때 실제 이미지 입력이다.\n"
        "반드시 JSON schema에 맞춰 응답하고, 사실로 확인되지 않은 내용은 추측하지 마라.\n"
        "이미지가 함께 제공되면 텍스트 요약만 보지 말고 이미지 안의 글자, 표, 숫자, 문서 레이아웃도 직접 읽어라.\n"
        "같은 정보가 이메일 서명과 신청서 첨부에 모두 있으면, 기본적으로 신청서 첨부 값을 더 우선한다. "
        "이메일 서명값은 신청서에 없는 보조 정보일 때만 우선한다.\n"
        "신청서 첨부에 `웹사이트 / 담당자 연락처`처럼 한 줄에 여러 값이 있으면, 그 안의 웹사이트와 연락처를 "
        "이메일 서명보다 우선해 분리해서 읽는다.\n"
        "fields[].field_name은 가능한 한 공통 의미 키에 가깝게 쓴다. 예: "
        "company_name, contact_name, phone_number, email_address, website_or_social, "
        "industry, product_or_service, target_region, application_purpose, "
        "company_intro_one_line, business_summary, request_summary.\n"
        "company_name은 회사 법인격 표현보다 운영자가 보기 쉬운 대표 회사명으로 정리한다. "
        "예: '주식회사 벡스'는 '벡스'처럼 쓸 수 있다.\n"
        "contact_name은 가능한 한 신청서/본문에서 확인된 실제 담당자명을 우선하고, 없을 때만 서명값을 보조로 쓴다.\n"
        "phone_number는 한국 번호라면 운영자가 바로 읽기 쉬운 표시 형식으로 정리한다. "
        "예: 010-1234-5678, 070-1234-5678.\n"
        "website_or_social은 대표 URL 하나를 우선하고, 불필요한 trailing slash는 제거해도 된다.\n"
        "industry는 일반 회사 소개 문장보다 신청서에 적힌 산업군 표현을 우선한다.\n"
        "product_or_service는 신청서의 `요청 제품/서비스`를 우선하고, 필요할 때만 사업 내용의 핵심 품목을 보강한다. "
        "지나치게 포괄적인 표현으로 뭉개지지 않게 한다.\n"
        "application_purpose는 단순히 '참가 신청'이라고 쓰지 말고, 신청서에 드러난 실제 참가 목적과 사업 목표를 짧게 정리한다. "
        "운영자가 왜 이 기업이 참가하는지 바로 이해할 수 있게 써라.\n"
        "company_intro_one_line은 설립연도나 수식어보다 업종과 대표 제품/분야를 우선해 한 줄로 쓴다.\n"
        "business_summary는 국내 실적 소개보다 `무엇을 가지고 어떤 시장/파트너를 찾는지`가 보이도록 정리한다.\n"
        "request_summary는 상세 요청사항이 분명할 때만 압축해서 쓰고, application_purpose와 같은 말을 반복하지 마라.\n"
        "company_intro_one_line, business_summary, request_summary는 운영자가 Excel 한 줄에서 빨리 읽을 수 있게 중복 없이 짧고 선명하게 쓴다.\n"
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
