"""공유 워크스페이스 review/sync 상태를 SQLite로 관리한다."""

from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
from typing import Any, Iterator


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class WorkspaceStateStore:
    """기능: 공유 워크스페이스의 review/sync 상태를 저장한다."""

    def __init__(self, db_path: str | Path) -> None:
        self.db_path = Path(db_path)

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        try:
            yield connection
            connection.commit()
        finally:
            connection.close()

    def ensure_schema(self) -> None:
        with self.connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS sync_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_kind TEXT NOT NULL,
                    app_kind TEXT NOT NULL,
                    started_at TEXT NOT NULL,
                    finished_at TEXT,
                    status TEXT NOT NULL,
                    notes_json TEXT NOT NULL DEFAULT '[]',
                    metadata_json TEXT NOT NULL DEFAULT '{}'
                );

                CREATE TABLE IF NOT EXISTS bundle_review_state (
                    bundle_id TEXT PRIMARY KEY,
                    received_at TEXT,
                    sender TEXT NOT NULL DEFAULT '',
                    subject TEXT NOT NULL DEFAULT '',
                    attachment_count INTEGER NOT NULL DEFAULT 0,
                    triage_label TEXT NOT NULL DEFAULT 'needs_human_review',
                    triage_reason TEXT NOT NULL DEFAULT '',
                    triage_confidence REAL,
                    analysis_source TEXT NOT NULL DEFAULT '',
                    export_status TEXT NOT NULL DEFAULT '',
                    company_name TEXT NOT NULL DEFAULT '',
                    contact_name TEXT NOT NULL DEFAULT '',
                    email_address TEXT NOT NULL DEFAULT '',
                    application_purpose TEXT NOT NULL DEFAULT '',
                    request_summary TEXT NOT NULL DEFAULT '',
                    unresolved_columns_json TEXT NOT NULL DEFAULT '[]',
                    notes_json TEXT NOT NULL DEFAULT '[]',
                    bundle_root_relpath TEXT NOT NULL,
                    raw_eml_relpath TEXT,
                    attachments_dir_relpath TEXT,
                    summary_relpath TEXT,
                    preview_relpath TEXT,
                    extracted_record_relpath TEXT,
                    projected_row_relpath TEXT,
                    dedupe_group_key TEXT,
                    is_export_representative INTEGER NOT NULL DEFAULT 0,
                    duplicate_of_bundle_id TEXT,
                    workbook_row_index INTEGER,
                    user_override_state TEXT NOT NULL DEFAULT '',
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS dedupe_groups (
                    dedupe_group_key TEXT PRIMARY KEY,
                    representative_bundle_id TEXT NOT NULL,
                    bundle_ids_json TEXT NOT NULL DEFAULT '[]',
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS representative_selection (
                    bundle_id TEXT PRIMARY KEY,
                    dedupe_group_key TEXT NOT NULL,
                    selection_source TEXT NOT NULL,
                    selected_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS user_overrides (
                    bundle_id TEXT PRIMARY KEY,
                    override_triage_label TEXT,
                    override_is_representative INTEGER,
                    override_notes TEXT NOT NULL DEFAULT '',
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS workbook_rows (
                    bundle_id TEXT PRIMARY KEY,
                    workbook_relpath TEXT NOT NULL,
                    sheet_name TEXT NOT NULL,
                    row_index INTEGER NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_bundle_review_state_triage
                ON bundle_review_state (triage_label, is_export_representative);
                """
            )

    def start_sync_run(
        self,
        *,
        run_kind: str,
        app_kind: str,
        metadata: dict[str, Any] | None = None,
    ) -> int:
        with self.connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO sync_runs (
                    run_kind, app_kind, started_at, status, notes_json, metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    run_kind,
                    app_kind,
                    utc_now_iso(),
                    "running",
                    "[]",
                    json.dumps(metadata or {}, ensure_ascii=False),
                ),
            )
            return int(cursor.lastrowid)

    def finish_sync_run(
        self,
        run_id: int,
        *,
        status: str,
        notes: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        with self.connect() as connection:
            connection.execute(
                """
                UPDATE sync_runs
                SET finished_at = ?, status = ?, notes_json = ?, metadata_json = ?
                WHERE id = ?
                """,
                (
                    utc_now_iso(),
                    status,
                    json.dumps(notes or [], ensure_ascii=False),
                    json.dumps(metadata or {}, ensure_ascii=False),
                    run_id,
                ),
            )

    def replace_review_items(self, items: list[dict[str, Any]]) -> None:
        with self.connect() as connection:
            connection.execute("DELETE FROM bundle_review_state")
            for item in items:
                connection.execute(
                    """
                    INSERT INTO bundle_review_state (
                        bundle_id, received_at, sender, subject, attachment_count,
                        triage_label, triage_reason, triage_confidence, analysis_source,
                        export_status, company_name, contact_name, email_address,
                        application_purpose, request_summary, unresolved_columns_json,
                        notes_json, bundle_root_relpath, raw_eml_relpath,
                        attachments_dir_relpath, summary_relpath, preview_relpath,
                        extracted_record_relpath, projected_row_relpath, dedupe_group_key,
                        is_export_representative, duplicate_of_bundle_id,
                        workbook_row_index, user_override_state, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(bundle_id) DO UPDATE SET
                        received_at = excluded.received_at,
                        sender = excluded.sender,
                        subject = excluded.subject,
                        attachment_count = excluded.attachment_count,
                        triage_label = excluded.triage_label,
                        triage_reason = excluded.triage_reason,
                        triage_confidence = excluded.triage_confidence,
                        analysis_source = excluded.analysis_source,
                        export_status = excluded.export_status,
                        company_name = excluded.company_name,
                        contact_name = excluded.contact_name,
                        email_address = excluded.email_address,
                        application_purpose = excluded.application_purpose,
                        request_summary = excluded.request_summary,
                        unresolved_columns_json = excluded.unresolved_columns_json,
                        notes_json = excluded.notes_json,
                        bundle_root_relpath = excluded.bundle_root_relpath,
                        raw_eml_relpath = excluded.raw_eml_relpath,
                        attachments_dir_relpath = excluded.attachments_dir_relpath,
                        summary_relpath = excluded.summary_relpath,
                        preview_relpath = excluded.preview_relpath,
                        extracted_record_relpath = excluded.extracted_record_relpath,
                        projected_row_relpath = excluded.projected_row_relpath,
                        dedupe_group_key = excluded.dedupe_group_key,
                        is_export_representative = excluded.is_export_representative,
                        duplicate_of_bundle_id = excluded.duplicate_of_bundle_id,
                        workbook_row_index = excluded.workbook_row_index,
                        user_override_state = excluded.user_override_state,
                        updated_at = excluded.updated_at
                    """,
                    (
                        item["bundle_id"],
                        item.get("received_at"),
                        item.get("sender") or "",
                        item.get("subject") or "",
                        int(item.get("attachment_count") or 0),
                        item.get("triage_label") or "needs_human_review",
                        item.get("triage_reason") or "",
                        item.get("triage_confidence"),
                        item.get("analysis_source") or "",
                        item.get("export_status") or "",
                        item.get("company_name") or "",
                        item.get("contact_name") or "",
                        item.get("email_address") or "",
                        item.get("application_purpose") or "",
                        item.get("request_summary") or "",
                        json.dumps(item.get("unresolved_columns") or [], ensure_ascii=False),
                        json.dumps(item.get("notes") or [], ensure_ascii=False),
                        item["bundle_root_relpath"],
                        item.get("raw_eml_relpath"),
                        item.get("attachments_dir_relpath"),
                        item.get("summary_relpath"),
                        item.get("preview_relpath"),
                        item.get("extracted_record_relpath"),
                        item.get("projected_row_relpath"),
                        item.get("dedupe_group_key"),
                        1 if item.get("is_export_representative") else 0,
                        item.get("duplicate_of_bundle_id"),
                        item.get("workbook_row_index"),
                        item.get("user_override_state") or "",
                        item.get("updated_at") or utc_now_iso(),
                    ),
                )

    def replace_dedupe_groups(self, groups: list[dict[str, Any]]) -> None:
        with self.connect() as connection:
            connection.execute("DELETE FROM dedupe_groups")
            connection.execute("DELETE FROM representative_selection")
            for group in groups:
                connection.execute(
                    """
                    INSERT INTO dedupe_groups (
                        dedupe_group_key, representative_bundle_id, bundle_ids_json, updated_at
                    ) VALUES (?, ?, ?, ?)
                    """,
                    (
                        group["dedupe_group_key"],
                        group["representative_bundle_id"],
                        json.dumps(group.get("bundle_ids") or [], ensure_ascii=False),
                        utc_now_iso(),
                    ),
                )
                connection.execute(
                    """
                    INSERT INTO representative_selection (
                        bundle_id, dedupe_group_key, selection_source, selected_at
                    ) VALUES (?, ?, ?, ?)
                    """,
                    (
                        group["representative_bundle_id"],
                        group["dedupe_group_key"],
                        group.get("selection_source") or "heuristic_latest",
                        utc_now_iso(),
                    ),
                )

    def save_user_override(
        self,
        *,
        bundle_id: str,
        override_triage_label: str | None = None,
        override_is_representative: bool | None = None,
        override_notes: str = "",
    ) -> None:
        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO user_overrides (
                    bundle_id, override_triage_label, override_is_representative,
                    override_notes, updated_at
                ) VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(bundle_id) DO UPDATE SET
                    override_triage_label = excluded.override_triage_label,
                    override_is_representative = excluded.override_is_representative,
                    override_notes = excluded.override_notes,
                    updated_at = excluded.updated_at
                """,
                (
                    bundle_id,
                    override_triage_label,
                    None if override_is_representative is None else int(override_is_representative),
                    override_notes,
                    utc_now_iso(),
                ),
            )

    def load_user_overrides(self) -> dict[str, dict[str, Any]]:
        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT bundle_id, override_triage_label, override_is_representative, override_notes
                FROM user_overrides
                """
            ).fetchall()
        return {
            str(row["bundle_id"]): {
                "override_triage_label": row["override_triage_label"],
                "override_is_representative": (
                    None if row["override_is_representative"] is None else bool(row["override_is_representative"])
                ),
                "override_notes": row["override_notes"] or "",
            }
            for row in rows
        }

    def save_workbook_rows(
        self,
        *,
        workbook_relpath: str,
        row_items: list[dict[str, Any]],
    ) -> None:
        with self.connect() as connection:
            connection.execute(
                "UPDATE bundle_review_state SET workbook_row_index = NULL, updated_at = ?",
                (utc_now_iso(),),
            )
            connection.execute("DELETE FROM workbook_rows")
            for item in row_items:
                connection.execute(
                    """
                    INSERT INTO workbook_rows (
                        bundle_id, workbook_relpath, sheet_name, row_index, updated_at
                    ) VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        item["bundle_id"],
                        workbook_relpath,
                        item["sheet_name"],
                        int(item["row_index"]),
                        utc_now_iso(),
                    ),
                )
                connection.execute(
                    """
                    UPDATE bundle_review_state
                    SET workbook_row_index = ?, updated_at = ?
                    WHERE bundle_id = ?
                    """,
                    (int(item["row_index"]), utc_now_iso(), item["bundle_id"]),
                )

    def clear_workbook_rows(self) -> None:
        with self.connect() as connection:
            connection.execute("DELETE FROM workbook_rows")
            connection.execute(
                "UPDATE bundle_review_state SET workbook_row_index = NULL, updated_at = ?",
                (utc_now_iso(),),
            )

    def list_review_items(
        self,
        *,
        search: str = "",
        triage_label: str = "",
        export_only: bool = False,
        include_duplicates: bool = True,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        query = [
            "SELECT * FROM bundle_review_state WHERE 1=1",
        ]
        params: list[Any] = []
        if search.strip():
            query.append(
                "AND (subject LIKE ? OR sender LIKE ? OR company_name LIKE ?)"
            )
            pattern = f"%{search.strip()}%"
            params.extend([pattern, pattern, pattern])
        if triage_label.strip():
            query.append("AND triage_label = ?")
            params.append(triage_label.strip())
        if export_only:
            query.append("AND is_export_representative = 1")
        if not include_duplicates:
            query.append("AND duplicate_of_bundle_id IS NULL")
        query.append("ORDER BY COALESCE(received_at, '') DESC, bundle_id DESC")
        if limit is not None:
            query.append("LIMIT ?")
            params.append(limit)

        sql = " ".join(query)
        with self.connect() as connection:
            rows = connection.execute(sql, params).fetchall()
        return [self._row_to_review_item(row) for row in rows]

    def summary_counts(self) -> dict[str, int]:
        with self.connect() as connection:
            total = int(
                connection.execute("SELECT COUNT(*) FROM bundle_review_state").fetchone()[0]
            )
            application = int(
                connection.execute(
                    "SELECT COUNT(*) FROM bundle_review_state WHERE triage_label = 'application'"
                ).fetchone()[0]
            )
            not_application = int(
                connection.execute(
                    "SELECT COUNT(*) FROM bundle_review_state WHERE triage_label = 'not_application'"
                ).fetchone()[0]
            )
            needs_human_review = int(
                connection.execute(
                    "SELECT COUNT(*) FROM bundle_review_state WHERE triage_label = 'needs_human_review'"
                ).fetchone()[0]
            )
            duplicate_application = int(
                connection.execute(
                    """
                    SELECT COUNT(*) FROM bundle_review_state
                    WHERE triage_label = 'application' AND duplicate_of_bundle_id IS NOT NULL
                    """
                ).fetchone()[0]
            )
            representatives = int(
                connection.execute(
                    "SELECT COUNT(*) FROM bundle_review_state WHERE is_export_representative = 1"
                ).fetchone()[0]
            )
        return {
            "total": total,
            "application": application,
            "not_application": not_application,
            "needs_human_review": needs_human_review,
            "duplicate_application": duplicate_application,
            "representative_application": representatives,
        }

    def latest_sync_run(self) -> dict[str, Any] | None:
        with self.connect() as connection:
            row = connection.execute(
                """
                SELECT id, run_kind, app_kind, started_at, finished_at, status, notes_json, metadata_json
                FROM sync_runs
                ORDER BY id DESC
                LIMIT 1
                """
            ).fetchone()
        if row is None:
            return None
        return {
            "id": int(row["id"]),
            "run_kind": row["run_kind"],
            "app_kind": row["app_kind"],
            "started_at": row["started_at"],
            "finished_at": row["finished_at"],
            "status": row["status"],
            "notes": json.loads(row["notes_json"] or "[]"),
            "metadata": json.loads(row["metadata_json"] or "{}"),
        }

    def _row_to_review_item(self, row: sqlite3.Row) -> dict[str, Any]:
        return {
            "bundle_id": row["bundle_id"],
            "received_at": row["received_at"],
            "sender": row["sender"],
            "subject": row["subject"],
            "attachment_count": int(row["attachment_count"] or 0),
            "triage_label": row["triage_label"],
            "triage_reason": row["triage_reason"],
            "triage_confidence": row["triage_confidence"],
            "analysis_source": row["analysis_source"],
            "export_status": row["export_status"],
            "company_name": row["company_name"],
            "contact_name": row["contact_name"],
            "email_address": row["email_address"],
            "application_purpose": row["application_purpose"],
            "request_summary": row["request_summary"],
            "unresolved_columns": json.loads(row["unresolved_columns_json"] or "[]"),
            "notes": json.loads(row["notes_json"] or "[]"),
            "bundle_root_relpath": row["bundle_root_relpath"],
            "raw_eml_relpath": row["raw_eml_relpath"],
            "attachments_dir_relpath": row["attachments_dir_relpath"],
            "summary_relpath": row["summary_relpath"],
            "preview_relpath": row["preview_relpath"],
            "extracted_record_relpath": row["extracted_record_relpath"],
            "projected_row_relpath": row["projected_row_relpath"],
            "dedupe_group_key": row["dedupe_group_key"],
            "is_export_representative": bool(row["is_export_representative"]),
            "duplicate_of_bundle_id": row["duplicate_of_bundle_id"],
            "workbook_row_index": row["workbook_row_index"],
            "user_override_state": row["user_override_state"] or "",
        }
