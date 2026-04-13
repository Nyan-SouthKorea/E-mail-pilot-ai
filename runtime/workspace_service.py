"""세이브 파일(workspace) 관련 공용 service를 모은다."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from runtime.device_secret_store import (
    load_local_device_secrets,
    remember_last_workspace_secret,
)
from runtime.local_settings import (
    load_local_app_settings,
    remember_workspace,
)
from runtime.secrets_store import WorkspaceSecretsStore
from runtime.state_store import WorkspaceStateStore
from runtime.workspace import (
    WORKSPACE_MANIFEST_FILENAME,
    assert_supported_workspace,
    assess_workspace_path,
    create_shared_workspace,
    load_shared_workspace,
    suggest_workspace_root,
)


@dataclass(slots=True)
class RecentWorkspaceItem:
    path: str
    name: str
    exists: bool
    has_saved_password: bool

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(slots=True)
class WorkspaceOpenResult:
    workspace_root: str
    workspace_label: str
    remembered_locally: bool
    readonly_requested: bool
    message: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(slots=True)
class WorkspaceStatusResult:
    workspace_root: str
    manifest: dict[str, object]
    shared_settings: dict[str, object]
    state_counts: dict[str, int]
    latest_sync_run: dict[str, object] | None
    recent_workspaces: list[dict[str, object]] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def list_recent_workspaces() -> list[RecentWorkspaceItem]:
    settings = load_local_app_settings()
    device_secrets = load_local_device_secrets()
    items: list[RecentWorkspaceItem] = []
    for workspace_path in settings.recent_workspaces:
        candidate = Path(workspace_path)
        items.append(
            RecentWorkspaceItem(
                path=workspace_path,
                name=candidate.name or workspace_path,
                exists=candidate.exists(),
                has_saved_password=(
                    device_secrets.last_workspace_root == workspace_path
                    and bool(device_secrets.last_workspace_password)
                ),
            )
        )
    return items


def create_workspace_entry(
    *,
    save_parent_dir: str,
    workspace_password: str,
    workspace_label: str,
    remember_local: bool = True,
) -> WorkspaceOpenResult:
    workspace_root = suggest_workspace_root(
        parent_dir=save_parent_dir,
        workspace_label=workspace_label,
    )
    workspace = create_shared_workspace(
        workspace_root=workspace_root,
        workspace_password=workspace_password,
        workspace_label=workspace_label,
    )
    if remember_local:
        remember_workspace(str(workspace.root()))
        remember_last_workspace_secret(
            workspace_root=str(workspace.root()),
            workspace_password=workspace_password,
        )
    return WorkspaceOpenResult(
        workspace_root=str(workspace.root()),
        workspace_label=workspace.manifest.workspace_label,
        remembered_locally=remember_local,
        readonly_requested=False,
        message="새 세이브 파일을 만들었습니다.",
    )


def open_workspace_entry(
    *,
    workspace_root: str,
    workspace_password: str,
    readonly_requested: bool = False,
    remember_local: bool = True,
) -> WorkspaceOpenResult:
    assessment = assess_workspace_path(
        path_text=workspace_root,
        selection_kind="workspace_open",
    )
    if assessment.status != "pass":
        raise RuntimeError(assessment.message)
    workspace = assert_supported_workspace(load_shared_workspace(workspace_root))
    WorkspaceSecretsStore(
        path=str(workspace.secure_blob_path()),
        password=workspace_password,
    ).read()
    if remember_local:
        remember_workspace(str(workspace.root()))
        remember_last_workspace_secret(
            workspace_root=str(workspace.root()),
            workspace_password=workspace_password,
        )
    return WorkspaceOpenResult(
        workspace_root=str(workspace.root()),
        workspace_label=workspace.manifest.workspace_label,
        remembered_locally=remember_local,
        readonly_requested=readonly_requested,
        message="세이브 파일을 열었습니다.",
    )


def close_workspace_entry(*, workspace_root: str = "") -> dict[str, object]:
    target_root = workspace_root.strip()
    return {
        "closed_workspace_root": target_root,
        "recent_entry_preserved": True,
        "saved_password_preserved": True,
    }


def inspect_workspace_entry(
    *,
    workspace_root: str,
    workspace_password: str,
) -> WorkspaceStatusResult:
    workspace = assert_supported_workspace(load_shared_workspace(workspace_root))
    secrets_store = WorkspaceSecretsStore(
        path=str(workspace.secure_blob_path()),
        password=workspace_password,
    )
    state_store = WorkspaceStateStore(workspace.state_db_path())
    state_store.ensure_schema()
    return WorkspaceStatusResult(
        workspace_root=str(workspace.root()),
        manifest=workspace.manifest.to_dict(),
        shared_settings=secrets_store.masked_summary(),
        state_counts=state_store.summary_counts(),
        latest_sync_run=state_store.latest_sync_run(),
        recent_workspaces=[item.to_dict() for item in list_recent_workspaces()],
    )


def workspace_manifest_exists(path: str | Path) -> bool:
    return (Path(path) / WORKSPACE_MANIFEST_FILENAME).exists()
