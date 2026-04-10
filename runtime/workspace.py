"""공유 워크스페이스 save 구조를 관리한다."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import uuid

from project_paths import ProfilePaths

WORKSPACE_MANIFEST_FILENAME = "workspace.epa-workspace.json"
WORKSPACE_MANIFEST_VERSION = "runtime.shared_workspace.v1"


def utc_now_iso() -> str:
    """기능: UTC 기준 현재 시각 ISO 문자열을 반환한다."""

    return datetime.now(timezone.utc).isoformat()


@dataclass(slots=True)
class SharedWorkspaceManifest:
    """기능: 공유 워크스페이스 manifest를 표현한다."""

    workspace_id: str
    version: str = WORKSPACE_MANIFEST_VERSION
    workspace_label: str = ""
    created_at: str = field(default_factory=utc_now_iso)
    profile_relative_root: str = "profile"
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
            profile_relative_root=str(payload.get("profile_relative_root") or "profile"),
            secure_blob_path=str(payload.get("secure_blob_path") or "secure/secrets.enc.json"),
            state_db_path=str(payload.get("state_db_path") or "state/state.sqlite"),
            lock_path=str(payload.get("lock_path") or "locks/write.lock"),
            notes=list(payload.get("notes") or []),
        )


@dataclass(slots=True)
class SharedWorkspace:
    """기능: 공유 워크스페이스 루트와 표준 경로를 묶는다."""

    root_dir: str
    manifest: SharedWorkspaceManifest

    def root(self) -> Path:
        return Path(self.root_dir)

    def manifest_path(self) -> Path:
        return self.root() / WORKSPACE_MANIFEST_FILENAME

    def profile_root(self) -> Path:
        return self.root() / self.manifest.profile_relative_root

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
        """기능: 워크스페이스 내부 경로를 루트 기준 상대경로로 바꾼다."""

        target = Path(path)
        if not target.is_absolute():
            return target.as_posix()
        return target.resolve().relative_to(self.root().resolve()).as_posix()

    def from_workspace_relative(self, relative_path: str | Path) -> Path:
        return self.root() / Path(relative_path)


@dataclass(slots=True)
class WorkspacePathAssessment:
    """기능: UI 입력 경로가 세이브 파일/템플릿 기준에 맞는지 설명한다."""

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
    """기능: 기존 공유 워크스페이스 manifest를 읽어 복원한다."""

    root = Path(workspace_root)
    manifest_path = root / WORKSPACE_MANIFEST_FILENAME
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    return SharedWorkspace(
        root_dir=str(root),
        manifest=SharedWorkspaceManifest.from_dict(payload),
    )


def assess_workspace_path(
    *,
    path_text: str,
    selection_kind: str,
    workspace_root: str | Path | None = None,
) -> WorkspacePathAssessment:
    """기능: UI에서 고른 경로를 열기/생성/가져오기/템플릿 입력 기준으로 분류한다."""

    text = path_text.strip()
    if not text:
        return WorkspacePathAssessment(
            status="warn",
            category="empty",
            message="아직 경로가 입력되지 않았다.",
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
    if selection_kind == "workspace_create":
        return _assess_workspace_create(candidate, normalized_path)
    if selection_kind == "profile_import":
        return _assess_profile_import(candidate, normalized_path)
    if selection_kind == "template_file":
        return _assess_template_file(
            candidate=candidate,
            normalized_path=normalized_path,
            workspace_root=workspace_root,
        )
    return WorkspacePathAssessment(
        status="fail",
        category="unknown_selection_kind",
        message=f"알 수 없는 경로 검사 종류다: {selection_kind}",
        normalized_path=normalized_path,
    )


def create_shared_workspace(
    *,
    workspace_root: str | Path,
    workspace_password: str,
    workspace_label: str = "",
    import_profile_root: str | Path | None = None,
) -> SharedWorkspace:
    """기능: 공유 워크스페이스 폴더 구조와 초기 상태를 만든다."""

    root = Path(workspace_root)
    root.mkdir(parents=True, exist_ok=True)

    manifest = SharedWorkspaceManifest(
        workspace_id=f"epa-{uuid.uuid4().hex[:16]}",
        workspace_label=workspace_label.strip(),
        notes=[
            "공유 워크스페이스에는 절대경로를 저장하지 않는다.",
            "민감한 값은 secure/secrets.enc.json에 암호화해 둔다.",
        ],
    )
    workspace = SharedWorkspace(root_dir=str(root), manifest=manifest)
    _ensure_workspace_dirs(workspace)
    _write_manifest(workspace)

    if import_profile_root:
        import_profile_into_workspace(
            source_profile_root=import_profile_root,
            workspace=workspace,
        )

    from runtime.secrets_store import create_encrypted_secrets_file
    from runtime.state_store import WorkspaceStateStore

    create_encrypted_secrets_file(
        path=workspace.secure_blob_path(),
        password=workspace_password,
        payload=_default_shared_settings(workspace),
    )
    WorkspaceStateStore(workspace.state_db_path()).ensure_schema()
    return workspace


def _assess_workspace_open(candidate: Path, normalized_path: str) -> WorkspacePathAssessment:
    if _looks_like_profile_subdir(candidate):
        return WorkspacePathAssessment(
            status="fail",
            category="profile_subdir",
            message="`profile/` 하위가 아니라 세이브 파일 루트 폴더를 선택해야 한다.",
            normalized_path=normalized_path,
        )
    if _looks_like_repo_root(candidate):
        return WorkspacePathAssessment(
            status="fail",
            category="repo_root",
            message="`repo` 자체는 세이브 파일 폴더로 열 수 없다. 별도 공유 폴더를 선택해야 한다.",
            normalized_path=normalized_path,
        )
    if not candidate.exists():
        return WorkspacePathAssessment(
            status="fail",
            category="missing",
            message="기존 세이브 파일을 열 때는 이미 존재하는 폴더를 선택해야 한다.",
            normalized_path=normalized_path,
        )
    if (candidate / WORKSPACE_MANIFEST_FILENAME).exists():
        return WorkspacePathAssessment(
            status="pass",
            category="existing_workspace",
            message="기존 세이브 파일 폴더로 보인다. 바로 열 수 있다.",
            normalized_path=normalized_path,
        )
    return WorkspacePathAssessment(
        status="fail",
        category="missing_manifest",
        message="이 폴더에는 세이브 파일 manifest가 없다. 새 세이브를 만들거나 manifest가 있는 폴더를 골라야 한다.",
        normalized_path=normalized_path,
    )


def _assess_workspace_create(candidate: Path, normalized_path: str) -> WorkspacePathAssessment:
    if _looks_like_profile_subdir(candidate):
        return WorkspacePathAssessment(
            status="fail",
            category="profile_subdir",
            message="`profile/` 하위가 아니라 세이브 파일 루트로 쓸 전용 폴더를 선택해야 한다.",
            normalized_path=normalized_path,
        )
    if _looks_like_repo_root(candidate):
        return WorkspacePathAssessment(
            status="fail",
            category="repo_root",
            message="`repo` 자체에는 세이브 파일을 만들 수 없다. 별도 공유 폴더를 선택해야 한다.",
            normalized_path=normalized_path,
        )
    if (candidate / WORKSPACE_MANIFEST_FILENAME).exists():
        return WorkspacePathAssessment(
            status="fail",
            category="existing_workspace",
            message="이미 세이브 파일이 있는 폴더다. 새로 만들기 대신 기존 세이브 열기를 써야 한다.",
            normalized_path=normalized_path,
        )
    if not candidate.exists():
        return WorkspacePathAssessment(
            status="pass",
            category="new_workspace_path",
            message="아직 없는 경로다. 이 경로로 새 세이브 파일 폴더를 만들 수 있다.",
            normalized_path=normalized_path,
        )
    if not any(candidate.iterdir()):
        return WorkspacePathAssessment(
            status="pass",
            category="empty_directory",
            message="비어 있는 폴더다. 새 세이브 파일 루트로 쓰기 좋다.",
            normalized_path=normalized_path,
        )
    return WorkspacePathAssessment(
        status="fail",
        category="non_empty_directory",
        message="비어 있지 않은 폴더다. 다른 용도와 섞이지 않도록 전용 빈 폴더를 권장한다.",
        normalized_path=normalized_path,
    )


def _assess_profile_import(candidate: Path, normalized_path: str) -> WorkspacePathAssessment:
    if not candidate.exists():
        return WorkspacePathAssessment(
            status="fail",
            category="missing",
            message="기존 profile import 경로는 실제로 존재해야 한다.",
            normalized_path=normalized_path,
        )
    if (candidate / WORKSPACE_MANIFEST_FILENAME).exists():
        return WorkspacePathAssessment(
            status="fail",
            category="workspace_root",
            message="세이브 파일 루트가 아니라 기존 로컬 profile root를 골라야 한다.",
            normalized_path=normalized_path,
        )
    if (candidate / "참고자료").exists() or (candidate / "실행결과").exists():
        return WorkspacePathAssessment(
            status="pass",
            category="profile_root",
            message="기존 profile root로 보인다. 참고자료와 실행결과를 가져올 수 있다.",
            normalized_path=normalized_path,
        )
    return WorkspacePathAssessment(
        status="fail",
        category="missing_profile_dirs",
        message="이 경로에는 `참고자료` 또는 `실행결과` 폴더가 없다. 기존 profile root를 다시 확인해야 한다.",
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
            message="템플릿은 `.xlsx` 또는 `.xlsm` 같은 Excel 파일이어야 한다.",
            normalized_path=normalized_path,
        )
    if workspace_root is not None:
        try:
            candidate.resolve(strict=False).relative_to(Path(workspace_root).resolve())
        except ValueError:
            return WorkspacePathAssessment(
                status="fail",
                category="outside_workspace",
                message="템플릿 경로는 현재 세이브 파일 폴더 안쪽에 있어야 한다.",
                normalized_path=normalized_path,
            )
    if candidate.exists():
        return WorkspacePathAssessment(
            status="pass",
            category="template_exists",
            message="현재 세이브 파일 기준으로 쓸 수 있는 템플릿 파일이다.",
            normalized_path=normalized_path,
        )
    return WorkspacePathAssessment(
        status="warn",
        category="template_missing",
        message="경로 형식은 맞지만 파일이 아직 없다. 저장은 가능하지만 이후 sync 전에는 실제 파일이 필요하다.",
        normalized_path=normalized_path,
    )


def import_profile_into_workspace(
    *,
    source_profile_root: str | Path,
    workspace: SharedWorkspace,
) -> list[Path]:
    """기능: 기존 로컬 프로필을 공유 워크스페이스 profile로 복사 import 한다."""

    source_root = Path(source_profile_root)
    destination_root = workspace.profile_root()
    destination_root.mkdir(parents=True, exist_ok=True)

    copied_roots: list[Path] = []
    for name in ["참고자료", "실행결과"]:
        source_path = source_root / name
        if not source_path.exists():
            continue
        destination_path = destination_root / name
        shutil.copytree(source_path, destination_path, dirs_exist_ok=True)
        copied_roots.append(destination_path)
    return copied_roots


def _looks_like_repo_root(path: Path) -> bool:
    return (
        path.exists()
        and path.is_dir()
        and (path / "AGENTS.md").exists()
        and (path / "README.md").exists()
        and (path / "app").exists()
        and (path / "runtime").exists()
    )


def _looks_like_profile_subdir(path: Path) -> bool:
    if path.name != "profile":
        return False
    return (path.parent / WORKSPACE_MANIFEST_FILENAME).exists()


def _ensure_workspace_dirs(workspace: SharedWorkspace) -> None:
    directories = [
        workspace.root(),
        workspace.secure_blob_path().parent,
        workspace.state_db_path().parent,
        workspace.lock_path().parent,
        workspace.profile_root(),
        workspace.profile_root() / "참고자료",
        workspace.profile_root() / "실행결과" / "받은 메일",
        workspace.profile_root() / "실행결과" / "엑셀 산출물",
        workspace.profile_root() / "실행결과" / "로그",
    ]
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)


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
            "default_folder": "INBOX",
        },
        "exports": {
            "template_workbook_relative_path": template_relative_path,
            "operating_workbook_relative_path": operating_relative_path,
        },
    }
