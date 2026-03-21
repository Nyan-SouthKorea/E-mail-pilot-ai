"""사용자 프로필 기준의 로컬 경로 규칙을 모은다."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


def workspace_root() -> Path:
    """기능: 현재 워크스페이스 루트 경로를 반환한다.

    입력:
    - 없음

    반환:
    - `repo/`의 상위 workspace 경로
    """

    return Path(__file__).resolve().parents[1]


def default_example_profile_root(profile_name: str = "김정민") -> Path:
    """기능: 현재 예시 사용자 프로필 루트 기본 경로를 반환한다.

    입력:
    - profile_name: 예시 프로필 이름

    반환:
    - `secrets/사용자 설정/<이름>` 경로
    """

    return workspace_root() / "secrets" / "사용자 설정" / profile_name


@dataclass(slots=True)
class ProfilePaths:
    """기능: 사용자 프로필 폴더 아래의 표준 reference/runtime 경로를 제공한다.

    입력:
    - profile_root: `secrets/사용자 설정/<이름>` 루트 경로

    반환:
    - 경로 helper 인스턴스
    """

    profile_root: str

    def root(self) -> Path:
        """기능: 프로필 루트 경로를 `Path`로 반환한다.

        입력:
        - 없음

        반환:
        - 프로필 루트 `Path`
        """

        return Path(self.profile_root)

    def reference_root(self) -> Path:
        """기능: read-only reference 루트 경로를 반환한다.

        입력:
        - 없음

        반환:
        - `참고자료` 경로
        """

        return self.root() / "참고자료"

    def fixture_examples_root(self) -> Path:
        """기능: 예시 수신 이메일 fixture 루트 경로를 반환한다.

        입력:
        - 없음

        반환:
        - `참고자료/수신 이메일 예시` 경로
        """

        return self.reference_root() / "수신 이메일 예시"

    def reference_exports_root(self) -> Path:
        """기능: 기대 산출물 reference 루트 경로를 반환한다.

        입력:
        - 없음

        반환:
        - `참고자료/기대되는 산출물` 경로
        """

        return self.reference_root() / "기대되는 산출물"

    def template_workbook_path(
        self,
        filename: str = "기업 신청서 모음.xlsx",
    ) -> Path:
        """기능: 현재 프로필의 기본 reference workbook 경로를 반환한다.

        입력:
        - filename: 템플릿 workbook 파일명

        반환:
        - reference workbook 경로
        """

        return self.reference_exports_root() / filename

    def runtime_root(self) -> Path:
        """기능: 실제 런타임 산출물 루트 경로를 반환한다.

        입력:
        - 없음

        반환:
        - `실행결과` 경로
        """

        return self.root() / "실행결과"

    def runtime_mail_bundles_root(self) -> Path:
        """기능: 메일 번들 저장 루트 경로를 반환한다.

        입력:
        - 없음

        반환:
        - `실행결과/받은 메일` 경로
        """

        return self.runtime_root() / "받은 메일"

    def runtime_exports_root(self) -> Path:
        """기능: 엑셀 산출물 저장 루트 경로를 반환한다.

        입력:
        - 없음

        반환:
        - `실행결과/엑셀 산출물` 경로
        """

        return self.runtime_root() / "엑셀 산출물"

    def runtime_logs_root(self) -> Path:
        """기능: 로그 저장 루트 경로를 반환한다.

        입력:
        - 없음

        반환:
        - `실행결과/로그` 경로
        """

        return self.runtime_root() / "로그"

    def runtime_analysis_logs_root(self) -> Path:
        """기능: 분석 smoke 결과 로그 경로를 반환한다.

        입력:
        - 없음

        반환:
        - `실행결과/로그/analysis_smoke` 경로
        """

        return self.runtime_logs_root() / "analysis_smoke"

    def runtime_exports_logs_root(self) -> Path:
        """기능: export 관련 로그 경로를 반환한다.

        입력:
        - 없음

        반환:
        - `실행결과/로그/exports` 경로
        """

        return self.runtime_logs_root() / "exports"

    def runtime_llm_logs_root(self) -> Path:
        """기능: LLM 사용 로그 경로를 반환한다.

        입력:
        - 없음

        반환:
        - `실행결과/로그/llm` 경로
        """

        return self.runtime_logs_root() / "llm"

    def runtime_mailbox_logs_root(self) -> Path:
        """기능: mailbox 관련 로그 경로를 반환한다.

        입력:
        - 없음

        반환:
        - `실행결과/로그/mailbox` 경로
        """

        return self.runtime_logs_root() / "mailbox"

    def llm_usage_log_path(self) -> Path:
        """기능: 현재 프로필의 기본 LLM usage log 파일 경로를 반환한다.

        입력:
        - 없음

        반환:
        - `실행결과/로그/llm/openai_usage.jsonl` 경로
        """

        return self.runtime_llm_logs_root() / "openai_usage.jsonl"

    def ensure_runtime_dirs(self) -> list[Path]:
        """기능: 프로필 기준 기본 runtime 디렉토리들을 생성한다.

        입력:
        - 없음

        반환:
        - 생성 또는 확인한 디렉토리 목록
        """

        directories = [
            self.runtime_root(),
            self.runtime_mail_bundles_root(),
            self.runtime_exports_root(),
            self.runtime_logs_root(),
            self.runtime_analysis_logs_root(),
            self.runtime_exports_logs_root(),
            self.runtime_llm_logs_root(),
            self.runtime_mailbox_logs_root(),
        ]
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
        return directories
