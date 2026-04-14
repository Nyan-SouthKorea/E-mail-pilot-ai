"""공유 워크스페이스 단일 작성자 잠금을 관리한다."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import socket
import subprocess
import uuid


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_iso_datetime(text: str) -> datetime:
    return datetime.fromisoformat(text.replace("Z", "+00:00"))


@dataclass(slots=True)
class WorkspaceLockData:
    """기능: write lock 파일 payload를 표현한다."""

    lock_id: str
    workspace_id: str
    host: str
    user: str
    process_id: int
    app_kind: str
    opened_at: str
    heartbeat_at: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> "WorkspaceLockData":
        return cls(
            lock_id=str(payload["lock_id"]),
            workspace_id=str(payload["workspace_id"]),
            host=str(payload["host"]),
            user=str(payload["user"]),
            process_id=int(payload["process_id"]),
            app_kind=str(payload["app_kind"]),
            opened_at=str(payload["opened_at"]),
            heartbeat_at=str(payload["heartbeat_at"]),
        )


class LockedWorkspaceError(RuntimeError):
    """기능: 다른 프로세스가 write lock을 잡고 있음을 알린다."""


@dataclass(slots=True)
class WorkspaceWriteLockHandle:
    """기능: 획득한 write lock에 대한 refresh/release helper다."""

    path: str
    data: WorkspaceLockData

    def refresh(self) -> None:
        payload = WorkspaceLockData(
            lock_id=self.data.lock_id,
            workspace_id=self.data.workspace_id,
            host=self.data.host,
            user=self.data.user,
            process_id=self.data.process_id,
            app_kind=self.data.app_kind,
            opened_at=self.data.opened_at,
            heartbeat_at=utc_now_iso(),
        )
        self.data = payload
        Path(self.path).write_text(
            json.dumps(payload.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def release(self) -> None:
        path = Path(self.path)
        if not path.exists():
            return
        try:
            current = WorkspaceLockData.from_dict(
                json.loads(path.read_text(encoding="utf-8"))
            )
        except Exception:
            path.unlink(missing_ok=True)
            return
        if current.lock_id == self.data.lock_id:
            path.unlink(missing_ok=True)


def acquire_workspace_write_lock(
    *,
    lock_path: str | Path,
    workspace_id: str,
    app_kind: str,
    stale_after_seconds: int = 120,
    force_takeover: bool = False,
) -> WorkspaceWriteLockHandle:
    """기능: 공유 워크스페이스 write lock을 획득한다."""

    path = Path(lock_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        current = _load_lock_data(path)
        if current is not None and not force_takeover and not is_stale_lock(
            current,
            stale_after_seconds=stale_after_seconds,
        ):
            raise LockedWorkspaceError(
                (
                    f"다른 작성자가 이미 워크스페이스를 편집 중이다: "
                    f"{current.user}@{current.host} pid={current.process_id} app={current.app_kind}"
                )
            )

    payload = WorkspaceLockData(
        lock_id=f"lock-{uuid.uuid4().hex[:16]}",
        workspace_id=workspace_id,
        host=socket.gethostname(),
        user=os.environ.get("USER") or os.environ.get("USERNAME") or "unknown",
        process_id=os.getpid(),
        app_kind=app_kind,
        opened_at=utc_now_iso(),
        heartbeat_at=utc_now_iso(),
    )
    path.write_text(
        json.dumps(payload.to_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return WorkspaceWriteLockHandle(path=str(path), data=payload)


def is_stale_lock(
    lock_data: WorkspaceLockData,
    *,
    stale_after_seconds: int = 120,
) -> bool:
    """기능: heartbeat 시각 기준 stale lock인지 판단한다."""

    if _is_local_dead_process(lock_data):
        return True
    heartbeat_at = _parse_iso_datetime(lock_data.heartbeat_at)
    return datetime.now(timezone.utc) - heartbeat_at > timedelta(seconds=stale_after_seconds)


def _load_lock_data(path: Path) -> WorkspaceLockData | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    try:
        return WorkspaceLockData.from_dict(payload)
    except Exception:
        return None


def _is_local_dead_process(lock_data: WorkspaceLockData) -> bool:
    local_host_candidates = {
        socket.gethostname().lower(),
        socket.getfqdn().lower(),
        "localhost",
        "127.0.0.1",
    }
    if lock_data.host.lower() not in local_host_candidates:
        return False
    if lock_data.process_id <= 0:
        return False
    if os.name == "nt":
        return _is_local_dead_process_windows(lock_data.process_id)
    try:
        os.kill(lock_data.process_id, 0)
    except ProcessLookupError:
        return True
    except PermissionError:
        return False
    except OSError:
        return False
    except SystemError:
        return False
    except Exception:
        return False
    return False


def _is_local_dead_process_windows(process_id: int) -> bool:
    creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    try:
        result = subprocess.run(
            [
                "tasklist",
                "/FI",
                f"PID eq {process_id}",
                "/FO",
                "CSV",
                "/NH",
            ],
            capture_output=True,
            text=True,
            creationflags=creationflags,
            check=False,
        )
    except Exception:
        return False

    output = (result.stdout or "").strip()
    if not output:
        return True
    lowered = output.lower()
    if "no tasks are running" in lowered:
        return True
    return False
