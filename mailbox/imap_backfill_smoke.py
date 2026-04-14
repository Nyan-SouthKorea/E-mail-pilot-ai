"""실제 계정 INBOX 전체를 read-only로 backfill 하는 smoke."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass, field
from email import policy
from email.parser import BytesParser
from pathlib import Path
from typing import Callable

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from project_paths import ProfilePaths, default_example_profile_root

if __package__ in (None, ""):
    from mailbox.autoconfig import (
        run_mailbox_autoconfig_smoke,
        save_mailbox_autoconfig_report,
    )
    from mailbox.bundle_reader import (
        is_valid_runtime_bundle_directory,
        list_valid_runtime_bundle_directories,
        load_normalized_message_from_bundle,
    )
    from mailbox.imap_fetch_smoke import (
        MailboxImapFetchSmokeReport,
        _open_logged_in_imap_client,
        choose_successful_imap_candidate,
        default_autoconfig_report_path,
        fetch_imap_message_by_uid,
        list_imap_message_uids,
        materialize_fetched_imap_message,
        predict_bundle_id_for_fetched_imap_message,
        resolve_successful_imap_login_username,
        resolve_successful_imap_login_username_kind,
    )
    from mailbox.local_account_config import (
        default_local_account_config_path,
        load_local_mailbox_account_config,
    )
else:
    from .autoconfig import (
        run_mailbox_autoconfig_smoke,
        save_mailbox_autoconfig_report,
    )
    from .bundle_reader import (
        is_valid_runtime_bundle_directory,
        list_valid_runtime_bundle_directories,
        load_normalized_message_from_bundle,
    )
    from .imap_fetch_smoke import (
        _open_logged_in_imap_client,
        choose_successful_imap_candidate,
        default_autoconfig_report_path,
        fetch_imap_message_by_uid,
        list_imap_message_uids,
        materialize_fetched_imap_message,
        predict_bundle_id_for_fetched_imap_message,
        resolve_successful_imap_login_username,
        resolve_successful_imap_login_username_kind,
    )
    from .local_account_config import (
        default_local_account_config_path,
        load_local_mailbox_account_config,
    )


@dataclass(slots=True)
class MailboxImapBackfillItemResult:
    """기능: backfill 중 메일 1건 처리 결과를 표현한다."""

    uid: str
    status: str
    bundle_id: str | None = None
    bundle_root: str | None = None
    normalized_json_path: str | None = None
    subject: str = ""
    internet_message_id: str = ""
    received_at: str | None = None
    failure_message: str = ""

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(slots=True)
class MailboxImapBackfillSmokeReport:
    """기능: INBOX 전체 read-only backfill 결과를 표현한다."""

    email_address: str
    login_username_kind: str
    auth_report_path: str
    success: bool
    selected_candidate: dict[str, object] | None
    folder: str
    total_message_count: int = 0
    fetched_count: int = 0
    skipped_existing_count: int = 0
    failed_count: int = 0
    items: list[MailboxImapBackfillItemResult] = field(default_factory=list)
    failure_message: str = ""
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["items"] = [item.to_dict() for item in self.items]
        return payload


ProgressCallback = Callable[[dict[str, object]], None]


def default_profile_root() -> Path:
    """기능: 현재 예시 사용자 프로필 루트 기본 경로를 반환한다."""

    return default_example_profile_root()


def default_backfill_report_path(profile_root: str, email_address: str) -> Path:
    """기능: IMAP backfill report 기본 저장 경로를 만든다."""

    profile_paths = ProfilePaths(profile_root)
    safe_name = email_address.replace("@", "_at_").replace(".", "_")
    return profile_paths.runtime_mailbox_logs_root() / f"{safe_name}_imap_backfill_smoke.json"


def run_imap_inbox_backfill_smoke(
    *,
    credentials_path: str | Path | None = None,
    profile_root: str | Path | None = None,
    account_config=None,
    folder: str = "INBOX",
    latest_limit: int | None = None,
    timeout_seconds: float = 8.0,
    max_probes_per_protocol: int = 2,
    on_progress: ProgressCallback | None = None,
) -> MailboxImapBackfillSmokeReport:
    """기능: 실제 계정으로 INBOX 전체를 read-only backfill 해 bundle로 저장한다."""

    config = account_config or load_local_mailbox_account_config(
        credentials_path=credentials_path,
        profile_root=profile_root,
    )
    profile_paths = ProfilePaths(config.profile_root)
    profile_paths.ensure_runtime_dirs()

    auth_report = run_mailbox_autoconfig_smoke(
        email_address=config.email_address,
        login_username=config.login_username,
        password=config.password,
        timeout_seconds=timeout_seconds,
        max_probes_per_protocol=max_probes_per_protocol,
    )
    auth_report_path = save_mailbox_autoconfig_report(
        auth_report,
        default_autoconfig_report_path(config.profile_root, config.email_address),
    )

    notes = list(config.notes) + list(auth_report.notes)
    selected_candidate = choose_successful_imap_candidate(auth_report)
    if selected_candidate is None:
        report = MailboxImapBackfillSmokeReport(
            email_address=config.email_address,
            login_username_kind=auth_report.login_username_kind,
            auth_report_path=str(auth_report_path),
            success=False,
            selected_candidate=None,
            folder=folder,
            failure_message="로그인 성공한 IMAP 후보가 없어 INBOX backfill을 진행하지 않았다.",
            notes=notes,
        )
        return save_imap_backfill_report(
            report,
            default_backfill_report_path(config.profile_root, config.email_address),
        )

    successful_login_username_kind = resolve_successful_imap_login_username_kind(
        report=auth_report,
        candidate=selected_candidate,
        explicit_login_username=config.login_username,
        email_address=config.email_address,
    )
    successful_login_username = resolve_successful_imap_login_username(
        report=auth_report,
        candidate=selected_candidate,
        explicit_login_username=config.login_username,
        email_address=config.email_address,
    )

    existing_valid_bundle_ids = {
        path.name
        for path in list_valid_runtime_bundle_directories(config.profile_root)
        if is_valid_runtime_bundle_directory(path)
    }
    existing_imap_uids = _load_existing_imap_uid_index(config.profile_root)
    report_output_path = default_backfill_report_path(
        config.profile_root,
        config.email_address,
    )

    client = _open_logged_in_imap_client(
        candidate=selected_candidate,
        login_username=successful_login_username,
        password=config.password,
        timeout_seconds=timeout_seconds,
    )
    try:
        uid_list = list_imap_message_uids(client=client, folder=folder)
        if latest_limit is not None and latest_limit > 0:
            uid_list = uid_list[-latest_limit:]
            notes.append(f"최근 {latest_limit}건만 빠른 테스트 범위로 backfill 했다.")
        items: list[MailboxImapBackfillItemResult] = []
        _emit_backfill_progress(
            callback=on_progress,
            processed_count=0,
            total_count=len(uid_list),
            items=items,
        )

        for index, uid in enumerate(uid_list, start=1):
            try:
                if uid in existing_imap_uids:
                    items.append(
                        MailboxImapBackfillItemResult(
                            uid=uid,
                            status="skipped_existing",
                        )
                    )
                    _maybe_checkpoint_backfill_report(
                        index=index,
                        total_count=len(uid_list),
                        items=items,
                        email_address=config.email_address,
                        login_username_kind=successful_login_username_kind,
                        auth_report_path=str(auth_report_path),
                        selected_candidate=selected_candidate.to_dict(),
                        folder=folder,
                        notes=notes,
                        output_path=report_output_path,
                    )
                    continue

                fetched = fetch_imap_message_by_uid(client=client, uid=uid, folder=folder)
                snapshot = _extract_fetched_message_snapshot(fetched.raw_bytes)
                bundle_id = predict_bundle_id_for_fetched_imap_message(
                    fetched_message=fetched,
                )
                if bundle_id in existing_valid_bundle_ids:
                    items.append(
                        MailboxImapBackfillItemResult(
                            uid=uid,
                            status="skipped_existing",
                            bundle_id=bundle_id,
                            subject=snapshot["subject"],
                            internet_message_id=snapshot["internet_message_id"],
                            received_at=fetched.internal_date,
                        )
                    )
                    existing_imap_uids.add(uid)
                    _maybe_checkpoint_backfill_report(
                        index=index,
                        total_count=len(uid_list),
                        items=items,
                        email_address=config.email_address,
                        login_username_kind=successful_login_username_kind,
                        auth_report_path=str(auth_report_path),
                        selected_candidate=selected_candidate.to_dict(),
                        folder=folder,
                        notes=notes,
                        output_path=report_output_path,
                    )
                    continue

                materialized = materialize_fetched_imap_message(
                    fetched_message=fetched,
                    profile_root=config.profile_root,
                    provider=auth_report.plan.provider_key,
                    account_id=config.email_address,
                    labels=["imap_inbox_backfill"],
                )
                existing_valid_bundle_ids.add(materialized.bundle_id)
                existing_imap_uids.add(uid)
                items.append(
                    MailboxImapBackfillItemResult(
                        uid=uid,
                        status="fetched",
                        bundle_id=materialized.bundle_id,
                        bundle_root=materialized.bundle_root,
                        normalized_json_path=materialized.normalized_json_path,
                        subject=snapshot["subject"],
                        internet_message_id=snapshot["internet_message_id"],
                        received_at=fetched.internal_date,
                    )
                )
            except Exception as exc:
                items.append(
                    MailboxImapBackfillItemResult(
                        uid=uid,
                        status="failed",
                        failure_message=f"{exc.__class__.__name__}: {exc}",
                    )
                )
            _maybe_checkpoint_backfill_report(
                index=index,
                total_count=len(uid_list),
                items=items,
                email_address=config.email_address,
                login_username_kind=successful_login_username_kind,
                auth_report_path=str(auth_report_path),
                selected_candidate=selected_candidate.to_dict(),
                folder=folder,
                notes=notes,
                output_path=report_output_path,
            )
            _emit_backfill_progress(
                callback=on_progress,
                processed_count=index,
                total_count=len(uid_list),
                items=items,
                latest_uid=uid,
            )

        fetched_count = sum(1 for item in items if item.status == "fetched")
        skipped_existing_count = sum(
            1 for item in items if item.status == "skipped_existing"
        )
        failed_count = sum(1 for item in items if item.status == "failed")
        report = MailboxImapBackfillSmokeReport(
            email_address=config.email_address,
            login_username_kind=successful_login_username_kind,
            auth_report_path=str(auth_report_path),
            success=failed_count == 0,
            selected_candidate=selected_candidate.to_dict(),
            folder=folder,
            total_message_count=len(uid_list),
            fetched_count=fetched_count,
            skipped_existing_count=skipped_existing_count,
            failed_count=failed_count,
            items=items,
            notes=notes,
        )
    except Exception as exc:
        report = MailboxImapBackfillSmokeReport(
            email_address=config.email_address,
            login_username_kind=successful_login_username_kind,
            auth_report_path=str(auth_report_path),
            success=False,
            selected_candidate=selected_candidate.to_dict(),
            folder=folder,
            failure_message=f"{exc.__class__.__name__}: {exc}",
            notes=notes,
        )
    finally:
        try:
            client.logout()
        except Exception:
            pass

    return save_imap_backfill_report(
        report,
        default_backfill_report_path(config.profile_root, config.email_address),
    )


def save_imap_backfill_report(
    report: MailboxImapBackfillSmokeReport,
    output_path: str | Path,
) -> MailboxImapBackfillSmokeReport:
    """기능: IMAP backfill smoke 결과를 JSON 파일로 저장한다."""

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(report.to_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return report


def _load_existing_imap_uid_index(profile_root: str) -> set[str]:
    """기능: 현재 프로필 아래 runtime bundle에서 이미 저장한 IMAP UID 집합을 읽는다."""

    existing_uids: set[str] = set()
    for bundle_root in list_valid_runtime_bundle_directories(profile_root):
        try:
            normalized = load_normalized_message_from_bundle(bundle_root)
        except Exception:
            continue
        if not any(label.startswith("imap_") for label in normalized.labels):
            continue
        message_key = (normalized.message_key or "").strip()
        if message_key.isdigit():
            existing_uids.add(message_key)
    return existing_uids


def _maybe_checkpoint_backfill_report(
    *,
    index: int,
    total_count: int,
    items: list[MailboxImapBackfillItemResult],
    email_address: str,
    login_username_kind: str,
    auth_report_path: str,
    selected_candidate: dict[str, object] | None,
    folder: str,
    notes: list[str],
    output_path: Path,
) -> None:
    """기능: 긴 backfill 실행 중 중간 checkpoint report를 주기적으로 저장한다."""

    if index % 100 != 0 and index != total_count:
        return

    fetched_count = sum(1 for item in items if item.status == "fetched")
    skipped_existing_count = sum(
        1 for item in items if item.status == "skipped_existing"
    )
    failed_count = sum(1 for item in items if item.status == "failed")
    checkpoint_report = MailboxImapBackfillSmokeReport(
        email_address=email_address,
        login_username_kind=login_username_kind,
        auth_report_path=auth_report_path,
        success=False,
        selected_candidate=selected_candidate,
        folder=folder,
        total_message_count=total_count,
        fetched_count=fetched_count,
        skipped_existing_count=skipped_existing_count,
        failed_count=failed_count,
        items=list(items),
        notes=list(notes)
        + [f"checkpoint_saved_after_{index}_items"],
    )
    save_imap_backfill_report(checkpoint_report, output_path)
    print(
        (
            f"[imap_backfill] {index}/{total_count} processed | "
            f"fetched={fetched_count} skipped={skipped_existing_count} failed={failed_count}"
        ),
        file=sys.stderr,
        flush=True,
    )


def _emit_backfill_progress(
    *,
    callback: ProgressCallback | None,
    processed_count: int,
    total_count: int,
    items: list[MailboxImapBackfillItemResult],
    latest_uid: str = "",
) -> None:
    if callback is None:
        return
    fetched_count = sum(1 for item in items if item.status == "fetched")
    skipped_existing_count = sum(1 for item in items if item.status == "skipped_existing")
    failed_count = sum(1 for item in items if item.status == "failed")
    callback(
        {
            "processed_count": processed_count,
            "total_count": total_count,
            "fetched_count": fetched_count,
            "skipped_existing_count": skipped_existing_count,
            "failed_count": failed_count,
            "latest_uid": latest_uid,
        }
    )


def _extract_fetched_message_snapshot(raw_bytes: bytes) -> dict[str, str]:
    message = BytesParser(policy=policy.default).parsebytes(raw_bytes)
    return {
        "subject": str(message.get("Subject") or "").strip(),
        "internet_message_id": str(message.get("Message-ID") or "").strip(),
    }


def main() -> None:
    """기능: CLI에서 실제 계정 IMAP backfill smoke를 실행한다."""

    parser = argparse.ArgumentParser(description="real account IMAP inbox backfill smoke")
    parser.add_argument(
        "--credentials-path",
        default=str(default_local_account_config_path()),
    )
    parser.add_argument("--profile-root", default=str(default_profile_root()))
    parser.add_argument("--folder", default="INBOX")
    parser.add_argument("--timeout-seconds", type=float, default=8.0)
    parser.add_argument("--max-probes-per-protocol", type=int, default=2)
    args = parser.parse_args()

    report = run_imap_inbox_backfill_smoke(
        credentials_path=args.credentials_path,
        profile_root=args.profile_root,
        folder=args.folder,
        timeout_seconds=args.timeout_seconds,
        max_probes_per_protocol=args.max_probes_per_protocol,
    )
    print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
    if not report.success:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
