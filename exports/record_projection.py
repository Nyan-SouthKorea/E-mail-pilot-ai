"""Analysis 결과를 템플릿 열 값으로 투영하는 계약."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

from analysis.schema import ExtractedField, ExtractedRecord

from .schema import TemplateProfile, TemplateSheet
from .semantic_mapping import (
    SemanticFieldDefinition,
    default_semantic_field_definitions,
)

RECORD_TEMPLATE_PROJECTION_SCHEMA_VERSION = "exports.record_template_projection.v1"


@dataclass(slots=True)
class ResolvedSemanticValue:
    """기능: `ExtractedRecord`에서 공통 의미 키 1개에 대응하는 값을 표현한다.

    입력:
    - semantic_key: 공통 의미 키
    - value: 실제 사용할 값
    - source_field_name: 값을 가져온 `ExtractedField.field_name`
    - source_kind: `field`, `record_summary` 같은 값의 출처
    - normalized_value: 표준화된 값
    - confidence: 값 신뢰도
    - evidence_ids: 연결된 근거 id 목록
    - notes: 추가 메모

    반환:
    - dataclass 인스턴스
    """

    semantic_key: str
    value: str
    source_field_name: str
    source_kind: str = "field"
    normalized_value: str | None = None
    confidence: float | None = None
    evidence_ids: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def preferred_value(self) -> str:
        """기능: 실제 투영에 우선 사용할 문자열을 반환한다.

        입력:
        - 없음

        반환:
        - `normalized_value` 우선, 없으면 원 `value`
        """

        return self.normalized_value or self.value

    def to_dict(self) -> dict[str, object]:
        """기능: 직렬화용 dict로 바꾼다.

        입력:
        - 없음

        반환:
        - 중첩 dataclass가 풀린 dict
        """

        return asdict(self)


@dataclass(slots=True)
class ResolvedRecordProjection:
    """기능: `ExtractedRecord`를 공통 의미 키 기준으로 해석한 결과를 표현한다.

    입력:
    - record_key: 원본 record 식별 키
    - resolved_values: 해석된 값 목록
    - unresolved_required_keys: 못 채운 필수 의미 키 목록
    - unresolved_optional_keys: 못 채운 선택 의미 키 목록
    - notes: 추가 메모

    반환:
    - dataclass 인스턴스
    """

    record_key: str
    resolved_values: list[ResolvedSemanticValue] = field(default_factory=list)
    unresolved_required_keys: list[str] = field(default_factory=list)
    unresolved_optional_keys: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def value_for(self, semantic_key: str) -> ResolvedSemanticValue | None:
        """기능: 의미 키 하나에 대응하는 값을 찾는다.

        입력:
        - semantic_key: 공통 의미 키

        반환:
        - 일치하는 `ResolvedSemanticValue` 또는 `None`
        """

        for value in self.resolved_values:
            if value.semantic_key == semantic_key:
                return value
        return None

    def to_dict(self) -> dict[str, object]:
        """기능: 직렬화용 dict로 바꾼다.

        입력:
        - 없음

        반환:
        - 중첩 dataclass가 풀린 dict
        """

        return asdict(self)


@dataclass(slots=True)
class ProjectedTemplateValue:
    """기능: 템플릿 열 1개에 실제로 써 넣을 값을 표현한다.

    입력:
    - sheet_name: 대상 시트명
    - column_index: 1-based 열 번호
    - column_letter: Excel 열 문자
    - header_text: 템플릿 헤더 텍스트
    - semantic_key: 연결된 공통 의미 키
    - value: 기록할 문자열 값
    - source_field_name: 값을 가져온 분석 필드명
    - source_kind: 값 출처 종류
    - confidence: 값 신뢰도
    - evidence_ids: 연결된 근거 id 목록
    - notes: 추가 메모

    반환:
    - dataclass 인스턴스
    """

    sheet_name: str
    column_index: int
    column_letter: str
    header_text: str
    semantic_key: str
    value: str
    source_field_name: str
    source_kind: str
    confidence: float | None = None
    evidence_ids: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        """기능: 직렬화용 dict로 바꾼다.

        입력:
        - 없음

        반환:
        - 중첩 dataclass가 풀린 dict
        """

        return asdict(self)


@dataclass(slots=True)
class ProjectedTemplateRow:
    """기능: 분석 결과를 템플릿 시트 한 줄에 투영한 결과를 표현한다.

    입력:
    - profile_id: 사용자 프로필 식별자
    - template_id: 템플릿 식별자
    - sheet_name: 대상 시트명
    - record_key: 원본 record 식별 키
    - values: 실제로 채울 열 값 목록
    - unresolved_columns: 아직 채우지 못한 템플릿 열 목록
    - skipped_columns: 사람 관리 전용 등으로 건너뛴 열 목록
    - notes: 추가 메모

    반환:
    - dataclass 인스턴스
    """

    profile_id: str
    template_id: str
    sheet_name: str
    record_key: str
    values: list[ProjectedTemplateValue] = field(default_factory=list)
    unresolved_columns: list[str] = field(default_factory=list)
    skipped_columns: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    schema_version: str = RECORD_TEMPLATE_PROJECTION_SCHEMA_VERSION

    def value_by_semantic_key(self, semantic_key: str) -> ProjectedTemplateValue | None:
        """기능: 의미 키 하나에 대응하는 투영 결과를 찾는다.

        입력:
        - semantic_key: 공통 의미 키

        반환:
        - 일치하는 `ProjectedTemplateValue` 또는 `None`
        """

        for value in self.values:
            if value.semantic_key == semantic_key:
                return value
        return None

    def to_dict(self) -> dict[str, object]:
        """기능: 직렬화용 dict로 바꾼다.

        입력:
        - 없음

        반환:
        - 중첩 dataclass가 풀린 dict
        """

        return asdict(self)


def default_extracted_record_aliases() -> dict[str, list[str]]:
    """기능: 공통 의미 키별 기본 분석 필드 alias 목록을 반환한다.

    입력:
    - 없음

    반환:
    - `semantic_key -> alias 목록`
    """

    alias_map = {
        definition.semantic_key: [
            definition.semantic_key,
            definition.display_name,
            *definition.example_headers,
        ]
        for definition in default_semantic_field_definitions()
    }

    alias_map["company_name"].extend(
        ["company", "company_title", "organization_name", "applicant_company"]
    )
    alias_map["contact_name"].extend(
        ["contact_person", "manager_name", "representative_name"]
    )
    alias_map["phone_number"].extend(
        ["phone", "mobile", "contact_phone", "representative_phone"]
    )
    alias_map["email_address"].extend(
        ["email", "contact_email", "sender_email", "representative_email"]
    )
    alias_map["website_or_social"].extend(
        ["website", "website_url", "homepage", "social_url", "sns_url"]
    )
    alias_map["industry"].extend(["industry_name", "industry_group", "business_sector"])
    alias_map["product_or_service"].extend(
        ["product", "service", "main_product", "main_service"]
    )
    alias_map["target_region"].extend(["target_market", "market_region", "target_area"])
    alias_map["application_purpose"].extend(
        ["purpose", "request_purpose", "application_reason"]
    )
    alias_map["company_intro_one_line"].extend(
        ["company_intro", "short_intro", "one_line_intro"]
    )
    alias_map["business_summary"].extend(
        ["business_overview", "business_description", "service_summary"]
    )
    alias_map["request_summary"].extend(
        ["request_details", "detail_request", "detailed_request", "상세요청사항"]
    )
    alias_map["received_at"].extend(["received_date", "message_received_at", "receipt_date"])
    alias_map["source_message_subject"].extend(
        ["message_subject", "email_subject", "subject"]
    )
    alias_map["internal_status"].extend(["status", "process_status"])
    alias_map["internal_notes"].extend(["notes", "memo", "internal_memo"])

    return alias_map


def resolve_record_semantic_values(
    record: ExtractedRecord,
    definitions: list[SemanticFieldDefinition] | None = None,
    alias_map: dict[str, list[str]] | None = None,
    include_human_only: bool = False,
) -> ResolvedRecordProjection:
    """기능: `ExtractedRecord`를 공통 의미 키 기준 값 목록으로 해석한다.

    입력:
    - record: 분석 결과
    - definitions: 공통 의미 필드 정의 목록
    - alias_map: 필드 alias 규칙
    - include_human_only: 사람 관리 전용 필드도 unresolved 대상으로 포함할지 여부

    반환:
    - `ResolvedRecordProjection`
    """

    definitions = definitions or default_semantic_field_definitions()
    alias_map = alias_map or default_extracted_record_aliases()
    lookup = _field_lookup(record.fields)

    resolved_values: list[ResolvedSemanticValue] = []
    unresolved_required_keys: list[str] = []
    unresolved_optional_keys: list[str] = []

    for definition in definitions:
        if definition.field_role == "human_only" and not include_human_only:
            continue

        field = _find_field_by_alias(
            lookup=lookup,
            aliases=alias_map.get(definition.semantic_key, []),
        )
        if field is not None:
            resolved_values.append(
                ResolvedSemanticValue(
                    semantic_key=definition.semantic_key,
                    value=field.value,
                    normalized_value=field.normalized_value,
                    source_field_name=field.field_name,
                    source_kind="field",
                    confidence=field.confidence,
                    evidence_ids=list(field.evidence_ids),
                )
            )
            continue

        fallback_value = _fallback_semantic_value(record, definition.semantic_key)
        if fallback_value is not None:
            resolved_values.append(fallback_value)
            continue

        if definition.required_for_v1:
            unresolved_required_keys.append(definition.semantic_key)
        else:
            unresolved_optional_keys.append(definition.semantic_key)

    notes: list[str] = []
    if unresolved_required_keys:
        notes.append("v1 필수 의미 키 일부가 아직 채워지지 않았다.")

    return ResolvedRecordProjection(
        record_key=record.message_key,
        resolved_values=resolved_values,
        unresolved_required_keys=unresolved_required_keys,
        unresolved_optional_keys=unresolved_optional_keys,
        notes=notes,
    )


def project_record_to_template(
    profile: TemplateProfile,
    record: ExtractedRecord,
    definitions: list[SemanticFieldDefinition] | None = None,
    alias_map: dict[str, list[str]] | None = None,
    include_human_only: bool = False,
    sheet_name: str | None = None,
) -> ProjectedTemplateRow:
    """기능: 분석 결과를 템플릿 시트 한 줄의 열 값들로 투영한다.

    입력:
    - profile: 의미 키가 반영된 템플릿 프로필
    - record: 분석 결과
    - definitions: 공통 의미 필드 정의 목록
    - alias_map: 분석 필드 alias 규칙
    - include_human_only: 사람 관리 전용 열도 AI가 채우도록 허용할지 여부
    - sheet_name: 특정 시트만 대상으로 삼고 싶을 때의 시트명

    반환:
    - `ProjectedTemplateRow`
    """

    definitions = definitions or default_semantic_field_definitions()
    definition_map = {
        definition.semantic_key: definition for definition in definitions
    }
    resolved_record = resolve_record_semantic_values(
        record=record,
        definitions=definitions,
        alias_map=alias_map,
        include_human_only=include_human_only,
    )

    sheet = _select_sheet(profile, sheet_name=sheet_name)
    if sheet is None:
        return ProjectedTemplateRow(
            profile_id=profile.profile_id,
            template_id=profile.template_id,
            sheet_name=sheet_name or "",
            record_key=record.message_key,
            notes=["대상 템플릿 시트를 찾지 못했다."],
        )

    values: list[ProjectedTemplateValue] = []
    unresolved_columns: list[str] = []
    skipped_columns: list[str] = []

    for column in sheet.columns:
        if not column.semantic_key:
            unresolved_columns.append(f"{column.header_text} | semantic_key 없음")
            continue

        definition = definition_map.get(column.semantic_key)
        if definition is not None and definition.field_role == "human_only" and not include_human_only:
            skipped_columns.append(f"{column.header_text} | human_only")
            continue

        resolved_value = resolved_record.value_for(column.semantic_key)
        if resolved_value is None:
            unresolved_columns.append(
                f"{column.header_text} | {column.semantic_key}"
            )
            continue

        values.append(
            ProjectedTemplateValue(
                sheet_name=sheet.sheet_name,
                column_index=column.column_index,
                column_letter=column.column_letter,
                header_text=column.header_text,
                semantic_key=column.semantic_key,
                value=resolved_value.preferred_value(),
                source_field_name=resolved_value.source_field_name,
                source_kind=resolved_value.source_kind,
                confidence=resolved_value.confidence,
                evidence_ids=list(resolved_value.evidence_ids),
                notes=list(resolved_value.notes),
            )
        )

    notes = list(resolved_record.notes)
    if skipped_columns:
        notes.append("human_only 열은 현재 자동 작성 대상에서 제외했다.")

    return ProjectedTemplateRow(
        profile_id=profile.profile_id,
        template_id=profile.template_id,
        sheet_name=sheet.sheet_name,
        record_key=record.message_key,
        values=values,
        unresolved_columns=unresolved_columns,
        skipped_columns=skipped_columns,
        notes=notes,
    )


def _field_lookup(fields: list[ExtractedField]) -> dict[str, ExtractedField]:
    lookup: dict[str, ExtractedField] = {}
    for field in fields:
        normalized = _normalize_key(field.field_name)
        if normalized and normalized not in lookup:
            lookup[normalized] = field
    return lookup


def _find_field_by_alias(
    lookup: dict[str, ExtractedField],
    aliases: list[str],
) -> ExtractedField | None:
    for alias in aliases:
        normalized = _normalize_key(alias)
        field = lookup.get(normalized)
        if field is not None:
            return field
    return None


def _normalize_key(text: str) -> str:
    return "".join(character for character in str(text).casefold() if character.isalnum())


def _fallback_semantic_value(
    record: ExtractedRecord,
    semantic_key: str,
) -> ResolvedSemanticValue | None:
    if semantic_key == "company_intro_one_line" and record.summary_one_line:
        return ResolvedSemanticValue(
            semantic_key=semantic_key,
            value=record.summary_one_line,
            source_field_name="summary_one_line",
            source_kind="record_summary",
            notes=["record.summary_one_line fallback 사용"],
        )

    if semantic_key == "business_summary" and record.summary_short:
        return ResolvedSemanticValue(
            semantic_key=semantic_key,
            value=record.summary_short,
            source_field_name="summary_short",
            source_kind="record_summary",
            notes=["record.summary_short fallback 사용"],
        )

    return None


def _select_sheet(profile: TemplateProfile, sheet_name: str | None) -> TemplateSheet | None:
    if sheet_name:
        for sheet in profile.sheets:
            if sheet.sheet_name == sheet_name:
                return sheet
        return None

    return profile.primary_sheet()
