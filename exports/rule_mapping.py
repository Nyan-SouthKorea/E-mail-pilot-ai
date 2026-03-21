"""템플릿 헤더에 rule 기반으로 의미 키를 붙이는 mapper."""

from __future__ import annotations

from dataclasses import dataclass

from .schema import TemplateProfile
from .semantic_mapping import (
    SemanticFieldDefinition,
    TemplateColumnSemanticMapping,
    TemplateSemanticMapping,
    apply_template_semantic_mapping,
    default_semantic_field_definitions,
)


@dataclass(slots=True)
class RuleSemanticMatch:
    """기능: rule 기반 의미 매칭 결과를 표현한다.

    입력:
    - semantic_key: 매칭된 의미 키
    - confidence: 신뢰도
    - rationale: 매칭 근거 설명

    반환:
    - dataclass 인스턴스
    """

    semantic_key: str
    confidence: float
    rationale: str


def build_rule_based_template_mapping(
    profile: TemplateProfile,
    definitions: list[SemanticFieldDefinition] | None = None,
) -> TemplateSemanticMapping:
    """기능: 템플릿 헤더를 보고 rule 기반 의미 매핑 결과를 만든다.

    입력:
    - profile: 템플릿 프로필
    - definitions: 공통 의미 필드 정의 목록

    반환:
    - `TemplateSemanticMapping`
    """

    definitions = definitions or default_semantic_field_definitions()
    mappings: list[TemplateColumnSemanticMapping] = []
    unresolved_headers: list[str] = []

    for sheet in profile.sheets:
        for column in sheet.columns:
            match = _match_header_to_semantic_key(
                header_text=column.header_text,
                definitions=definitions,
            )
            if match is None:
                unresolved_headers.append(f"{sheet.sheet_name}:{column.header_text}")
                continue

            mappings.append(
                TemplateColumnSemanticMapping(
                    sheet_name=sheet.sheet_name,
                    column_index=column.column_index,
                    header_text=column.header_text,
                    semantic_key=match.semantic_key,
                    confidence=match.confidence,
                    matched_by="rule",
                    rationale=match.rationale,
                )
            )

    notes: list[str] = []
    if unresolved_headers:
        notes.append("일부 헤더는 rule 기반으로 의미 키를 확정하지 못했다.")

    return TemplateSemanticMapping(
        profile_id=profile.profile_id,
        template_id=profile.template_id,
        mappings=mappings,
        unresolved_headers=unresolved_headers,
        notes=notes,
    )


def apply_rule_based_template_mapping(
    profile: TemplateProfile,
    definitions: list[SemanticFieldDefinition] | None = None,
) -> tuple[TemplateProfile, TemplateSemanticMapping]:
    """기능: rule 기반 매핑을 만들고 `TemplateProfile`에 반영한다.

    입력:
    - profile: 의미 키가 비어 있는 템플릿 프로필
    - definitions: 공통 의미 필드 정의 목록

    반환:
    - `(semantic_key 반영된 profile, mapping 결과)`
    """

    mapping = build_rule_based_template_mapping(profile, definitions=definitions)
    mapped_profile = apply_template_semantic_mapping(profile, mapping)
    return mapped_profile, mapping


def _match_header_to_semantic_key(
    header_text: str,
    definitions: list[SemanticFieldDefinition],
) -> RuleSemanticMatch | None:
    normalized_header = _normalize_text(header_text)

    exact_match: RuleSemanticMatch | None = None
    partial_match: RuleSemanticMatch | None = None

    for definition in definitions:
        candidates = [
            definition.semantic_key,
            definition.display_name,
            *definition.example_headers,
        ]
        for candidate in candidates:
            normalized_candidate = _normalize_text(candidate)
            if not normalized_candidate:
                continue

            if normalized_header == normalized_candidate:
                exact_match = RuleSemanticMatch(
                    semantic_key=definition.semantic_key,
                    confidence=0.99,
                    rationale=f"header `{header_text}`가 `{candidate}`와 exact match",
                )
                break

            if (
                normalized_candidate in normalized_header
                or normalized_header in normalized_candidate
            ) and partial_match is None:
                partial_match = RuleSemanticMatch(
                    semantic_key=definition.semantic_key,
                    confidence=0.85,
                    rationale=f"header `{header_text}`가 `{candidate}`와 부분 일치",
                )
        if exact_match is not None:
            return exact_match

    return partial_match


def _normalize_text(text: str) -> str:
    return "".join(character for character in str(text).casefold() if character.isalnum())
