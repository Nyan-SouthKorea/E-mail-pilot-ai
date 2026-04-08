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
                "triage_label",
                "triage_reason",
                "triage_confidence",
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
                "triage_label": {"type": "string"},
                "triage_reason": {"type": "string"},
                "triage_confidence": {"type": ["number", "null"]},
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
        "모든 메일에는 triage_label, triage_reason, triage_confidence를 반드시 채운다.\n"
        "triage_label은 정확히 application, not_application, needs_human_review 중 하나만 사용한다.\n"
        "application은 실제 신청 의사와 신청 기업/담당자 정보가 확인될 때만 쓴다. "
        "본문이나 첨부에 참가 신청, 지원서 제출, 신청서 송부 같은 명시 신호가 있고 회사/담당자 식별이 가능해야 한다.\n"
        "not_application은 전시회 안내, 프로그램 소개, 참고자료 전달, 뉴스/홍보, 내부 메모, 자기 자신에게 보낸 정리 메일처럼 "
        "workbook 누적 대상이 아닌 메일에 쓴다.\n"
        "needs_human_review는 신청 가능성이 있지만 본문/첨부 신호가 약하거나 충돌할 때 쓴다.\n"
        "triage_reason은 왜 그렇게 분류했는지 근거 중심으로 한 문장으로 쓴다.\n"
        "triage_confidence는 0과 1 사이 숫자로 쓴다.\n"
        "기업 신청서가 아니라 전시회 소개, 프로그램 안내, 파트너 제안 메일처럼 직접 신청서 형식이 아닌 경우에도 "
        "운영자가 workbook에 넣어 관리할 수 있도록 업무형 필드를 best-effort로 채워라.\n"
        "이런 안내형 메일에서는 company_name에 주최/발신 organization을 우선 넣고, "
        "product_or_service에는 행사/프로그램 자체를, application_purpose에는 수신자 기준 검토 목적을, "
        "request_summary에는 다음 확인사항이나 요청 액션을 짧게 정리한다.\n"
        "summary_one_line과 summary_short는 본문 정보가 충분하면 비워 두지 마라.\n"
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

    record = ExtractedRecord(
        bundle_id=bundle_id,
        message_key=message_key,
        record_type=payload.get("record_type", "unknown"),
        category=payload.get("category", "unknown"),
        fields=fields,
        summary_one_line=payload.get("summary_one_line", ""),
        summary_short=payload.get("summary_short", ""),
        triage_label=payload.get("triage_label", "needs_human_review"),
        triage_reason=payload.get("triage_reason", ""),
        triage_confidence=payload.get("triage_confidence"),
        overall_confidence=payload.get("overall_confidence"),
        action_hints=list(payload.get("action_hints") or []),
        unresolved_questions=list(payload.get("unresolved_questions") or []),
    )
    return _postprocess_extracted_record(record)


def _postprocess_extracted_record(record: ExtractedRecord) -> ExtractedRecord:
    _normalize_triage_fields(record)
    _ensure_non_empty_summaries(record)
    if _looks_like_event_overview_record(record):
        _apply_event_overview_fallbacks(record)
        _ensure_non_empty_summaries(record)
    _ensure_triage_fallback(record)
    return record


def _normalize_triage_fields(record: ExtractedRecord) -> None:
    normalized = (
        (record.triage_label or "")
        .strip()
        .casefold()
        .replace("-", "_")
        .replace(" ", "_")
    )
    normalized = normalized.replace("__", "_")

    mapping = {
        "application": "application",
        "applicant": "application",
        "apply": "application",
        "registration": "application",
        "submit_application": "application",
        "not_application": "not_application",
        "non_application": "not_application",
        "information": "not_application",
        "info": "not_application",
        "overview": "not_application",
        "reference": "not_application",
        "needs_human_review": "needs_human_review",
        "need_human_review": "needs_human_review",
        "human_review": "needs_human_review",
        "review": "needs_human_review",
        "uncertain": "needs_human_review",
    }
    record.triage_label = mapping.get(normalized, "needs_human_review")

    if record.triage_confidence is not None:
        record.triage_confidence = round(
            min(1.0, max(0.0, float(record.triage_confidence))),
            2,
        )


def _ensure_triage_fallback(record: ExtractedRecord) -> None:
    has_company_signal = bool(_field_value(record, "company_name").strip())
    has_contact_signal = any(
        _field_value(record, field_name).strip()
        for field_name in ["contact_name", "phone_number", "email_address"]
    )
    text_blob = _record_text_blob(record)
    looks_like_application = any(
        token in text_blob
        for token in [
            "참가 신청",
            "신청 드립니다",
            "신청합니다",
            "참가기업 모집",
            "application",
            "registration",
            "submit",
        ]
    )
    looks_like_overview = _looks_like_event_overview_record(record) or any(
        token in text_blob
        for token in [
            "전시회 성격",
            "프로그램 안내",
            "참가 검토",
            "행사 소개",
            "overview",
            "guide",
        ]
    )

    if record.triage_label == "needs_human_review":
        if looks_like_application and has_company_signal and has_contact_signal:
            record.triage_label = "application"
        elif looks_like_overview and not has_contact_signal:
            record.triage_label = "not_application"

    if not record.triage_reason.strip():
        if record.triage_label == "application":
            record.triage_reason = (
                "본문 또는 첨부에서 실제 신청 의사와 기업/담당자 식별 신호가 함께 확인된다."
            )
        elif record.triage_label == "not_application":
            record.triage_reason = (
                "안내·참고·내부정리 성격이 강하고 workbook 누적용 신청서 신호가 충분하지 않다."
            )
        else:
            record.triage_reason = (
                "일부 신호는 있으나 신청 여부를 자동 확정하기에는 본문/첨부 근거가 더 필요하다."
            )

    if record.triage_confidence is None:
        if record.triage_label == "application":
            record.triage_confidence = 0.84 if has_company_signal and has_contact_signal else 0.72
        elif record.triage_label == "not_application":
            record.triage_confidence = 0.82 if looks_like_overview else 0.7
        else:
            record.triage_confidence = 0.56


def _record_text_blob(record: ExtractedRecord) -> str:
    parts = [
        record.record_type,
        record.category,
        record.summary_one_line,
        record.summary_short,
        " ".join(record.action_hints),
        " ".join(record.unresolved_questions),
    ]
    parts.extend(
        field.normalized_value or field.value
        for field in record.fields
        if (field.normalized_value or field.value).strip()
    )
    return " ".join(parts).casefold()


def _looks_like_event_overview_record(record: ExtractedRecord) -> bool:
    category_text = f"{record.record_type} {record.category}".casefold()
    if any(token in category_text for token in ["event", "exhibition", "fair", "program", "overview"]):
        return True

    field_names = set(record.field_map().keys())
    return bool(
        field_names.intersection(
            {
                "event_name",
                "event_type",
                "host_organization",
                "practical_fit",
                "booth_sizes_available",
            }
        )
    )


def _apply_event_overview_fallbacks(record: ExtractedRecord) -> None:
    _ensure_derived_field(
        record,
        field_name="company_name",
        value=_build_event_company_name(record),
        source_field_names=["host_organization", "event_name"],
        notes="전시회 안내형 메일에서 주최 기관/행사명을 기업명 fallback으로 사용했다.",
    )
    _ensure_derived_field(
        record,
        field_name="product_or_service",
        value=_build_event_product_or_service(record),
        source_field_names=["event_name", "event_type", "booth_sizes_available"],
        notes="전시회 안내형 메일에서 행사/프로그램 정보를 주요 제품·서비스 fallback으로 사용했다.",
    )
    _ensure_derived_field(
        record,
        field_name="application_purpose",
        value=_build_event_application_purpose(record),
        source_field_names=["event_name", "target_region", "practical_fit"],
        notes="전시회 안내형 메일에서 참가 검토 목적을 신청목적 fallback으로 구성했다.",
    )
    _ensure_derived_field(
        record,
        field_name="request_summary",
        value=_build_event_request_summary(record),
        source_field_names=["booth_sizes_available", "practical_fit"],
        notes="전시회 안내형 메일에서 다음 확인 액션을 상세 요청사항 fallback으로 구성했다.",
    )


def _ensure_non_empty_summaries(record: ExtractedRecord) -> None:
    if not record.summary_one_line.strip():
        fallback = _build_summary_one_line_fallback(record)
        if fallback:
            record.summary_one_line = fallback

    if not record.summary_short.strip():
        fallback = _build_summary_short_fallback(record)
        if fallback:
            record.summary_short = fallback


def _build_event_company_name(record: ExtractedRecord) -> str:
    return _field_value(record, "host_organization") or _field_value(record, "event_name")


def _build_event_product_or_service(record: ExtractedRecord) -> str:
    event_name = _field_value(record, "event_name")
    event_type = _field_value(record, "event_type")
    booth_sizes = _field_value(record, "booth_sizes_available")

    if event_name and event_type:
        return f"{event_name} {event_type}"
    if event_type:
        return event_type
    if event_name and booth_sizes:
        return f"{event_name} 전시회 및 부스 운영 프로그램"
    return event_name


def _build_event_application_purpose(record: ExtractedRecord) -> str:
    event_name = _field_value(record, "event_name") or "전시회"
    target_region = _field_value(record, "target_region")
    practical_fit = _condense_practical_fit(_field_value(record, "practical_fit"))

    if target_region and practical_fit:
        return f"{target_region} 시장 대상 {event_name} 참가 검토 및 {practical_fit}"
    if practical_fit:
        return f"{event_name} 참가 검토 및 {practical_fit}"
    if target_region:
        return f"{target_region} 시장 대상 {event_name} 정보 검토"
    return f"{event_name} 관련 사업 기회 검토"


def _build_event_request_summary(record: ExtractedRecord) -> str:
    parts: list[str] = []

    if record.action_hints:
        parts.append("전시회 참가 적합성 검토")

    if _field_value(record, "booth_sizes_available"):
        parts.append("부스 규모 옵션 검토")

    unresolved_text = " ".join(question.strip() for question in record.unresolved_questions if question.strip())
    if "일정" in unresolved_text and "참가비" in unresolved_text:
        parts.append("일정/참가비 추가 확인")
    else:
        if "일정" in unresolved_text:
            parts.append("개최 일정 확인")
        if "참가비" in unresolved_text:
            parts.append("참가비 확인")
        if "주소" in unresolved_text or "전시장" in unresolved_text:
            parts.append("전시장 세부 정보 확인")

    if not parts:
        application_purpose = _field_value(record, "application_purpose")
        if application_purpose:
            return application_purpose
        return "전시회 참가 여부와 세부 운영 조건 확인"

    return ", ".join(_unique_preserve_order(parts))


def _build_summary_one_line_fallback(record: ExtractedRecord) -> str:
    company_name = _field_value(record, "company_name") or _field_value(record, "host_organization")
    product_or_service = _field_value(record, "product_or_service") or _field_value(record, "event_type")
    event_name = _field_value(record, "event_name")

    if company_name and product_or_service:
        if event_name and event_name not in product_or_service:
            return f"{company_name}가 안내한 {event_name} {product_or_service}"
        return f"{company_name}가 안내한 {product_or_service}"
    if company_name and event_name:
        return f"{company_name}가 안내한 {event_name} 관련 메일"
    return company_name or event_name or ""


def _build_summary_short_fallback(record: ExtractedRecord) -> str:
    event_name = _field_value(record, "event_name")
    company_name = _field_value(record, "company_name") or _field_value(record, "host_organization")
    target_region = _field_value(record, "target_region")
    practical_fit = _field_value(record, "practical_fit")

    first_sentence_parts = [part for part in [company_name, event_name, target_region] if part]
    first_sentence = ""
    if first_sentence_parts:
        first_sentence = " / ".join(first_sentence_parts[:3]) + " 관련 안내입니다."

    second_sentence = ""
    if practical_fit:
        second_sentence = f"핵심 목적은 {_condense_practical_fit(practical_fit)}입니다."

    return " ".join(part for part in [first_sentence, second_sentence] if part).strip()


def _ensure_derived_field(
    record: ExtractedRecord,
    *,
    field_name: str,
    value: str,
    source_field_names: list[str],
    notes: str,
) -> None:
    if not value.strip():
        return

    if _field_value(record, field_name):
        return

    source_fields = [
        field
        for name in source_field_names
        if (field := record.field_map().get(name)) is not None and field.value.strip()
    ]

    record.fields.append(
        ExtractedField(
            field_name=field_name,
            value=value.strip(),
            normalized_value=value.strip(),
            confidence=_derived_confidence(source_fields),
            evidence_ids=_merge_evidence_ids(source_fields),
            notes=notes,
        )
    )


def _field_value(record: ExtractedRecord, field_name: str) -> str:
    field = record.field_map().get(field_name)
    if field is None:
        return ""
    return field.normalized_value or field.value


def _condense_practical_fit(text: str) -> str:
    normalized = text.replace("에 적합", "").replace("적합", "").strip(" .")
    if not normalized:
        return ""

    parts = [part.strip() for part in normalized.split(",") if part.strip()]
    if len(parts) >= 2:
        return f"{parts[0]} 및 {parts[1]} 기회 확인"
    return f"{parts[0]} 기회 확인"


def _derived_confidence(source_fields: list[ExtractedField]) -> float:
    confidences = [field.confidence for field in source_fields if field.confidence is not None]
    if not confidences:
        return 0.72
    return round(max(0.6, min(0.95, (sum(confidences) / len(confidences)) - 0.08)), 2)


def _merge_evidence_ids(source_fields: list[ExtractedField]) -> list[str]:
    evidence_ids: list[str] = []
    for field in source_fields:
        for evidence_id in field.evidence_ids:
            if evidence_id not in evidence_ids:
                evidence_ids.append(evidence_id)
    return evidence_ids


def _unique_preserve_order(items: list[str]) -> list[str]:
    unique_items: list[str] = []
    for item in items:
        if item not in unique_items:
            unique_items.append(item)
    return unique_items
