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

                CREATE TABLE IF NOT EXISTS feature_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    feature_id TEXT NOT NULL,
                    app_kind TEXT NOT NULL,
                    trigger_source TEXT NOT NULL DEFAULT '',
                    started_at TEXT NOT NULL,
                    finished_at TEXT,
                    status TEXT NOT NULL,
                    metadata_json TEXT NOT NULL DEFAULT '{}',
                    outputs_json TEXT NOT NULL DEFAULT '{}',
                    notes_json TEXT NOT NULL DEFAULT '[]',
                    error_summary TEXT NOT NULL DEFAULT ''
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
                    application_group_id TEXT,
                    canonical_bundle_id TEXT,
                    included_in_export INTEGER NOT NULL DEFAULT 0,
                    canonical_selection_reason TEXT NOT NULL DEFAULT '',
                    canonical_selection_confidence REAL,
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
                """
            )
            bundle_review_columns = [
                ("raw_eml_relpath", "TEXT"),
                ("attachments_dir_relpath", "TEXT"),
                ("summary_relpath", "TEXT"),
                ("preview_relpath", "TEXT"),
                ("extracted_record_relpath", "TEXT"),
                ("projected_row_relpath", "TEXT"),
                ("application_group_id", "TEXT"),
                ("canonical_bundle_id", "TEXT"),
                ("included_in_export", "INTEGER NOT NULL DEFAULT 0"),
                ("canonical_selection_reason", "TEXT NOT NULL DEFAULT ''"),
                ("canonical_selection_confidence", "REAL"),
                ("dedupe_group_key", "TEXT"),
                ("is_export_representative", "INTEGER NOT NULL DEFAULT 0"),
                ("duplicate_of_bundle_id", "TEXT"),
                ("workbook_row_index", "INTEGER"),
                ("user_override_state", "TEXT NOT NULL DEFAULT ''"),
            ]
            for column_name, column_definition in bundle_review_columns:
                self._ensure_column(
                    connection,
                    table_name="bundle_review_state",
                    column_name=column_name,
                    column_definition=column_definition,
                )
            feature_run_columns = [
                ("trigger_source", "TEXT NOT NULL DEFAULT ''"),
                ("outputs_json", "TEXT NOT NULL DEFAULT '{}'"),
                ("error_summary", "TEXT NOT NULL DEFAULT ''"),
            ]
            for column_name, column_definition in feature_run_columns:
                self._ensure_column(
                    connection,
                    table_name="feature_runs",
                    column_name=column_name,
                    column_definition=column_definition,
                )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_bundle_review_state_triage
                ON bundle_review_state (triage_label, is_export_representative)
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_bundle_review_state_received
                ON bundle_review_state (received_at DESC, bundle_id DESC)
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_bundle_review_state_company
                ON bundle_review_state (company_name COLLATE NOCASE, received_at DESC, bundle_id DESC)
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_bundle_review_state_sender
                ON bundle_review_state (sender COLLATE NOCASE, received_at DESC, bundle_id DESC)
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_bundle_review_state_group
                ON bundle_review_state (application_group_id, included_in_export)
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_bundle_review_state_export
                ON bundle_review_state (triage_label, included_in_export)
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_feature_runs_feature
                ON feature_runs (feature_id, id DESC)
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

    def start_feature_run(
        self,
        *,
        feature_id: str,
        app_kind: str,
        trigger_source: str,
        metadata: dict[str, Any] | None = None,
    ) -> int:
        with self.connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO feature_runs (
                    feature_id, app_kind, trigger_source, started_at, status, metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    feature_id,
                    app_kind,
                    trigger_source,
                    utc_now_iso(),
                    "running",
                    json.dumps(metadata or {}, ensure_ascii=False),
                ),
            )
            return int(cursor.lastrowid)

    def finish_feature_run(
        self,
        run_id: int,
        *,
        status: str,
        outputs: dict[str, Any] | None = None,
        notes: list[str] | None = None,
        error_summary: str = "",
    ) -> None:
        with self.connect() as connection:
            connection.execute(
                """
                UPDATE feature_runs
                SET finished_at = ?, status = ?, outputs_json = ?, notes_json = ?, error_summary = ?
                WHERE id = ?
                """,
                (
                    utc_now_iso(),
                    status,
                    json.dumps(outputs or {}, ensure_ascii=False),
                    json.dumps(notes or [], ensure_ascii=False),
                    error_summary,
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
                        extracted_record_relpath, projected_row_relpath, application_group_id,
                        canonical_bundle_id, included_in_export, canonical_selection_reason,
                        canonical_selection_confidence, dedupe_group_key,
                        is_export_representative, duplicate_of_bundle_id,
                        workbook_row_index, user_override_state, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                        application_group_id = excluded.application_group_id,
                        canonical_bundle_id = excluded.canonical_bundle_id,
                        included_in_export = excluded.included_in_export,
                        canonical_selection_reason = excluded.canonical_selection_reason,
                        canonical_selection_confidence = excluded.canonical_selection_confidence,
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
                        item.get("application_group_id"),
                        item.get("canonical_bundle_id"),
                        1 if item.get("included_in_export") else 0,
                        item.get("canonical_selection_reason") or "",
                        item.get("canonical_selection_confidence"),
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
        offset: int = 0,
        sort: str = "received_desc",
    ) -> list[dict[str, Any]]:
        query, params = self._build_review_items_query(
            search=search,
            triage_label=triage_label,
            export_only=export_only,
            include_duplicates=include_duplicates,
        )
        query.append(self._review_sort_clause(sort))
        if limit is not None:
            query.append("LIMIT ?")
            params.append(limit)
        if offset > 0:
            query.append("OFFSET ?")
            params.append(offset)

        sql = " ".join(query)
        with self.connect() as connection:
            rows = connection.execute(sql, params).fetchall()
        return [self._row_to_review_item(row) for row in rows]

    def list_review_page_items(
        self,
        *,
        search: str = "",
        triage_label: str = "",
        export_only: bool = False,
        include_duplicates: bool = True,
        limit: int | None = None,
        offset: int = 0,
        sort: str = "received_desc",
    ) -> list[dict[str, Any]]:
        query, params = self._build_review_items_query(
            search=search,
            triage_label=triage_label,
            export_only=export_only,
            include_duplicates=include_duplicates,
            select_clause=(
                "SELECT bundle_id, received_at, sender, subject, triage_label, "
                "export_status, company_name, included_in_export, workbook_row_index, "
                "unresolved_columns_json FROM bundle_review_state WHERE 1=1"
            ),
        )
        query.append(self._review_sort_clause(sort))
        if limit is not None:
            query.append("LIMIT ?")
            params.append(limit)
        if offset > 0:
            query.append("OFFSET ?")
            params.append(offset)
        sql = " ".join(query)
        with self.connect() as connection:
            rows = connection.execute(sql, params).fetchall()
        return [self._row_to_review_list_item(row) for row in rows]

    def count_review_items(
        self,
        *,
        search: str = "",
        triage_label: str = "",
        export_only: bool = False,
        include_duplicates: bool = True,
    ) -> int:
        query, params = self._build_review_items_query(
            search=search,
            triage_label=triage_label,
            export_only=export_only,
            include_duplicates=include_duplicates,
            select_clause="SELECT COUNT(*) FROM bundle_review_state WHERE 1=1",
        )
        sql = " ".join(query)
        with self.connect() as connection:
            return int(connection.execute(sql, params).fetchone()[0])

    def get_review_item(self, bundle_id: str) -> dict[str, Any] | None:
        with self.connect() as connection:
            row = connection.execute(
                "SELECT * FROM bundle_review_state WHERE bundle_id = ?",
                (bundle_id,),
            ).fetchone()
        if row is None:
            return None
        return self._row_to_review_item(row)

    def summary_counts(self) -> dict[str, int]:
        with self.connect() as connection:
            row = connection.execute(
                """
                SELECT
                    COUNT(*) AS total,
                    SUM(CASE WHEN triage_label = 'application' THEN 1 ELSE 0 END) AS application,
                    SUM(CASE WHEN triage_label = 'not_application' THEN 1 ELSE 0 END) AS not_application,
                    SUM(CASE WHEN triage_label = 'needs_human_review' THEN 1 ELSE 0 END) AS needs_human_review,
                    SUM(CASE WHEN triage_label = 'application' AND included_in_export = 1 THEN 1 ELSE 0 END) AS export_included,
                    SUM(CASE WHEN triage_label = 'application' AND included_in_export = 0 THEN 1 ELSE 0 END) AS held_application,
                    SUM(CASE WHEN analysis_source = 'failed_before_analysis' THEN 1 ELSE 0 END) AS failed_before_analysis
                FROM bundle_review_state
                """
            ).fetchone()
        return {
            "total": int(row["total"] or 0),
            "application": int(row["application"] or 0),
            "not_application": int(row["not_application"] or 0),
            "needs_human_review": int(row["needs_human_review"] or 0),
            "export_included_application": int(row["export_included"] or 0),
            "held_application": int(row["held_application"] or 0),
            "failed_before_analysis": int(row["failed_before_analysis"] or 0),
        }

    def _build_review_items_query(
        self,
        *,
        search: str = "",
        triage_label: str = "",
        export_only: bool = False,
        include_duplicates: bool = True,
        select_clause: str = "SELECT * FROM bundle_review_state WHERE 1=1",
    ) -> tuple[list[str], list[Any]]:
        query = [select_clause]
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
            query.append("AND included_in_export = 1")
        if not include_duplicates:
            query.append("AND included_in_export = 1")
        return query, params

    def _review_sort_clause(self, sort: str) -> str:
        normalized = (sort or "received_desc").strip().lower()
        if normalized == "company_asc":
            return "ORDER BY LOWER(COALESCE(company_name, '')), COALESCE(received_at, '') DESC, bundle_id DESC"
        if normalized == "sender_asc":
            return "ORDER BY LOWER(COALESCE(sender, '')), COALESCE(received_at, '') DESC, bundle_id DESC"
        return "ORDER BY COALESCE(received_at, '') DESC, bundle_id DESC"

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

    def latest_feature_runs(self) -> list[dict[str, Any]]:
        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT fr.*
                FROM feature_runs fr
                INNER JOIN (
                    SELECT feature_id, MAX(id) AS max_id
                    FROM feature_runs
                    GROUP BY feature_id
                ) latest
                ON latest.feature_id = fr.feature_id
                AND latest.max_id = fr.id
                ORDER BY fr.feature_id ASC
                """
            ).fetchall()
        return [self._row_to_feature_run(row) for row in rows]

    def feature_run_history(
        self,
        *,
        feature_id: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        query = [
            "SELECT * FROM feature_runs WHERE 1=1",
        ]
        params: list[Any] = []
        if feature_id:
            query.append("AND feature_id = ?")
            params.append(feature_id)
        query.append("ORDER BY id DESC LIMIT ?")
        params.append(limit)
        sql = " ".join(query)
        with self.connect() as connection:
            rows = connection.execute(sql, params).fetchall()
        return [self._row_to_feature_run(row) for row in rows]

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
            "application_group_id": row["application_group_id"],
            "canonical_bundle_id": row["canonical_bundle_id"],
            "included_in_export": bool(row["included_in_export"]),
            "canonical_selection_reason": row["canonical_selection_reason"] or "",
            "canonical_selection_confidence": row["canonical_selection_confidence"],
            "dedupe_group_key": row["dedupe_group_key"],
            "is_export_representative": bool(row["is_export_representative"]),
            "duplicate_of_bundle_id": row["duplicate_of_bundle_id"],
            "workbook_row_index": row["workbook_row_index"],
            "user_override_state": row["user_override_state"] or "",
        }

    def _row_to_review_list_item(self, row: sqlite3.Row) -> dict[str, Any]:
        unresolved_columns = json.loads(row["unresolved_columns_json"] or "[]")
        return {
            "bundle_id": row["bundle_id"],
            "received_at": row["received_at"],
            "sender": row["sender"],
            "subject": row["subject"],
            "triage_label": row["triage_label"],
            "export_status": row["export_status"],
            "company_name": row["company_name"],
            "included_in_export": bool(row["included_in_export"]),
            "workbook_row_index": row["workbook_row_index"],
            "unresolved_columns": unresolved_columns,
            "unresolved_count": len(unresolved_columns),
        }

    def _ensure_column(
        self,
        connection: sqlite3.Connection,
        *,
        table_name: str,
        column_name: str,
        column_definition: str,
    ) -> None:
        rows = connection.execute(f"PRAGMA table_info({table_name})").fetchall()
        if any(str(row["name"]) == column_name for row in rows):
            return
        connection.execute(
            f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_definition}"
        )

    def _row_to_feature_run(self, row: sqlite3.Row) -> dict[str, Any]:
        return {
            "id": int(row["id"]),
            "feature_id": row["feature_id"],
            "app_kind": row["app_kind"],
            "trigger_source": row["trigger_source"],
            "started_at": row["started_at"],
            "finished_at": row["finished_at"],
            "status": row["status"],
            "metadata": json.loads(row["metadata_json"] or "{}"),
            "outputs": json.loads(row["outputs_json"] or "{}"),
            "notes": json.loads(row["notes_json"] or "[]"),
            "error_summary": row["error_summary"] or "",
        }
