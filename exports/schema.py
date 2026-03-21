"""Exports 계층에서 공통으로 사용하는 템플릿 계약."""

from dataclasses import asdict, dataclass, field

TEMPLATE_PROFILE_SCHEMA_VERSION = "exports.template_profile.v1"


@dataclass(slots=True)
class TemplateColumn:
    """기능: Excel 템플릿의 한 열 정보를 표현한다.

    입력:
    - 헤더 이름, 열 위치, 예시 값, 의미 해석 결과 같은 열 단위 정보

    반환:
    - dataclass 인스턴스
    """

    header_text: str
    column_index: int
    column_letter: str
    header_cell_ref: str
    semantic_key: str | None = None
    semantic_confidence: float | None = None
    example_value: str | None = None
    example_cell_ref: str | None = None
    required: bool = False
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        """기능: 열 정보를 JSON 직렬화용 dict로 바꾼다.

        입력:
        - 없음

        반환:
        - 중첩 dataclass가 풀린 dict
        """

        return asdict(self)


@dataclass(slots=True)
class TemplateSheet:
    """기능: Excel 템플릿의 시트 단위 규칙을 표현한다.

    입력:
    - 시트 이름, 헤더 행, 데이터 시작 행, 열 목록, append 규칙

    반환:
    - dataclass 인스턴스
    """

    sheet_name: str
    header_row_index: int
    data_start_row_index: int
    columns: list[TemplateColumn] = field(default_factory=list)
    append_mode: str = "append_after_last_row"
    frozen_panes: str | None = None
    notes: list[str] = field(default_factory=list)

    def column_by_header(self, header_text: str) -> TemplateColumn | None:
        """기능: 헤더 이름으로 열을 찾는다.

        입력:
        - header_text: 찾을 헤더 문자열

        반환:
        - 일치하는 `TemplateColumn` 또는 `None`
        """

        for column in self.columns:
            if column.header_text == header_text:
                return column
        return None

    def column_by_semantic_key(self, semantic_key: str) -> TemplateColumn | None:
        """기능: 의미 키로 열을 찾는다.

        입력:
        - semantic_key: 공통 의미 필드 키

        반환:
        - 일치하는 `TemplateColumn` 또는 `None`
        """

        for column in self.columns:
            if column.semantic_key == semantic_key:
                return column
        return None

    def to_dict(self) -> dict[str, object]:
        """기능: 시트 규칙을 JSON 직렬화용 dict로 바꾼다.

        입력:
        - 없음

        반환:
        - 중첩 dataclass가 풀린 dict
        """

        return asdict(self)


@dataclass(slots=True)
class TemplateProfile:
    """기능: 프로필별 Excel 템플릿 규칙 묶음을 표현한다.

    입력:
    - 프로필 식별자, 원본 워크북 경로, 시트 규칙 목록, 메모

    반환:
    - dataclass 인스턴스
    """

    profile_id: str
    source_workbook_path: str
    template_id: str = ""
    sheets: list[TemplateSheet] = field(default_factory=list)
    primary_sheet_name: str | None = None
    notes: list[str] = field(default_factory=list)
    schema_version: str = TEMPLATE_PROFILE_SCHEMA_VERSION

    def primary_sheet(self) -> TemplateSheet | None:
        """기능: 기본 시트 규칙을 반환한다.

        입력:
        - 없음

        반환:
        - 기본 `TemplateSheet` 또는 `None`
        """

        if self.primary_sheet_name:
            for sheet in self.sheets:
                if sheet.sheet_name == self.primary_sheet_name:
                    return sheet

        return self.sheets[0] if self.sheets else None

    def to_dict(self) -> dict[str, object]:
        """기능: 템플릿 프로필을 JSON 직렬화용 dict로 바꾼다.

        입력:
        - 없음

        반환:
        - 중첩 dataclass가 풀린 dict
        """

        return asdict(self)
