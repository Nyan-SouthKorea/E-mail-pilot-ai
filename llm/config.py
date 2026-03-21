"""LLM 계층의 실행 설정을 정의한다."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path

from project_paths import ProfilePaths, default_example_profile_root


def workspace_root() -> Path:
    """기능: 워크스페이스 루트 경로를 반환한다.

    입력:
    - 없음

    반환:
    - `repo/`의 상위 workspace 경로
    """

    return Path(__file__).resolve().parents[2]


def default_results_root() -> Path:
    """기능: LLM 실행 로그의 기본 results 루트 경로를 반환한다.

    입력:
    - 없음

    반환:
    - `../results`
    """

    return workspace_root() / "results"


def default_llm_usage_log_path() -> Path:
    """기능: 기본 LLM 사용 로그 파일 경로를 반환한다.

    입력:
    - 없음

    반환:
    - `results/llm/openai_usage.jsonl` 경로
    """

    return default_results_root() / "llm" / "openai_usage.jsonl"


def default_profile_llm_usage_log_path(profile_root: str | None = None) -> Path:
    """기능: 프로필 기반 실행의 기본 LLM 사용 로그 파일 경로를 반환한다.

    입력:
    - profile_root: 사용자 프로필 루트 경로. 없으면 예시 프로필 기준

    반환:
    - `실행결과/로그/llm/openai_usage.jsonl` 경로
    """

    resolved_root = profile_root or str(default_example_profile_root())
    profile_paths = ProfilePaths(resolved_root)
    return profile_paths.llm_usage_log_path()


def default_openai_api_key_file() -> Path:
    """기능: 로컬 OpenAI API 키 파일 기본 경로를 반환한다.

    입력:
    - 없음

    반환:
    - `../secrets/chatgpt_api_key.txt`
    """

    return workspace_root() / "secrets" / "chatgpt_api_key.txt"


@dataclass(slots=True)
class OpenAIResponsesConfig:
    """기능: OpenAI Responses API 래퍼 설정을 표현한다.

    입력:
    - model: 기본 호출 모델명
    - api_key_env: API 키를 읽을 환경 변수 이름
    - usage_log_path: JSONL 사용 로그 경로
    - store: OpenAI 측 저장 여부
    - timeout_seconds: 네트워크 timeout
    - service_tier: 우선 처리 등 서비스 티어
    - include_request_preview: 로그에 요청 preview 일부를 남길지 여부
    - max_preview_chars: preview 최대 길이
    - pricing_snapshot_date: 가격표 스냅샷 날짜
    - pricing_source_url: 가격표 출처 URL
    - default_metadata: 기본 metadata

    반환:
    - dataclass 인스턴스
    """

    model: str = "gpt-5.4-mini"
    api_key_env: str = "OPENAI_API_KEY"
    api_key_file: str = field(default_factory=lambda: str(default_openai_api_key_file()))
    usage_log_path: str = field(default_factory=lambda: str(default_llm_usage_log_path()))
    store: bool = False
    timeout_seconds: float = 120.0
    service_tier: str = "auto"
    include_request_preview: bool = False
    max_preview_chars: int = 280
    pricing_snapshot_date: str = "2026-03-21"
    pricing_source_url: str = "https://openai.com/api/pricing/"
    default_metadata: dict[str, str] = field(default_factory=dict)

    def usage_log_file(self) -> Path:
        """기능: 사용 로그 파일 경로를 `Path`로 반환한다.

        입력:
        - 없음

        반환:
        - 사용 로그 `Path`
        """

        return Path(self.usage_log_path)

    def to_dict(self) -> dict[str, object]:
        """기능: 설정을 직렬화용 dict로 바꾼다.

        입력:
        - 없음

        반환:
        - dataclass가 풀린 dict
        """

        return asdict(self)
