"""Analysis 계층에서 공통으로 사용하는 데이터 계약 helper."""

import copy

EXTRACTED_RECORD_SCHEMA_VERSION = "analysis.extracted_record.v1"


def make_evidence_ref(
    evidence_id,
    kind,
    source,
    body_part_id="",
    artifact_id="",
    page_number=None,
    locator="",
    snippet="",
    confidence=None,
):
    """기능: 추출 근거 위치 dict를 만든다.

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
    - 근거 dict
    """

    return {
        "evidence_id": evidence_id,
        "kind": kind,
        "source": source,
        "body_part_id": body_part_id,
        "artifact_id": artifact_id,
        "page_number": page_number,
        "locator": locator,
        "snippet": snippet,
        "confidence": confidence,
    }


def make_extracted_field(
    field_name,
    value,
    normalized_value="",
    confidence=None,
    evidence_ids=None,
    notes="",
):
    """기능: 필드 값과 근거 연결 dict를 만든다.

    입력:
    - field_name: 내부 필드명
    - value: 추출된 원값
    - normalized_value: 후처리된 표준값
    - confidence: 필드 수준 신뢰도
    - evidence_ids: 연결된 근거 id 목록
    - notes: 후처리 메모

    반환:
    - 필드 dict
    """

    if evidence_ids is None:
        evidence_ids = []

    return {
        "field_name": field_name,
        "value": value,
        "normalized_value": normalized_value,
        "confidence": confidence,
        "evidence_ids": list(evidence_ids),
        "notes": notes,
    }


def make_extracted_record(
    bundle_id,
    message_key,
    record_type,
    category,
    fields=None,
    evidence=None,
    summary_one_line="",
    summary_short="",
    overall_confidence=None,
    action_hints=None,
    unresolved_questions=None,
    source_artifact_ids=None,
    schema_version=EXTRACTED_RECORD_SCHEMA_VERSION,
):
    """기능: 메일 1건의 구조화 분석 결과 dict를 만든다.

    입력:
    - 식별 키, 분류/요약 결과, 필드 목록, 근거 목록, 후속 action 힌트

    반환:
    - 분석 결과 dict
    """

    if fields is None:
        fields = []
    if evidence is None:
        evidence = []
    if action_hints is None:
        action_hints = []
    if unresolved_questions is None:
        unresolved_questions = []
    if source_artifact_ids is None:
        source_artifact_ids = []

    return {
        "bundle_id": bundle_id,
        "message_key": message_key,
        "record_type": record_type,
        "category": category,
        "fields": copy.deepcopy(fields),
        "evidence": copy.deepcopy(evidence),
        "summary_one_line": summary_one_line,
        "summary_short": summary_short,
        "overall_confidence": overall_confidence,
        "action_hints": list(action_hints),
        "unresolved_questions": list(unresolved_questions),
        "source_artifact_ids": list(source_artifact_ids),
        "schema_version": schema_version,
    }


def build_field_map(record):
    """기능: 필드명을 key로 한 빠른 조회 dict를 만든다.

    입력:
    - record: 분석 결과 dict

    반환:
    - `field_name -> field dict` 조회용 dict
    """

    field_map = {}
    for field in record.get("fields", []):
        field_name = field.get("field_name", "")
        if field_name:
            field_map[field_name] = field
    return field_map


def copy_extracted_record(record):
    """기능: 분석 결과 dict의 깊은 복사본을 만든다.

    입력:
    - record: 분석 결과 dict

    반환:
    - 복사된 분석 결과 dict
    """

    return copy.deepcopy(record)
