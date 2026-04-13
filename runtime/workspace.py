"""공유 세이브 파일(workspace) 구조를 관리한다."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import uuid

from project_paths import ProfilePaths
from runtime.local_settings import default_workspace_parent_dir

WORKSPACE_MANIFEST_FILENAME = "workspace.epa-workspace.json"
WORKSPACE_MANIFEST_VERSION = "runtime.shared_workspace.v2"

_INVALID_WINDOWS_FILENAME_CHARS = re.compile(r'[<>:"/\\\\|?*]+')


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_workspace_directory_name(
    *,
    workspace_label: str,
    now: datetime | None = None,
) -> str:
    timestamp = (now or datetime.now()).strftime("%y%m%d_%H%M")
    label = _INVALID_WINDOWS_FILENAME_CHARS.sub(" ", workspace_label.strip())
    label = re.sub(r"\s+", " ", label).strip()
    return f"{timestamp}_{label}" if label else f"{timestamp}_새 세이브"


def suggest_workspace_root(
    *,
    parent_dir: str | Path | None = None,
    workspace_label: str,
    now: datetime | None = None,
) -> Path:
    base_dir = Path(parent_dir or default_workspace_parent_dir())
    return base_dir / build_workspace_directory_name(workspace_label=workspace_label, now=now)


@dataclass(slots=True)
class SharedWorkspaceManifest:
    workspace_id: str
    version: str = WORKSPACE_MANIFEST_VERSION
    workspace_label: str = ""
    created_at: str = field(default_factory=utc_now_iso)
    profile_relative_root: str = "."
    secure_blob_path: str = "secure/secrets.enc.json"
    state_db_path: str = "state/state.sqlite"
    lock_path: str = "locks/write.lock"
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> "SharedWorkspaceManifest":
        return cls(
            workspace_id=str(payload["workspace_id"]),
            version=str(payload.get("version") or WORKSPACE_MANIFEST_VERSION),
            workspace_label=str(payload.get("workspace_label") or ""),
            created_at=str(payload.get("created_at") or utc_now_iso()),
            profile_relative_root=str(payload.get("profile_relative_root") or "."),
            secure_blob_path=str(payload.get("secure_blob_path") or "secure/secrets.enc.json"),
            state_db_path=str(payload.get("state_db_path") or "state/state.sqlite"),
            lock_path=str(payload.get("lock_path") or "locks/write.lock"),
            notes=list(payload.get("notes") or []),
        )


@dataclass(slots=True)
class SharedWorkspace:
    root_dir: str
    manifest: SharedWorkspaceManifest

    def root(self) -> Path:
        return Path(self.root_dir)

    def manifest_path(self) -> Path:
        return self.root() / WORKSPACE_MANIFEST_FILENAME

    def profile_root(self) -> Path:
        relative = str(self.manifest.profile_relative_root or ".").strip() or "."
        if relative in {".", "./"}:
            return self.root()
        return self.root() / relative

    def profile_paths(self) -> ProfilePaths:
        return ProfilePaths(str(self.profile_root()))

    def secure_blob_path(self) -> Path:
        return self.root() / self.manifest.secure_blob_path

    def state_db_path(self) -> Path:
        return self.root() / self.manifest.state_db_path

    def lock_path(self) -> Path:
        return self.root() / self.manifest.lock_path

    def review_logs_root(self) -> Path:
        return self.profile_paths().runtime_review_logs_root()

    def operating_workbook_path(self) -> Path:
        return self.profile_paths().operating_export_workbook_path()

    def operating_snapshot_root(self) -> Path:
        return self.profile_paths().runtime_exports_snapshots_root()

    def to_workspace_relative(self, path: str | Path) -> str:
        target = Path(path)
        if not target.is_absolute():
            return target.as_posix()
        return target.resolve().relative_to(self.root().resolve()).as_posix()

    def from_workspace_relative(self, relative_path: str | Path) -> Path:
        return self.root() / Path(relative_path)

    def is_supported(self) -> bool:
        return self.manifest.version == WORKSPACE_MANIFEST_VERSION


@dataclass(slots=True)
class WorkspacePathAssessment:
    status: str
    category: str
    message: str
    normalized_path: str = ""

    def to_dict(self) -> dict[str, str]:
        return {
            "status": self.status,
            "category": self.category,
            "message": self.message,
            "normalized_path": self.normalized_path,
        }


def load_shared_workspace(workspace_root: str | Path) -> SharedWorkspace:
    root = Path(workspace_root)
    manifest_path = root / WORKSPACE_MANIFEST_FILENAME
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    return SharedWorkspace(root_dir=str(root), manifest=SharedWorkspaceManifest.from_dict(payload))


def assert_supported_workspace(workspace: SharedWorkspace) -> SharedWorkspace:
    if workspace.manifest.version != WORKSPACE_MANIFEST_VERSION:
        raise RuntimeError("지원하지 않는 이전 베타 세이브입니다. 새 세이브 파일을 만들어야 합니다.")
    return workspace


def assess_workspace_path(
    *,
    path_text: str,
    selection_kind: str,
    workspace_root: str | Path | None = None,
) -> WorkspacePathAssessment:
    text = path_text.strip()
    if not text:
        return WorkspacePathAssessment(
            status="warn",
            category="empty",
            message="아직 경로가 입력되지 않았습니다.",
        )

    candidate = Path(text).expanduser()
    if not candidate.is_absolute():
        if selection_kind == "template_file" and workspace_root:
            candidate = Path(workspace_root) / candidate
        else:
            candidate = candidate.resolve(strict=False)
    normalized_path = str(candidate)

    if selection_kind == "workspace_open":
        return _assess_workspace_open(candidate, normalized_path)
    if selection_kind == "workspace_parent":
        return _assess_workspace_parent(candidate, normalized_path)
    if selection_kind == "template_file":
        return _assess_template_file(
            candidate=candidate,
            normalized_path=normalized_path,
            workspace_root=workspace_root,
        )
    return WorkspacePathAssessment(
        status="fail",
        category="unknown_selection_kind",
        message=f"알 수 없는 경로 검사 종류입니다: {selection_kind}",
        normalized_path=normalized_path,
    )


def create_shared_workspace(
    *,
    workspace_root: str | Path,
    workspace_password: str,
    workspace_label: str = "",
    import_profile_root: str | Path | None = None,
) -> SharedWorkspace:
    root = Path(workspace_root)
    if import_profile_root:
        raise RuntimeError("이전 데이터 가져오기는 더 이상 지원하지 않습니다. 새 세이브 파일로 다시 시작해 주세요.")

    root.mkdir(parents=True, exist_ok=True)
    manifest = SharedWorkspaceManifest(
        workspace_id=f"epa-{uuid.uuid4().hex[:16]}",
        workspace_label=workspace_label.strip(),
        notes=[
            "새 세이브 파일은 v2 영문 구조를 사용합니다.",
            "민감한 값은 secure/secrets.enc.json에 암호화해 둡니다.",
        ],
    )
    workspace = SharedWorkspace(root_dir=str(root), manifest=manifest)
    _write_manifest(workspace)
    _ensure_workspace_dirs(workspace)
    _ensure_default_template_workbook(workspace)

    from runtime.secrets_store import create_encrypted_secrets_file
    from runtime.state_store import WorkspaceStateStore

    create_encrypted_secrets_file(
        path=workspace.secure_blob_path(),
        password=workspace_password,
        payload=_default_shared_settings(workspace),
    )
    WorkspaceStateStore(workspace.state_db_path()).ensure_schema()
    return workspace


def import_profile_into_workspace(
    *,
    source_profile_root: str | Path,
    workspace: SharedWorkspace,
) -> list[Path]:
    raise RuntimeError("이전 베타 데이터 가져오기는 지원하지 않습니다. 새 세이브 파일로 다시 시작해 주세요.")


def _assess_workspace_open(candidate: Path, normalized_path: str) -> WorkspacePathAssessment:
    if _looks_like_repo_root(candidate):
        return WorkspacePathAssessment(
            status="fail",
            category="repo_root",
            message="repo 폴더 자체는 세이브 파일 폴더가 아닙니다. 별도의 세이브 파일 폴더를 골라야 합니다.",
            normalized_path=normalized_path,
        )
    if not candidate.exists():
        return WorkspacePathAssessment(
            status="fail",
            category="missing",
            message="기존 세이브 파일을 열려면 이미 존재하는 폴더를 선택해야 합니다.",
            normalized_path=normalized_path,
        )
    manifest_path = candidate / WORKSPACE_MANIFEST_FILENAME
    if manifest_path.exists():
        try:
            workspace = load_shared_workspace(candidate)
        except Exception:
            return WorkspacePathAssessment(
                status="fail",
                category="broken_manifest",
                message="세이브 파일 manifest를 읽지 못했습니다. 파일이 손상되었을 수 있습니다.",
                normalized_path=normalized_path,
            )
        if not workspace.is_supported():
            return WorkspacePathAssessment(
                status="fail",
                category="unsupported_legacy_workspace",
                message="이 폴더는 이전 베타 세이브입니다. 새 세이브 파일을 만들어야 합니다.",
                normalized_path=normalized_path,
            )
        return WorkspacePathAssessment(
            status="pass",
            category="existing_workspace",
            message="기존 세이브 파일 폴더입니다. 바로 열 수 있습니다.",
            normalized_path=normalized_path,
        )
    if (candidate / "profile").exists() or (candidate / "참고자료").exists() or (candidate / "실행결과").exists():
        return WorkspacePathAssessment(
            status="fail",
            category="legacy_workspace_like",
            message="이 폴더는 이전 베타 구조처럼 보입니다. 새 세이브 파일을 만들어야 합니다.",
            normalized_path=normalized_path,
        )
    return WorkspacePathAssessment(
        status="fail",
        category="missing_manifest",
        message="이 폴더에는 세이브 파일 manifest가 없습니다. 새 세이브를 만들거나 올바른 폴더를 골라야 합니다.",
        normalized_path=normalized_path,
    )


def _assess_workspace_parent(candidate: Path, normalized_path: str) -> WorkspacePathAssessment:
    if _looks_like_repo_root(candidate):
        return WorkspacePathAssessment(
            status="fail",
            category="repo_root",
            message="repo 폴더 자체를 세이브 파일 저장 위치로 쓰지 않습니다. 별도의 상위 폴더를 고르세요.",
            normalized_path=normalized_path,
        )
    if not candidate.exists():
        return WorkspacePathAssessment(
            status="warn",
            category="missing_parent",
            message="아직 없는 폴더입니다. 저장 시 함께 만들 수 있지만, 보통은 기존 상위 폴더를 고르는 편이 좋습니다.",
            normalized_path=normalized_path,
        )
    if not candidate.is_dir():
        return WorkspacePathAssessment(
            status="fail",
            category="not_directory",
            message="폴더만 선택할 수 있습니다.",
            normalized_path=normalized_path,
        )
    return WorkspacePathAssessment(
        status="pass",
        category="workspace_parent",
        message="이 위치 아래에 새 세이브 파일 폴더를 만들 수 있습니다.",
        normalized_path=normalized_path,
    )


def _assess_template_file(
    *,
    candidate: Path,
    normalized_path: str,
    workspace_root: str | Path | None,
) -> WorkspacePathAssessment:
    suffix = candidate.suffix.lower()
    if suffix not in {".xlsx", ".xlsm", ".xltx", ".xltm"}:
        return WorkspacePathAssessment(
            status="fail",
            category="invalid_template_suffix",
            message="엑셀 양식은 `.xlsx` 또는 `.xlsm` 같은 Excel 파일이어야 합니다.",
            normalized_path=normalized_path,
        )
    if workspace_root is not None:
        try:
            candidate.resolve(strict=False).relative_to(Path(workspace_root).resolve())
        except ValueError:
            return WorkspacePathAssessment(
                status="fail",
                category="outside_workspace",
                message="엑셀 양식은 현재 세이브 파일 폴더 안에 있어야 합니다.",
                normalized_path=normalized_path,
            )
    if candidate.exists():
        return WorkspacePathAssessment(
            status="pass",
            category="template_exists",
            message="현재 세이브 파일 기준으로 사용할 수 있는 엑셀 양식입니다.",
            normalized_path=normalized_path,
        )
    return WorkspacePathAssessment(
        status="warn",
        category="template_missing",
        message="경로 형식은 맞지만 파일이 아직 없습니다. 새 세이브에서는 기본 양식이 자동 준비됩니다.",
        normalized_path=normalized_path,
    )


def _looks_like_repo_root(path: Path) -> bool:
    return (
        path.exists()
        and path.is_dir()
        and (path / "AGENTS.md").exists()
        and (path / "README.md").exists()
        and (path / "app").exists()
        and (path / "runtime").exists()
    )


def _ensure_workspace_dirs(workspace: SharedWorkspace) -> None:
    directories = [
        workspace.root(),
        workspace.secure_blob_path().parent,
        workspace.state_db_path().parent,
        workspace.lock_path().parent,
        workspace.profile_paths().runtime_mail_bundles_root(),
        workspace.profile_paths().reference_exports_root(),
        workspace.profile_paths().runtime_exports_root(),
        workspace.profile_paths().runtime_exports_snapshots_root(),
        workspace.profile_paths().runtime_logs_root(),
        workspace.profile_paths().runtime_app_logs_root(),
        workspace.profile_paths().runtime_exports_logs_root(),
        workspace.profile_paths().runtime_analysis_logs_root(),
        workspace.profile_paths().runtime_mailbox_logs_root(),
        workspace.profile_paths().runtime_review_logs_root(),
        workspace.profile_paths().runtime_llm_logs_root(),
    ]
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)


def _ensure_default_template_workbook(workspace: SharedWorkspace) -> None:
    template_path = workspace.profile_paths().template_workbook_path()
    if template_path.exists():
        return
    from openpyxl import Workbook

    template_path.parent.mkdir(parents=True, exist_ok=True)
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "기업 신청서"
    headers = [
        "번호",
        "기업명",
        "담당자명",
        "연락처",
        "이메일",
        "홈페이지/SNS",
        "관련산업군",
        "주요 제품/서비스",
        "신청목적",
        "기업소개(한줄)",
        "사업내용 요약",
        "상세 요청 사항",
    ]
    for column_index, header in enumerate(headers, start=1):
        worksheet.cell(row=1, column=column_index).value = header
    worksheet.freeze_panes = "A2"
    workbook.save(template_path)


def _write_manifest(workspace: SharedWorkspace) -> None:
    workspace.manifest_path().write_text(
        json.dumps(workspace.manifest.to_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _default_shared_settings(workspace: SharedWorkspace) -> dict[str, object]:
    profile_paths = workspace.profile_paths()
    default_template_path = profile_paths.template_workbook_path()
    template_relative_path = ""
    if default_template_path.exists():
        template_relative_path = workspace.to_workspace_relative(default_template_path)

    operating_relative_path = workspace.to_workspace_relative(
        profile_paths.operating_export_workbook_path()
    )

    return {
        "workspace": {
            "workspace_id": workspace.manifest.workspace_id,
            "workspace_label": workspace.manifest.workspace_label,
            "created_at": workspace.manifest.created_at,
        },
        "llm": {
            "api_key": "",
            "model": "gpt-5.4",
        },
        "mailbox": {
            "email_address": "",
            "login_username": "",
            "password": "",
            "default_folder": "",
            "available_folders": [],
            "recommended_folder": "",
            "connection_status": "unknown",
            "connection_checked_at": "",
            "last_error": "",
            "login_username_kind": "email_address_fallback",
        },
        "exports": {
            "template_workbook_relative_path": template_relative_path,
            "operating_workbook_relative_path": operating_relative_path,
        },
    }
