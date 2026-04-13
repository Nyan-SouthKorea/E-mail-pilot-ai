"""review board 결과를 공유 워크스페이스 상태로 정리한다."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import json
from pathlib import Path
import re
from typing import Any

from runtime.state_store import WorkspaceStateStore
from runtime.workspace import SharedWorkspace


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


_CORPORATE_MARKERS = [
    "(주)",
    "주식회사",
    "inc.",
    "inc",
    "ltd.",
    "ltd",
    "corp.",
    "corp",
    "co.,ltd.",
    "co., ltd.",
]


@dataclass(slots=True)
class WorkspaceReviewItem:
    """기능: 공유 워크스페이스에 저장할 review item을 표현한다."""

    bundle_id: str
    bundle_root_relpath: str
    received_at: str | None
    sender: str
    subject: str
    attachment_count: int
    triage_label: str
    triage_reason: str
    triage_confidence: float | None
    analysis_source: str
    export_status: str
    company_name: str = ""
    contact_name: str = ""
    email_address: str = ""
    application_purpose: str = ""
    request_summary: str = ""
    unresolved_columns: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    summary_relpath: str | None = None
    preview_relpath: str | None = None
    extracted_record_relpath: str | None = None
    projected_row_relpath: str | None = None
    raw_eml_relpath: str | None = None
    attachments_dir_relpath: str | None = None
    dedupe_group_key: str | None = None
    is_export_representative: bool = False
    duplicate_of_bundle_id: str | None = None
    workbook_row_index: int | None = None
    user_override_state: str = ""
    updated_at: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def ingest_review_report_into_state(
    *,
    workspace: SharedWorkspace,
    state_store: WorkspaceStateStore,
    report_path: str | Path,
) -> list[WorkspaceReviewItem]:
    """기능: 최신 review report를 읽어 state DB의 canonical review 상태로 반영한다."""

    payload = json.loads(Path(report_path).read_text(encoding="utf-8"))
    items = [
        _workspace_item_from_report_entry(
            workspace=workspace,
            entry=item_payload,
        )
        for item_payload in (payload.get("items") or [])
    ]

    overrides = state_store.load_user_overrides()
    _apply_user_overrides(items, overrides)
    groups = _apply_application_dedupe(items, overrides)

    state_store.replace_review_items([item.to_dict() for item in items])
    state_store.replace_dedupe_groups(groups)
    return items


def normalize_company_name(company_name: str) -> str:
    """기능: dedupe용 회사명 정규화 key를 만든다."""

    text = company_name.strip().casefold()
    for marker in _CORPORATE_MARKERS:
        text = text.replace(marker.casefold(), " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _workspace_item_from_report_entry(
    *,
    workspace: SharedWorkspace,
    entry: dict[str, Any],
) -> WorkspaceReviewItem:
    bundle_id = str(entry["bundle_id"])
    bundle_root_relpath = _resolve_item_relative_path(
        workspace=workspace,
        maybe_path=entry.get("bundle_root"),
        fallback=workspace.profile_paths().runtime_mail_bundles_root().relative_to(workspace.root()) / bundle_id,
    )
    bundle_root_path = Path(bundle_root_relpath)

    return WorkspaceReviewItem(
        bundle_id=bundle_id,
        bundle_root_relpath=bundle_root_relpath,
        received_at=entry.get("received_at"),
        sender=str(entry.get("sender") or ""),
        subject=str(entry.get("subject") or ""),
        attachment_count=int(entry.get("attachment_count") or 0),
        triage_label=str(entry.get("triage_label") or "needs_human_review"),
        triage_reason=str(entry.get("triage_reason") or ""),
        triage_confidence=entry.get("triage_confidence"),
        analysis_source=str(entry.get("analysis_source") or ""),
        export_status=str(entry.get("export_status") or ""),
        company_name=str(entry.get("company_name") or ""),
        contact_name=str(entry.get("contact_name") or ""),
        email_address=str(entry.get("email_address") or ""),
        application_purpose=str(entry.get("application_purpose") or ""),
        request_summary=str(entry.get("request_summary") or ""),
        unresolved_columns=list(entry.get("unresolved_columns") or []),
        notes=list(entry.get("notes") or []),
        summary_relpath=_resolve_item_relative_path(
            workspace=workspace,
            maybe_path=entry.get("summary_path"),
            fallback=bundle_root_path / "summary.md",
        ),
        preview_relpath=_resolve_item_relative_path(
            workspace=workspace,
            maybe_path=entry.get("preview_path"),
            fallback=bundle_root_path / "preview.html",
        ),
        extracted_record_relpath=_resolve_item_relative_path(
            workspace=workspace,
            maybe_path=entry.get("extracted_record_path"),
            fallback=workspace.profile_paths().runtime_analysis_logs_root().relative_to(workspace.root())
            / f"{bundle_id}_extracted_record.json",
        ),
        projected_row_relpath=_resolve_item_relative_path(
            workspace=workspace,
            maybe_path=entry.get("projected_row_path"),
            fallback=workspace.profile_paths().runtime_exports_logs_root().relative_to(workspace.root())
            / f"{bundle_id}_projected_row.json",
        ),
        raw_eml_relpath=(bundle_root_path / "raw.eml").as_posix(),
        attachments_dir_relpath=(bundle_root_path / "attachments").as_posix(),
    )


def _resolve_item_relative_path(
    *,
    workspace: SharedWorkspace,
    maybe_path: str | Path | None,
    fallback: str | Path,
) -> str:
    if maybe_path:
        candidate = Path(maybe_path)
        if candidate.is_absolute():
            try:
                return workspace.to_workspace_relative(candidate)
            except Exception:
                return Path(fallback).as_posix()
        return candidate.as_posix()
    return Path(fallback).as_posix()


def _apply_user_overrides(
    items: list[WorkspaceReviewItem],
    overrides: dict[str, dict[str, Any]],
) -> None:
    for item in items:
        override = overrides.get(item.bundle_id)
        if override is None:
            continue
        states: list[str] = []
        triage_label = override.get("override_triage_label")
        if triage_label:
            item.triage_label = str(triage_label)
            states.append("triage_override")
        if override.get("override_is_representative") is not None:
            states.append("representative_override")
        item.user_override_state = ",".join(states)
        override_notes = str(override.get("override_notes") or "").strip()
        if override_notes:
            item.notes.append(f"user_override: {override_notes}")


def _apply_application_dedupe(
    items: list[WorkspaceReviewItem],
    overrides: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    for item in items:
        item.dedupe_group_key = None
        item.is_export_representative = False
        item.duplicate_of_bundle_id = None

    grouped: dict[str, list[WorkspaceReviewItem]] = {}
    for item in items:
        if item.triage_label != "application":
            continue
        dedupe_group_key = normalize_company_name(item.company_name)
        if not dedupe_group_key:
            continue
        item.dedupe_group_key = dedupe_group_key
        grouped.setdefault(dedupe_group_key, []).append(item)

    groups: list[dict[str, Any]] = []
    for dedupe_group_key, group_items in grouped.items():
        representative = _choose_representative(group_items, overrides)
        representative.is_export_representative = True
        representative.export_status = "exported_representative"
        for item in group_items:
            if item.bundle_id == representative.bundle_id:
                continue
            item.duplicate_of_bundle_id = representative.bundle_id
            item.export_status = "duplicate_application"
        groups.append(
            {
                "dedupe_group_key": dedupe_group_key,
                "representative_bundle_id": representative.bundle_id,
                "bundle_ids": [item.bundle_id for item in group_items],
                "selection_source": "user_override"
                if overrides.get(representative.bundle_id, {}).get("override_is_representative")
                else "heuristic_latest",
            }
        )
    return groups


def _choose_representative(
    group_items: list[WorkspaceReviewItem],
    overrides: dict[str, dict[str, Any]],
) -> WorkspaceReviewItem:
    explicit = [
        item
        for item in group_items
        if overrides.get(item.bundle_id, {}).get("override_is_representative") is True
    ]
    if explicit:
        return explicit[0]

    return sorted(
        group_items,
        key=lambda item: (
            item.received_at or "",
            _field_completeness_score(item),
            item.attachment_count,
            item.bundle_id,
        ),
        reverse=True,
    )[0]


def _field_completeness_score(item: WorkspaceReviewItem) -> int:
    return sum(
        1
        for value in [
            item.company_name,
            item.contact_name,
            item.email_address,
            item.application_purpose,
            item.request_summary,
        ]
        if value.strip()
    )
