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


def load_shared_workspace(workspace_root: str | Path) -> SharedWorkspace:
    """기능: 기존 공유 워크스페이스 manifest를 읽어 복원한다."""

    root = Path(workspace_root)
    manifest_path = root / WORKSPACE_MANIFEST_FILENAME
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    return SharedWorkspace(
        root_dir=str(root),
        manifest=SharedWorkspaceManifest.from_dict(payload),
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
