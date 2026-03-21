"""Exports 계층에서 템플릿 열 의미 해석에 사용하는 계약."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, replace

from .schema import TemplateColumn, TemplateProfile, TemplateSheet

TEMPLATE_SEMANTIC_MAPPING_SCHEMA_VERSION = "exports.template_semantic_mapping.v1"


@dataclass(slots=True)
class SemanticFieldDefinition:
    """기능: 프로필과 무관한 공통 의미 필드 정의를 표현한다.

    입력:
    - semantic_key: 내부 공통 의미 키
    - display_name: 사용자 친화적인 필드 이름
    - description: 필드 의미 설명
    - field_role: `extract`, `generate`, `meta`, `system`, `human_only` 중 하나
    - example_headers: 템플릿에서 자주 보이는 헤더 예시
    - preferred_sources: 추출 우선 source 힌트
    - required_for_v1: v1에서 특히 중요한 필드 여부
    - notes: 추가 메모

    반환:
    - dataclass 인스턴스
    """

    semantic_key: str
    display_name: str
    description: str
    field_role: str
    example_headers: list[str] = field(default_factory=list)
    preferred_sources: list[str] = field(default_factory=list)
    required_for_v1: bool = False
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        """기능: 필드 정의를 JSON 직렬화용 dict로 바꾼다.

        입력:
        - 없음

        반환:
        - 중첩 dataclass가 풀린 dict
        """

        return asdict(self)


@dataclass(slots=True)
class TemplateColumnSemanticMapping:
    """기능: 템플릿 열 1개에 대한 의미 해석 결과를 표현한다.

    입력:
    - sheet_name: 대상 시트명
    - column_index: 1-based 열 번호
    - header_text: 원본 헤더 텍스트
    - semantic_key: 연결된 공통 의미 키
    - confidence: 매핑 신뢰도
    - matched_by: `llm`, `rule`, `manual` 같은 매핑 주체
    - rationale: 매핑 근거 설명
    - notes: 추가 메모

    반환:
    - dataclass 인스턴스
    """

    sheet_name: str
    column_index: int
    header_text: str
    semantic_key: str
    confidence: float | None = None
    matched_by: str = "llm"
    rationale: str = ""
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        """기능: 열 매핑 결과를 JSON 직렬화용 dict로 바꾼다.

        입력:
        - 없음

        반환:
        - 중첩 dataclass가 풀린 dict
        """

        return asdict(self)


@dataclass(slots=True)
class TemplateSemanticMapping:
    """기능: 템플릿 전체의 의미 매핑 결과를 표현한다.

    입력:
    - profile_id: 사용자 프로필 식별자
    - template_id: 템플릿 식별자
    - mappings: 열별 의미 매핑 목록
    - unresolved_headers: 아직 의미 키를 붙이지 못한 헤더 목록
    - notes: 추가 메모

    반환:
    - dataclass 인스턴스
    """

    profile_id: str
    template_id: str
    mappings: list[TemplateColumnSemanticMapping] = field(default_factory=list)
    unresolved_headers: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    schema_version: str = TEMPLATE_SEMANTIC_MAPPING_SCHEMA_VERSION

    def mapping_for(
        self,
        sheet_name: str,
        column_index: int,
    ) -> TemplateColumnSemanticMapping | None:
        """기능: 시트명과 열 번호로 매핑 결과를 찾는다.

        입력:
        - sheet_name: 시트명
        - column_index: 1-based 열 번호

        반환:
        - 일치하는 매핑 또는 `None`
        """

        for mapping in self.mappings:
            if mapping.sheet_name == sheet_name and mapping.column_index == column_index:
                return mapping
        return None

    def to_dict(self) -> dict[str, object]:
        """기능: 템플릿 매핑 결과를 JSON 직렬화용 dict로 바꾼다.

        입력:
        - 없음

        반환:
        - 중첩 dataclass가 풀린 dict
        """

        return asdict(self)


def default_semantic_field_definitions() -> list[SemanticFieldDefinition]:
    """기능: v1 기준 공통 의미 필드 정의 목록을 반환한다.

    입력:
    - 없음

    반환:
    - `SemanticFieldDefinition` 목록
    """

    return [
        SemanticFieldDefinition(
            semantic_key="row_number",
            display_name="번호",
            description="워크북 append 시 자동으로 채우는 순번",
            field_role="system",
            example_headers=["번호", "순번", "No", "No."],
            preferred_sources=[],
        ),
        SemanticFieldDefinition(
            semantic_key="company_name",
            display_name="기업명",
            description="신청 기업 또는 조직의 공식 이름",
            field_role="extract",
            example_headers=["기업명", "회사명", "업체명"],
            preferred_sources=["attachment_table", "body_text"],
            required_for_v1=True,
        ),
        SemanticFieldDefinition(
            semantic_key="contact_name",
            display_name="담당자명",
            description="신청을 보낸 담당자 또는 대표 연락 담당자 이름",
            field_role="extract",
            example_headers=["담당자명", "담당자", "성함"],
            preferred_sources=["body_text", "attachment_table", "signature"],
            required_for_v1=True,
        ),
        SemanticFieldDefinition(
            semantic_key="phone_number",
            display_name="연락처",
            description="전화번호 또는 휴대전화 번호",
            field_role="extract",
            example_headers=["연락처", "전화번호", "휴대폰"],
            preferred_sources=["body_text", "attachment_table", "signature"],
            required_for_v1=True,
        ),
        SemanticFieldDefinition(
            semantic_key="email_address",
            display_name="이메일",
            description="대표 연락 이메일 주소",
            field_role="extract",
            example_headers=["이메일", "메일", "E-mail", "Email"],
            preferred_sources=["message_header", "body_text", "attachment_table"],
            required_for_v1=True,
        ),
        SemanticFieldDefinition(
            semantic_key="website_or_social",
            display_name="홈페이지/SNS",
            description="회사 홈페이지, 쇼핑몰, SNS 주소",
            field_role="extract",
            example_headers=["홈페이지/SNS", "홈페이지", "웹사이트", "SNS"],
            preferred_sources=["attachment_table", "body_text"],
        ),
        SemanticFieldDefinition(
            semantic_key="industry",
            display_name="관련산업군",
            description="기업이 속한 산업군 또는 업종",
            field_role="extract",
            example_headers=["관련산업군", "산업군", "업종"],
            preferred_sources=["attachment_table", "ocr", "vision"],
            required_for_v1=True,
        ),
        SemanticFieldDefinition(
            semantic_key="product_or_service",
            display_name="주요 제품/서비스",
            description="제공하는 주요 제품이나 서비스 설명",
            field_role="extract",
            example_headers=["주요 제품/서비스", "제품/서비스", "주력제품"],
            preferred_sources=["attachment_table", "body_text", "ocr"],
            required_for_v1=True,
        ),
        SemanticFieldDefinition(
            semantic_key="target_region",
            display_name="진출대상지역",
            description="희망 시장 또는 대상 지역",
            field_role="extract",
            example_headers=["진출대상지역", "희망지역", "대상지역"],
            preferred_sources=["attachment_table", "body_text"],
        ),
        SemanticFieldDefinition(
            semantic_key="application_purpose",
            display_name="신청목적",
            description="왜 이 신청을 했는지에 대한 목적 요약",
            field_role="generate",
            example_headers=["신청목적", "지원목적", "문의목적"],
            preferred_sources=["attachment_table", "body_text", "vision"],
            required_for_v1=True,
        ),
        SemanticFieldDefinition(
            semantic_key="company_intro_one_line",
            display_name="기업소개(한줄)",
            description="중복 표현을 줄인 한줄 기업 소개",
            field_role="generate",
            example_headers=["기업소개", "회사소개", "한줄소개"],
            preferred_sources=["attachment_table", "pdf", "body_text"],
        ),
        SemanticFieldDefinition(
            semantic_key="business_summary",
            display_name="사업내용 요약",
            description="기업이 진행하는 사업 내용을 짧게 요약한 필드",
            field_role="generate",
            example_headers=["사업내용", "사업내용 요약", "사업개요"],
            preferred_sources=["attachment_table", "pdf", "body_text", "vision"],
            required_for_v1=True,
        ),
        SemanticFieldDefinition(
            semantic_key="request_summary",
            display_name="요청사항 요약",
            description="상세 요청사항을 보고용 문장으로 정리한 필드",
            field_role="generate",
            example_headers=["요청사항", "요청사항 요약", "상세 요청사항", "상세 요청 사항"],
            preferred_sources=["attachment_table", "body_text", "vision"],
            required_for_v1=True,
        ),
        SemanticFieldDefinition(
            semantic_key="received_at",
            display_name="접수일",
            description="이메일을 수신한 시각 또는 업무 접수 일시",
            field_role="meta",
            example_headers=["접수일", "수신일시", "등록일"],
            preferred_sources=["message_header"],
        ),
        SemanticFieldDefinition(
            semantic_key="source_message_subject",
            display_name="이메일 제목",
            description="원본 이메일 제목",
            field_role="meta",
            example_headers=["이메일 제목", "메일 제목", "제목"],
            preferred_sources=["message_header"],
        ),
        SemanticFieldDefinition(
            semantic_key="internal_status",
            display_name="진행상태",
            description="내부 검토 상태나 선정 여부 같은 사람 관리 필드",
            field_role="human_only",
            example_headers=["진행상태", "선정여부", "처리상태"],
            preferred_sources=[],
        ),
        SemanticFieldDefinition(
            semantic_key="internal_notes",
            display_name="비고",
            description="내부 메모나 운영 비고",
            field_role="human_only",
            example_headers=["비고", "메모", "내부메모"],
            preferred_sources=[],
        ),
    ]


def semantic_field_definition_map() -> dict[str, SemanticFieldDefinition]:
    """기능: 의미 키를 기준으로 필드 정의를 조회하는 dict를 만든다.

    입력:
    - 없음

    반환:
    - `semantic_key -> SemanticFieldDefinition` dict
    """

    return {
        definition.semantic_key: definition
        for definition in default_semantic_field_definitions()
    }


def apply_template_semantic_mapping(
    profile: TemplateProfile,
    mapping: TemplateSemanticMapping,
) -> TemplateProfile:
    """기능: 템플릿 의미 매핑 결과를 `TemplateProfile`에 반영한다.

    입력:
    - profile: 의미 키가 비어 있는 템플릿 프로필
    - mapping: 열 의미 해석 결과

    반환:
    - `semantic_key`, `semantic_confidence`가 반영된 새 `TemplateProfile`
    """

    sheets: list[TemplateSheet] = []
    for sheet in profile.sheets:
        mapped_columns: list[TemplateColumn] = []
        for column in sheet.columns:
            matched_mapping = mapping.mapping_for(
                sheet_name=sheet.sheet_name,
                column_index=column.column_index,
            )
            if matched_mapping is None:
                mapped_columns.append(column)
                continue

            mapped_columns.append(
                replace(
                    column,
                    semantic_key=matched_mapping.semantic_key,
                    semantic_confidence=matched_mapping.confidence,
                )
            )

        sheets.append(replace(sheet, columns=mapped_columns))

    return replace(profile, sheets=sheets)


def merge_template_semantic_mappings(
    *mappings: TemplateSemanticMapping,
) -> TemplateSemanticMapping:
    """기능: 여러 템플릿 의미 매핑 결과를 우선순위대로 합친다.

    입력:
    - mappings: 앞에 오는 결과가 우선인 매핑 목록

    반환:
    - 중복 열은 앞선 결과를 유지한 `TemplateSemanticMapping`
    """

    if not mappings:
        raise ValueError("최소 1개의 TemplateSemanticMapping이 필요합니다.")

    merged_mappings: list[TemplateColumnSemanticMapping] = []
    seen_keys: set[tuple[str, int]] = set()
    notes: list[str] = []

    for mapping in mappings:
        for item in mapping.mappings:
            key = (item.sheet_name, item.column_index)
            if key in seen_keys:
                continue
            merged_mappings.append(item)
            seen_keys.add(key)

        for note in mapping.notes:
            if note not in notes:
                notes.append(note)

    resolved_headers = {
        f"{item.sheet_name}:{item.header_text}"
        for item in merged_mappings
    }
    unresolved_headers: list[str] = []
    for mapping in mappings:
        for header_ref in mapping.unresolved_headers:
            if header_ref in resolved_headers:
                continue
            if header_ref in unresolved_headers:
                continue
            unresolved_headers.append(header_ref)

    first_mapping = mappings[0]
    return TemplateSemanticMapping(
        profile_id=first_mapping.profile_id,
        template_id=first_mapping.template_id,
        mappings=merged_mappings,
        unresolved_headers=unresolved_headers,
        notes=notes,
    )
