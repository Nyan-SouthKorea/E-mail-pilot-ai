"""review board 결과를 공유 워크스페이스 상태로 정리한다."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import json
from pathlib import Path
import re
from typing import Any

from llm import OpenAIResponsesWrapper
from mailbox.bundle_reader import load_normalized_message_from_bundle
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
    application_group_id: str | None = None
    canonical_bundle_id: str | None = None
    included_in_export: bool = False
    canonical_selection_reason: str = ""
    canonical_selection_confidence: float | None = None
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
    wrapper: OpenAIResponsesWrapper | None = None,
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
    groups = _apply_application_canonical_selection(
        workspace=workspace,
        items=items,
        overrides=overrides,
        wrapper=wrapper,
    )

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


def _apply_application_canonical_selection(
    *,
    workspace: SharedWorkspace,
    items: list[WorkspaceReviewItem],
    overrides: dict[str, dict[str, Any]],
    wrapper: OpenAIResponsesWrapper | None,
) -> list[dict[str, Any]]:
    for item in items:
        item.application_group_id = None
        item.canonical_bundle_id = None
        item.included_in_export = False
        item.canonical_selection_reason = ""
        item.canonical_selection_confidence = None
        item.dedupe_group_key = None
        item.is_export_representative = False
        item.duplicate_of_bundle_id = None

    grouped: dict[str, list[tuple[WorkspaceReviewItem, dict[str, Any]]]] = {}
    for item in items:
        if item.triage_label != "application":
            continue
        candidate_context = _build_canonical_candidate_context(
            workspace=workspace,
            item=item,
        )
        application_group_id = _build_application_group_id(
            item=item,
            candidate_context=candidate_context,
        )
        if not application_group_id:
            continue
        item.application_group_id = application_group_id
        item.dedupe_group_key = application_group_id
        grouped.setdefault(application_group_id, []).append((item, candidate_context))

    groups: list[dict[str, Any]] = []
    for application_group_id, grouped_candidates in grouped.items():
        group_items = [item for item, _ in grouped_candidates]
        canonical_item, selection_source, selection_reason, selection_confidence = _choose_canonical_item(
            group_items=group_items,
            grouped_candidates=grouped_candidates,
            overrides=overrides,
            wrapper=wrapper,
        )
        canonical_item.canonical_bundle_id = canonical_item.bundle_id
        canonical_item.included_in_export = True
        canonical_item.is_export_representative = True
        canonical_item.export_status = "엑셀 반영됨"
        canonical_item.canonical_selection_reason = selection_reason
        canonical_item.canonical_selection_confidence = selection_confidence

        for item in group_items:
            item.canonical_bundle_id = canonical_item.bundle_id
            item.application_group_id = application_group_id
            item.dedupe_group_key = application_group_id
            if item.bundle_id == canonical_item.bundle_id:
                continue
            item.included_in_export = False
            item.duplicate_of_bundle_id = canonical_item.bundle_id
            item.export_status = "보류"
            item.canonical_selection_reason = selection_reason
            item.canonical_selection_confidence = selection_confidence
        groups.append(
            {
                "dedupe_group_key": application_group_id,
                "representative_bundle_id": canonical_item.bundle_id,
                "bundle_ids": [item.bundle_id for item in group_items],
                "selection_source": selection_source,
            }
        )
    return groups


def _choose_canonical_item(
    *,
    group_items: list[WorkspaceReviewItem],
    grouped_candidates: list[tuple[WorkspaceReviewItem, dict[str, Any]]],
    overrides: dict[str, dict[str, Any]],
    wrapper: OpenAIResponsesWrapper | None,
) -> tuple[WorkspaceReviewItem, str, str, float | None]:
    explicit = [
        item
        for item in group_items
        if overrides.get(item.bundle_id, {}).get("override_is_representative") is True
    ]
    if explicit:
        return explicit[0], "user_override", "사용자 override로 엑셀 반영 대상을 유지했습니다.", 1.0

    if wrapper is not None and getattr(wrapper.config, "api_key", "") and len(group_items) > 1:
        llm_choice = _choose_canonical_with_llm(
            grouped_candidates=grouped_candidates,
            wrapper=wrapper,
        )
        if llm_choice is not None:
            return llm_choice

    chosen = sorted(
        group_items,
        key=lambda item: (
            item.received_at or "",
            _field_completeness_score(item),
            item.attachment_count,
            item.bundle_id,
        ),
        reverse=True,
    )[0]
    return (
        chosen,
        "heuristic_fallback",
        "최신 시각, 신청 정보 충실도, 첨부 수를 기준으로 자동 선택했습니다.",
        None,
    )


def _build_application_group_id(
    *,
    item: WorkspaceReviewItem,
    candidate_context: dict[str, Any],
) -> str:
    normalized_company = normalize_company_name(item.company_name)
    thread_key = str(candidate_context.get("thread_key") or "").strip()
    contact_email = _normalize_contact_key(item.email_address or item.sender or "")
    topic_key = _normalize_application_topic_key(
        subject=item.subject,
        application_purpose=item.application_purpose,
        request_summary=item.request_summary,
        normalized_company=normalized_company,
    )
    if normalized_company and contact_email and topic_key:
        return f"{normalized_company}|contact:{contact_email}|topic:{topic_key}"
    if normalized_company and thread_key and topic_key:
        return f"{normalized_company}|thread:{thread_key}|topic:{topic_key}"
    if normalized_company and contact_email:
        return f"{normalized_company}|contact:{contact_email}"
    if normalized_company and topic_key:
        return f"{normalized_company}|topic:{topic_key}"
    if contact_email and topic_key:
        return f"contact:{contact_email}|topic:{topic_key}"
    if normalized_company:
        return normalized_company
    if thread_key:
        return f"thread:{thread_key}"
    return item.bundle_id


def _build_canonical_candidate_context(
    *,
    workspace: SharedWorkspace,
    item: WorkspaceReviewItem,
) -> dict[str, Any]:
    bundle_root = workspace.from_workspace_relative(item.bundle_root_relpath)
    body_text = ""
    thread_key = ""
    message_key = ""
    try:
        normalized = load_normalized_message_from_bundle(bundle_root)
        body_text = (normalized.body_text or "").strip()
        thread_key = (normalized.thread_key or "").strip()
        message_key = (normalized.message_key or "").strip()
    except Exception:
        pass
    return {
        "bundle_id": item.bundle_id,
        "thread_key": thread_key,
        "message_key": message_key,
        "body_snippet": _truncate_text(body_text, max_length=600),
    }


def _choose_canonical_with_llm(
    *,
    grouped_candidates: list[tuple[WorkspaceReviewItem, dict[str, Any]]],
    wrapper: OpenAIResponsesWrapper,
) -> tuple[WorkspaceReviewItem, str, str, float | None] | None:
    candidate_map = {item.bundle_id: item for item, _ in grouped_candidates}
    candidate_lines: list[str] = []
    for index, (item, context) in enumerate(grouped_candidates, start=1):
        candidate_lines.append(
            "\n".join(
                [
                    f"[후보 {index}]",
                    f"bundle_id: {item.bundle_id}",
                    f"received_at: {item.received_at or ''}",
                    f"subject: {item.subject}",
                    f"sender: {item.sender}",
                    f"company_name: {item.company_name}",
                    f"contact_name: {item.contact_name}",
                    f"email_address: {item.email_address}",
                    f"application_purpose: {item.application_purpose}",
                    f"request_summary: {item.request_summary}",
                    f"attachment_count: {item.attachment_count}",
                    f"thread_key: {context.get('thread_key') or ''}",
                    f"message_key: {context.get('message_key') or ''}",
                    "body_snippet:",
                    str(context.get("body_snippet") or "(본문 없음)"),
                ]
            )
        )
    prompt = (
        "아래 신청 메일 후보들 중에서 실제 엑셀 반영 기준으로 삼을 canonical 메일 1건만 고르세요.\n"
        "최신 시각만 보지 말고, 실제 신청 정보의 충실도, 수정본 여부, 첨부의 최신성, 회신 체인에서 실제 신청서가 어디에 있는지를 함께 보세요.\n"
        "단순 회신이나 수신 확인 메일은 canonical로 고르지 말고, 실제 신청 내용이 가장 완전한 메일을 우선하세요.\n"
        "반드시 후보 중 하나의 bundle_id만 반환하세요.\n\n"
        + "\n\n".join(candidate_lines)
    )
    try:
        envelope = wrapper.create_response(
            operation="runtime.canonical_selection",
            input_payload=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": prompt,
                        }
                    ],
                }
            ],
            text=_canonical_selection_text_config(),
            max_output_tokens=220,
        )
        payload = json.loads(envelope.output_text)
    except Exception:
        return None
    bundle_id = str(payload.get("canonical_bundle_id") or "").strip()
    if bundle_id not in candidate_map:
        return None
    confidence = payload.get("confidence")
    try:
        confidence_value = None if confidence is None else float(confidence)
    except (TypeError, ValueError):
        confidence_value = None
    return (
        candidate_map[bundle_id],
        "llm_canonical_selection",
        str(payload.get("reason") or "LLM이 export 기준 canonical 메일을 자동 선택했습니다."),
        confidence_value,
    )


def _canonical_selection_text_config() -> dict[str, Any]:
    return {
        "format": {
            "name": "canonical_application_message",
            "type": "json_schema",
            "strict": True,
            "schema": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "canonical_bundle_id",
                    "reason",
                    "confidence",
                ],
                "properties": {
                    "canonical_bundle_id": {"type": "string"},
                    "reason": {"type": "string"},
                    "confidence": {"type": ["number", "null"]},
                },
            },
        },
        "verbosity": "low",
    }


def _truncate_text(value: str, *, max_length: int) -> str:
    normalized = re.sub(r"\s+", " ", value or "").strip()
    if len(normalized) <= max_length:
        return normalized
    return normalized[: max_length - 1].rstrip() + "…"


def _normalize_contact_key(value: str) -> str:
    text = (value or "").strip().casefold()
    match = re.search(r"([a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,})", text)
    if match:
        return match.group(1)
    return text


def _normalize_application_topic_key(
    *,
    subject: str,
    application_purpose: str,
    request_summary: str,
    normalized_company: str,
) -> str:
    source = subject or application_purpose or request_summary
    text = (source or "").casefold()
    if not text:
        return ""
    text = re.sub(r"^\s*(\[[^\]]+\]\s*)+", "", text)
    text = re.sub(r"^\s*(re|fw|fwd|답장|회신|전달)\s*:\s*", "", text)
    if normalized_company:
        text = text.replace(normalized_company, " ")
        compact_company = re.sub(r"\s+", "", normalized_company)
        if compact_company:
            text = text.replace(compact_company, " ")
    replacements = {
        "신청서": "신청",
        "수정본": " ",
        "최종본": " ",
        "업데이트": " ",
        "update": " ",
        "revised": " ",
        "revision": " ",
        "회신": " ",
        "답장": " ",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    text = re.sub(r"[^0-9a-z가-힣]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


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
