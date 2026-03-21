"""Analysis 계층에서 공통으로 사용하는 데이터 계약."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

EXTRACTED_RECORD_SCHEMA_VERSION = "analysis.extracted_record.v1"


@dataclass(slots=True)
class EvidenceRef:
    """기능: 추출 근거의 위치와 종류를 표현한다.

    입력:
    - evidence_id: 근거 식별자
    - kind: `body_text`, `attachment_table`, `ocr`, `vision` 같은 종류
    - source: 근거가 나온 계층 또는 자산 종류
    - body_part_id: 본문 파트 식별자
    - artifact_id: 첨부 또는 파생 자산 식별자
    - page_number: 문서 페이지
    - locator: 셀 좌표, bbox, 문단 경로 같은 위치 설명
    - snippet: 근거 요약 문자열
    - confidence: 근거 자체의 신뢰도

    반환:
    - dataclass 인스턴스
    """

    evidence_id: str
    kind: str
    source: str
    body_part_id: str | None = None
    artifact_id: str | None = None
    page_number: int | None = None
    locator: str | None = None
    snippet: str | None = None
    confidence: float | None = None


@dataclass(slots=True)
class ExtractedField:
    """기능: 필드 값과 그 근거를 표현한다.

    입력:
    - field_name: 내부 필드명
    - value: 추출된 원값
    - normalized_value: 후처리된 표준값
    - confidence: 필드 수준 신뢰도
    - evidence_ids: 연결된 근거 id 목록
    - notes: 후처리 메모

    반환:
    - dataclass 인스턴스
    """

    field_name: str
    value: str
    normalized_value: str | None = None
    confidence: float | None = None
    evidence_ids: list[str] = field(default_factory=list)
    notes: str | None = None


@dataclass(slots=True)
class ExtractedRecord:
    """기능: 메일 1건에서 나온 구조화 분석 결과를 표현한다.

    입력:
    - 식별 키, 분류/요약 결과, 필드 목록, 근거 목록, 후속 action 힌트

    반환:
    - dataclass 인스턴스
    """

    bundle_id: str
    message_key: str
    record_type: str
    category: str
    fields: list[ExtractedField] = field(default_factory=list)
    evidence: list[EvidenceRef] = field(default_factory=list)
    summary_one_line: str = ""
    summary_short: str = ""
    overall_confidence: float | None = None
    action_hints: list[str] = field(default_factory=list)
    unresolved_questions: list[str] = field(default_factory=list)
    source_artifact_ids: list[str] = field(default_factory=list)
    schema_version: str = EXTRACTED_RECORD_SCHEMA_VERSION

    def field_map(self) -> dict[str, ExtractedField]:
        """기능: 필드명을 key로 한 빠른 조회 dict를 만든다.

        입력:
        - 없음

        반환:
        - `field_name -> ExtractedField` dict
        """

        return {field.field_name: field for field in self.fields}

    def to_dict(self) -> dict[str, object]:
        """기능: 분석 결과를 JSON 직렬화용 dict로 바꾼다.

        입력:
        - 없음

        반환:
        - 중첩 dataclass가 풀린 dict
        """

        return asdict(self)
