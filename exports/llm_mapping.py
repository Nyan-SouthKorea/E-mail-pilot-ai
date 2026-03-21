"""Rule로 해결되지 않은 템플릿 헤더를 LLM으로 보충 매핑한다."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from llm import OpenAIResponsesWrapper

from .rule_mapping import build_rule_based_template_mapping
from .schema import TemplateProfile
from .semantic_mapping import (
    SemanticFieldDefinition,
    TemplateColumnSemanticMapping,
    TemplateSemanticMapping,
    apply_template_semantic_mapping,
    default_semantic_field_definitions,
    merge_template_semantic_mappings,
    semantic_field_definition_map,
)

UNRESOLVED_TEMPLATE_HEADER_SENTINEL = "__unresolved__"


@dataclass(slots=True)
class UnresolvedTemplateHeader:
    """기능: rule 기반으로 확정하지 못한 템플릿 헤더 정보를 표현한다.

    입력:
    - sheet_name: 헤더가 속한 시트명
    - column_index: 1-based 열 번호
    - header_text: 원본 헤더 텍스트
    - example_value: 템플릿에서 관찰한 예시 값
    - example_cell_ref: 예시 값 셀 주소

    반환:
    - dataclass 인스턴스
    """

    sheet_name: str
    column_index: int
    header_text: str
    example_value: str | None = None
    example_cell_ref: str | None = None

    def to_dict(self) -> dict[str, object]:
        """기능: 헤더 정보를 JSON 직렬화용 dict로 바꾼다.

        입력:
        - 없음

        반환:
        - dict
        """

        return {
            "sheet_name": self.sheet_name,
            "column_index": self.column_index,
            "header_text": self.header_text,
            "example_value": self.example_value,
            "example_cell_ref": self.example_cell_ref,
        }


def build_hybrid_template_mapping(
    profile: TemplateProfile,
    *,
    wrapper: OpenAIResponsesWrapper | None = None,
    definitions: list[SemanticFieldDefinition] | None = None,
    model: str | None = None,
) -> TemplateSemanticMapping:
    """기능: rule 우선, unresolved만 LLM fallback으로 보충한 매핑을 만든다.

    입력:
    - profile: 템플릿 프로필
    - wrapper: OpenAI 공용 래퍼
    - definitions: 공통 의미 필드 정의 목록
    - model: 필요 시 사용할 모델명

    반환:
    - 병합된 `TemplateSemanticMapping`
    """

    definitions = definitions or default_semantic_field_definitions()
    rule_mapping = build_rule_based_template_mapping(profile, definitions=definitions)
    if not rule_mapping.unresolved_headers:
        return rule_mapping

    llm_mapping = build_llm_fallback_template_mapping(
        profile=profile,
        base_mapping=rule_mapping,
        wrapper=wrapper,
        definitions=definitions,
        model=model,
    )
    merged_mapping = merge_template_semantic_mappings(rule_mapping, llm_mapping)
    return merged_mapping


def apply_hybrid_template_mapping(
    profile: TemplateProfile,
    *,
    wrapper: OpenAIResponsesWrapper | None = None,
    definitions: list[SemanticFieldDefinition] | None = None,
    model: str | None = None,
) -> tuple[TemplateProfile, TemplateSemanticMapping]:
    """기능: rule-first + LLM fallback 매핑을 만들고 프로필에 반영한다.

    입력:
    - profile: 의미 키가 비어 있는 템플릿 프로필
    - wrapper: OpenAI 공용 래퍼
    - definitions: 공통 의미 필드 정의 목록
    - model: 필요 시 사용할 모델명

    반환:
    - `(semantic_key 반영된 profile, merged mapping)`
    """

    mapping = build_hybrid_template_mapping(
        profile,
        wrapper=wrapper,
        definitions=definitions,
        model=model,
    )
    mapped_profile = apply_template_semantic_mapping(profile, mapping)
    return mapped_profile, mapping


def build_llm_fallback_template_mapping(
    *,
    profile: TemplateProfile,
    base_mapping: TemplateSemanticMapping,
    wrapper: OpenAIResponsesWrapper | None = None,
    definitions: list[SemanticFieldDefinition] | None = None,
    model: str | None = None,
) -> TemplateSemanticMapping:
    """기능: unresolved template header만 대상으로 LLM fallback 매핑을 만든다.

    입력:
    - profile: 템플릿 프로필
    - base_mapping: 우선 적용된 rule 기반 매핑
    - wrapper: OpenAI 공용 래퍼
    - definitions: 공통 의미 필드 정의 목록
    - model: 필요 시 사용할 모델명

    반환:
    - unresolved 헤더 보충용 `TemplateSemanticMapping`
    """

    definitions = definitions or default_semantic_field_definitions()
    unresolved_headers = collect_unresolved_template_headers(
        profile=profile,
        base_mapping=base_mapping,
    )
    if not unresolved_headers:
        return TemplateSemanticMapping(
            profile_id=profile.profile_id,
            template_id=profile.template_id,
            notes=["LLM fallback 대상 unresolved header가 없었다."],
        )

    wrapper = wrapper or OpenAIResponsesWrapper()
    envelope = wrapper.create_response(
        operation="template_semantic_mapping_fallback",
        model=model,
        instructions=build_llm_template_mapping_instructions(definitions),
        input_payload=build_llm_template_mapping_input(
            profile=profile,
            unresolved_headers=unresolved_headers,
            definitions=definitions,
        ),
        text={
            "format": build_llm_template_mapping_response_schema(definitions),
            "verbosity": "low",
        },
        metadata={
            "profile_id": profile.profile_id,
            "template_id": profile.template_id,
            "unresolved_header_count": str(len(unresolved_headers)),
        },
    )

    payload = _parse_llm_mapping_payload(envelope)
    definition_map = semantic_field_definition_map()

    llm_mappings: list[TemplateColumnSemanticMapping] = []
    unresolved_refs_by_key = {
        (item.sheet_name, item.column_index): item for item in unresolved_headers
    }

    for item in payload.get("items", []):
        semantic_key = item.get("semantic_key") or UNRESOLVED_TEMPLATE_HEADER_SENTINEL
        if semantic_key == UNRESOLVED_TEMPLATE_HEADER_SENTINEL:
            continue
        if semantic_key not in definition_map:
            continue

        key = (str(item["sheet_name"]), int(item["column_index"]))
        unresolved_header = unresolved_refs_by_key.get(key)
        header_text = (
            unresolved_header.header_text
            if unresolved_header is not None
            else str(item["header_text"])
        )

        llm_mappings.append(
            TemplateColumnSemanticMapping(
                sheet_name=str(item["sheet_name"]),
                column_index=int(item["column_index"]),
                header_text=header_text,
                semantic_key=semantic_key,
                confidence=float(item.get("confidence") or 0.0),
                matched_by="llm_fallback",
                rationale=str(item.get("rationale") or ""),
                notes=["rule 기반 unresolved header에 대한 LLM fallback"],
            )
        )

    llm_resolved_refs = {
        f"{item.sheet_name}:{item.header_text}"
        for item in llm_mappings
    }
    unresolved_headers_after_llm = [
        f"{item.sheet_name}:{item.header_text}"
        for item in unresolved_headers
        if f"{item.sheet_name}:{item.header_text}" not in llm_resolved_refs
    ]

    notes: list[str] = [
        "rule 기반 unresolved header만 LLM fallback으로 보충했다.",
    ]
    if unresolved_headers_after_llm:
        notes.append("일부 헤더는 LLM fallback 후에도 unresolved 상태로 남았다.")

    return TemplateSemanticMapping(
        profile_id=profile.profile_id,
        template_id=profile.template_id,
        mappings=llm_mappings,
        unresolved_headers=unresolved_headers_after_llm,
        notes=notes,
    )


def collect_unresolved_template_headers(
    *,
    profile: TemplateProfile,
    base_mapping: TemplateSemanticMapping,
) -> list[UnresolvedTemplateHeader]:
    """기능: 아직 의미 키가 없는 템플릿 헤더 목록을 수집한다.

    입력:
    - profile: 템플릿 프로필
    - base_mapping: 이미 적용된 매핑 결과

    반환:
    - unresolved header 정보 목록
    """

    unresolved_headers: list[UnresolvedTemplateHeader] = []
    for sheet in profile.sheets:
        for column in sheet.columns:
            matched_mapping = base_mapping.mapping_for(
                sheet_name=sheet.sheet_name,
                column_index=column.column_index,
            )
            if matched_mapping is not None:
                continue

            unresolved_headers.append(
                UnresolvedTemplateHeader(
                    sheet_name=sheet.sheet_name,
                    column_index=column.column_index,
                    header_text=column.header_text,
                    example_value=column.example_value,
                    example_cell_ref=column.example_cell_ref,
                )
            )

    return unresolved_headers


def build_llm_template_mapping_input(
    *,
    profile: TemplateProfile,
    unresolved_headers: list[UnresolvedTemplateHeader],
    definitions: list[SemanticFieldDefinition],
) -> str:
    """기능: unresolved header 의미 보충용 LLM 입력 텍스트를 만든다.

    입력:
    - profile: 템플릿 프로필
    - unresolved_headers: unresolved header 목록
    - definitions: 공통 의미 필드 정의 목록

    반환:
    - LLM 입력 문자열
    """

    lines = [
        f"[template_profile]",
        f"profile_id: {profile.profile_id}",
        f"template_id: {profile.template_id}",
        "",
        "[available_semantic_fields]",
    ]

    for definition in definitions:
        lines.append(f"semantic_key: {definition.semantic_key}")
        lines.append(f"display_name: {definition.display_name}")
        lines.append(f"field_role: {definition.field_role}")
        lines.append(f"description: {definition.description}")
        lines.append(
            "example_headers: "
            + ", ".join(definition.example_headers or ["(없음)"])
        )
        lines.append("")

    lines.append("[unresolved_headers]")
    for item in unresolved_headers:
        lines.append(f"sheet_name: {item.sheet_name}")
        lines.append(f"column_index: {item.column_index}")
        lines.append(f"header_text: {item.header_text}")
        lines.append(f"example_value: {item.example_value or '(없음)'}")
        lines.append(f"example_cell_ref: {item.example_cell_ref or '(없음)'}")
        lines.append("")

    return "\n".join(lines).strip()


def build_llm_template_mapping_instructions(
    definitions: list[SemanticFieldDefinition],
) -> str:
    """기능: unresolved header 보충 매핑용 시스템 지시문을 만든다.

    입력:
    - definitions: 공통 의미 필드 정의 목록

    반환:
    - 지시문 문자열
    """

    allowed_keys = ", ".join(
        [definition.semantic_key for definition in definitions]
        + [UNRESOLVED_TEMPLATE_HEADER_SENTINEL]
    )
    return (
        "당신은 Excel 템플릿의 헤더 이름을 공통 의미 키로 분류하는 보조 매퍼다.\n"
        "반드시 unresolved header만 판단하고, 확실하지 않으면 semantic_key를 "
        f"`{UNRESOLVED_TEMPLATE_HEADER_SENTINEL}`로 둔다.\n"
        "허용된 semantic_key는 다음뿐이다:\n"
        f"{allowed_keys}\n"
        "header_text, example_value, display_name, description, example_headers를 함께 보고 가장 가까운 의미 키를 고른다.\n"
        "사람 전용 내부 관리 필드는 internal_status 또는 internal_notes만 사용한다.\n"
        "번호 같은 순번 열은 row_number를 사용한다.\n"
        "반드시 JSON schema에 맞춰 응답하고, 각 판단 이유를 rationale에 짧게 남긴다."
    )


def build_llm_template_mapping_response_schema(
    definitions: list[SemanticFieldDefinition],
) -> dict[str, Any]:
    """기능: unresolved header 의미 보충용 structured output schema를 만든다.

    입력:
    - definitions: 공통 의미 필드 정의 목록

    반환:
    - Responses API용 json_schema dict
    """

    allowed_semantic_keys = [
        definition.semantic_key for definition in definitions
    ] + [UNRESOLVED_TEMPLATE_HEADER_SENTINEL]

    return {
        "name": "template_header_semantic_mapping",
        "type": "json_schema",
        "strict": True,
        "schema": {
            "type": "object",
            "additionalProperties": False,
            "required": ["items"],
            "properties": {
                "items": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": [
                            "sheet_name",
                            "column_index",
                            "header_text",
                            "semantic_key",
                            "confidence",
                            "rationale",
                        ],
                        "properties": {
                            "sheet_name": {"type": "string"},
                            "column_index": {"type": "integer"},
                            "header_text": {"type": "string"},
                            "semantic_key": {
                                "type": "string",
                                "enum": allowed_semantic_keys,
                            },
                            "confidence": {"type": "number"},
                            "rationale": {"type": "string"},
                        },
                    },
                }
            },
        },
    }


def _parse_llm_mapping_payload(envelope) -> dict[str, Any]:
    parsed_output = envelope.parsed_output
    if parsed_output is not None:
        if hasattr(parsed_output, "model_dump"):
            return parsed_output.model_dump()
        if hasattr(parsed_output, "to_dict"):
            return parsed_output.to_dict()
        return dict(parsed_output)

    return json.loads(envelope.output_text)
