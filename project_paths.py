"""사용자 데이터 경로 규칙을 모은다."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


def workspace_root() -> Path:
    return Path(__file__).resolve().parents[1]


def default_example_profile_root(profile_name: str = "김정민") -> Path:
    return workspace_root() / "secrets" / "사용자 설정" / profile_name


@dataclass(slots=True)
class ProfilePaths:
    """기능: legacy profile과 새 v2 save layout을 모두 읽는 경로 helper다."""

    profile_root: str

    def root(self) -> Path:
        return Path(self.profile_root)

    def layout_version(self) -> str:
        root = self.root()
        if (root / "workspace.epa-workspace.json").exists() or (root / "mail").exists():
            return "workspace_v2"
        return "legacy_profile"

    def reference_root(self) -> Path:
        if self.layout_version() == "workspace_v2":
            return self.root() / "exports" / "template"
        return self.root() / "참고자료"

    def fixture_examples_root(self) -> Path:
        if self.layout_version() == "workspace_v2":
            return self.root() / "mail" / "fixtures"
        return self.reference_root() / "수신 이메일 예시"

    def reference_exports_root(self) -> Path:
        if self.layout_version() == "workspace_v2":
            return self.root() / "exports" / "template"
        return self.reference_root() / "기대되는 산출물"

    def template_workbook_path(self, filename: str = "") -> Path:
        if self.layout_version() == "workspace_v2":
            return self.reference_exports_root() / (filename or "export_template.xlsx")
        return self.reference_exports_root() / (filename or "기업 신청서 모음.xlsx")

    def runtime_root(self) -> Path:
        if self.layout_version() == "workspace_v2":
            return self.root()
        return self.root() / "실행결과"

    def runtime_mail_bundles_root(self) -> Path:
        if self.layout_version() == "workspace_v2":
            return self.root() / "mail" / "bundles"
        return self.runtime_root() / "받은 메일"

    def runtime_exports_root(self) -> Path:
        if self.layout_version() == "workspace_v2":
            return self.root() / "exports" / "output"
        return self.runtime_root() / "엑셀 산출물"

    def runtime_exports_snapshots_root(self) -> Path:
        if self.layout_version() == "workspace_v2":
            return self.runtime_exports_root() / "snapshots"
        return self.runtime_exports_root() / "스냅샷"

    def operating_export_workbook_path(self, filename: str = "") -> Path:
        if self.layout_version() == "workspace_v2":
            return self.runtime_exports_root() / (filename or "operating_workbook.xlsx")
        return self.runtime_exports_root() / (filename or "운영본_기업_신청서_모음.xlsx")

    def runtime_logs_root(self) -> Path:
        if self.layout_version() == "workspace_v2":
            return self.root() / "logs"
        return self.runtime_root() / "로그"

    def runtime_app_logs_root(self) -> Path:
        if self.layout_version() == "workspace_v2":
            return self.runtime_logs_root() / "app"
        return self.runtime_logs_root() / "app"

    def runtime_analysis_logs_root(self) -> Path:
        if self.layout_version() == "workspace_v2":
            return self.runtime_logs_root() / "analysis"
        return self.runtime_logs_root() / "analysis_smoke"

    def runtime_exports_logs_root(self) -> Path:
        if self.layout_version() == "workspace_v2":
            return self.runtime_logs_root() / "app" / "exports"
        return self.runtime_logs_root() / "exports"

    def runtime_llm_logs_root(self) -> Path:
        return self.runtime_logs_root() / "llm"

    def runtime_mailbox_logs_root(self) -> Path:
        return self.runtime_logs_root() / "mailbox"

    def runtime_review_logs_root(self) -> Path:
        return self.runtime_logs_root() / "review"

    def llm_usage_log_path(self) -> Path:
        return self.runtime_llm_logs_root() / "openai_usage.jsonl"

    def ensure_runtime_dirs(self) -> list[Path]:
        if self.layout_version() == "workspace_v2":
            directories = [
                self.runtime_mail_bundles_root(),
                self.reference_exports_root(),
                self.runtime_exports_root(),
                self.runtime_exports_snapshots_root(),
                self.runtime_logs_root(),
                self.runtime_app_logs_root(),
                self.runtime_exports_logs_root(),
                self.runtime_analysis_logs_root(),
                self.runtime_mailbox_logs_root(),
                self.runtime_review_logs_root(),
                self.runtime_llm_logs_root(),
            ]
        else:
            directories = [
                self.runtime_mail_bundles_root(),
                self.runtime_exports_root(),
                self.runtime_exports_snapshots_root(),
                self.runtime_logs_root(),
                self.runtime_analysis_logs_root(),
                self.runtime_exports_logs_root(),
                self.runtime_mailbox_logs_root(),
                self.runtime_review_logs_root(),
                self.runtime_llm_logs_root(),
            ]
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
        return directories
