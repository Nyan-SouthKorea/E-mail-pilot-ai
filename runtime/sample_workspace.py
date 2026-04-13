"""repo-safe 샘플 워크스페이스를 만든다."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil

from openpyxl import Workbook

from analysis.inbox_review_board_smoke import (
    InboxReviewBoardItem,
    InboxReviewBoardReport,
    build_inbox_review_board_html,
)
from analysis.schema import ExtractedField, ExtractedRecord
from exports import apply_hybrid_template_mapping, project_record_to_template, read_template_profile
from llm import OpenAIResponsesConfig, OpenAIResponsesWrapper
from mailbox.bundle_storage import build_mail_bundle_id, build_mail_bundle_paths
from mailbox.schema import Address, BodyPart, MailBundle, NormalizedMessage, StoredArtifact
from runtime.review_state import ingest_review_report_into_state
from runtime.secrets_store import WorkspaceSecretsStore
from runtime.state_store import WorkspaceStateStore
from runtime.sync_service import rebuild_operating_workbook, update_latest_review_pointers
from runtime.workspace import SharedWorkspace, create_shared_workspace


@dataclass(slots=True)
class SampleWorkspaceSeedResult:
    """기능: 샘플 워크스페이스 seed 생성 결과를 표현한다."""

    workspace_root: str
    template_workbook_relpath: str
    review_json_relpath: str
    review_html_relpath: str
    operating_workbook_relpath: str
    bundle_ids: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class SampleMessageSpec:
    """기능: 합성 샘플 메일 1건 정의를 표현한다."""

    message_key: str
    received_at: str
    sender_name: str
    sender_email: str
    subject: str
    body_text: str
    company_name: str
    contact_name: str
    phone_number: str
    email_address: str
    website_or_social: str
    industry: str
    product_or_service: str
    application_purpose: str
    business_summary: str
    request_summary: str
    triage_label: str
    triage_reason: str
    triage_confidence: float
    attachment_filename: str = ""
    attachment_content: str = ""


def create_sample_workspace(
    *,
    workspace_root: str | Path,
    workspace_password: str,
    workspace_label: str = "샘플 워크스페이스",
) -> SampleWorkspaceSeedResult:
    """기능: repo-safe 샘플 워크스페이스를 새로 만든다."""

    workspace = create_shared_workspace(
        workspace_root=workspace_root,
        workspace_password=workspace_password,
        workspace_label=workspace_label,
    )
    return seed_sample_workspace(
        workspace=workspace,
        workspace_password=workspace_password,
    )


def seed_sample_workspace(
    *,
    workspace: SharedWorkspace,
    workspace_password: str,
) -> SampleWorkspaceSeedResult:
    """기능: 기존 공유 워크스페이스에 샘플 데이터와 review state를 채운다."""

    profile_paths = workspace.profile_paths()
    profile_paths.ensure_runtime_dirs()
    _prepare_sample_profile_roots(workspace)

    template_path = _build_sample_template_workbook(workspace)
    wrapper = OpenAIResponsesWrapper(
        OpenAIResponsesConfig(
            api_key="",
            usage_log_path=str(profile_paths.llm_usage_log_path()),
        )
    )
    template_profile = read_template_profile(
        workbook_path=str(template_path),
        profile_id="sample-workspace",
        template_id=template_path.stem,
    )
    mapped_profile, _ = apply_hybrid_template_mapping(template_profile, wrapper=wrapper)

    extracted_root = profile_paths.runtime_analysis_logs_root()
    exports_root = profile_paths.runtime_exports_logs_root()
    review_root = profile_paths.runtime_review_logs_root()
    for directory in [extracted_root, exports_root, review_root]:
        directory.mkdir(parents=True, exist_ok=True)

    sample_items: list[InboxReviewBoardItem] = []
    bundle_ids: list[str] = []
    for spec in _default_sample_messages():
        materialized = _materialize_sample_message(
            workspace=workspace,
            spec=spec,
            mapped_profile=mapped_profile,
            extracted_root=extracted_root,
            exports_root=exports_root,
        )
        sample_items.append(materialized["item"])
        bundle_ids.append(materialized["bundle_id"])

    timestamp_label = datetime.now().strftime("%y%m%d_%H%M")
    review_json_path = review_root / f"{timestamp_label}_sample_inbox_review_board.json"
    review_html_path = review_root / f"{timestamp_label}_sample_inbox_review_board.html"
    report = InboxReviewBoardReport(
        generated_at=_utc_now_iso(),
        profile_root=str(workspace.profile_root()),
        review_json_path=str(review_json_path),
        review_html_path=str(review_html_path),
        output_workbook_path=str(profile_paths.operating_export_workbook_path()),
        total_bundle_count=len(sample_items),
        application_count=sum(1 for item in sample_items if item.triage_label == "application"),
        not_application_count=sum(1 for item in sample_items if item.triage_label == "not_application"),
        needs_human_review_count=sum(
            1 for item in sample_items if item.triage_label == "needs_human_review"
        ),
        exported_count=sum(1 for item in sample_items if item.export_status == "exported"),
        skipped_count=sum(1 for item in sample_items if item.export_status.startswith("skipped_")),
        failed_count=0,
        items=sample_items,
        notes=[
            "repo-safe 합성 메일 4건으로 샘플 워크스페이스를 만들었다.",
            "샘플 review board는 실제 메일과 API key 없이도 리뷰센터와 workbook 재반영을 검증할 수 있다.",
        ],
    )
    review_json_path.write_text(
        json.dumps(report.to_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    review_html_path.write_text(
        build_inbox_review_board_html(report=report),
        encoding="utf-8",
    )
    update_latest_review_pointers(workspace=workspace, review_report=report)

    state_store = WorkspaceStateStore(workspace.state_db_path())
    state_store.ensure_schema()
    ingest_review_report_into_state(
        workspace=workspace,
        state_store=state_store,
        report_path=review_json_path,
    )
    workbook_result = rebuild_operating_workbook(
        workspace=workspace,
        state_store=state_store,
        template_path=template_path,
        wrapper=wrapper,
    )

    secrets_store = WorkspaceSecretsStore(
        path=str(workspace.secure_blob_path()),
        password=workspace_password,
    )
    payload = secrets_store.read()
    payload["llm"] = {
        "api_key": "",
        "model": "gpt-5.4",
    }
    payload["mailbox"] = {
        "email_address": "sample@example.com",
        "login_username": "sample@example.com",
        "password": "",
        "default_folder": "INBOX",
    }
    payload["exports"] = {
        "template_workbook_relative_path": workspace.to_workspace_relative(template_path),
        "operating_workbook_relative_path": workbook_result["operating_workbook_relpath"],
    }
    secrets_store.write(payload)

    return SampleWorkspaceSeedResult(
        workspace_root=str(workspace.root()),
        template_workbook_relpath=workspace.to_workspace_relative(template_path),
        review_json_relpath=workspace.to_workspace_relative(review_json_path),
        review_html_relpath=workspace.to_workspace_relative(review_html_path),
        operating_workbook_relpath=str(workbook_result["operating_workbook_relpath"]),
        bundle_ids=bundle_ids,
        notes=[
            "샘플 세이브는 실제 메일과 비밀값 없이 리뷰센터와 workbook 재반영을 반복 검증하는 용도다.",
        ],
    )


def _prepare_sample_profile_roots(workspace: SharedWorkspace) -> None:
    targets = [
        workspace.profile_paths().runtime_mail_bundles_root(),
        workspace.profile_paths().runtime_logs_root(),
        workspace.profile_paths().runtime_exports_root(),
    ]
    for target in targets:
        if target.exists():
            shutil.rmtree(target)
        target.mkdir(parents=True, exist_ok=True)
    workspace.profile_paths().ensure_runtime_dirs()


def _build_sample_template_workbook(workspace: SharedWorkspace) -> Path:
    template_path = workspace.profile_paths().template_workbook_path()
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
        cell = worksheet.cell(row=1, column=column_index)
        cell.value = header
    worksheet.freeze_panes = "A2"
    workbook.save(template_path)
    return template_path


def _materialize_sample_message(
    *,
    workspace: SharedWorkspace,
    spec: SampleMessageSpec,
    mapped_profile,
    extracted_root: Path,
    exports_root: Path,
) -> dict[str, object]:
    bundle_id = build_mail_bundle_id(
        received_at=spec.received_at,
        message_key=spec.message_key,
    )
    bundle_ids_root = workspace.profile_paths().runtime_mail_bundles_root()
    bundle_ids_root.mkdir(parents=True, exist_ok=True)
    bundle_paths = build_mail_bundle_paths(str(workspace.profile_root()), bundle_id)
    bundle_root = Path(bundle_paths.root_dir)
    if bundle_root.exists():
        shutil.rmtree(bundle_root)
    attachments_root = bundle_root / bundle_paths.attachments_dir
    attachments_root.mkdir(parents=True, exist_ok=True)

    artifacts: list[StoredArtifact] = []
    if spec.attachment_filename:
        attachment_path = attachments_root / spec.attachment_filename
        attachment_path.write_text(spec.attachment_content or "sample attachment", encoding="utf-8")
        artifacts.append(
            StoredArtifact(
                artifact_id="attachment_1",
                role="attachment",
                filename=spec.attachment_filename,
                media_type="text/plain",
                relative_path=f"attachments/{spec.attachment_filename}",
                size_bytes=attachment_path.stat().st_size,
            )
        )

    preview_html = _build_preview_html(spec)
    raw_eml = _build_raw_eml(spec)
    summary_md = _build_summary_markdown(spec)

    (bundle_root / bundle_paths.raw_eml_path).write_text(raw_eml, encoding="utf-8")
    (bundle_root / bundle_paths.preview_html_path).write_text(preview_html, encoding="utf-8")
    (bundle_root / bundle_paths.summary_md_path).write_text(summary_md, encoding="utf-8")

    bundle = MailBundle(
        bundle_id=bundle_id,
        provider="sample",
        account_id="sample-workspace",
        folder="INBOX",
        fetched_at=_utc_now_iso(),
        from_address=Address(email=spec.sender_email, name=spec.sender_name),
        paths=bundle_paths,
        internet_message_id=f"<{spec.message_key}@sample-workspace>",
        remote_message_id=spec.message_key,
        remote_thread_id=f"{spec.company_name or spec.sender_email}-thread",
        subject=spec.subject,
        sent_at=spec.received_at,
        received_at=spec.received_at,
        to=[Address(email="pilot@example.com", name="운영자")],
        body_parts=[
            BodyPart(
                part_id="body_text",
                mime_type="text/plain",
                content=spec.body_text,
                is_primary=True,
            ),
            BodyPart(
                part_id="body_html",
                mime_type="text/html",
                content=preview_html,
                content_path=bundle_paths.preview_html_path,
                is_primary=True,
            ),
        ],
        artifacts=artifacts,
        headers={
            "subject": spec.subject,
            "from": f"{spec.sender_name} <{spec.sender_email}>",
            "to": "운영자 <pilot@example.com>",
        },
        labels=["sample_workspace"],
    )
    normalized = NormalizedMessage.from_bundle(bundle)
    normalized_path = bundle_root / bundle_paths.normalized_json_path
    normalized_path.write_text(
        json.dumps(normalized.to_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    extracted_record = _build_sample_extracted_record(bundle_id=bundle_id, spec=spec)
    extracted_record_path = extracted_root / f"{bundle_id}_extracted_record.json"
    extracted_record_path.write_text(
        json.dumps(extracted_record.to_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    projected_row = project_record_to_template(mapped_profile, extracted_record)
    projected_row_path = exports_root / f"{bundle_id}_projected_row.json"
    projected_row_path.write_text(
        json.dumps(projected_row.to_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    export_status = _sample_export_status(spec=spec)
    field_map = extracted_record.field_map()
    item = InboxReviewBoardItem(
        bundle_id=bundle_id,
        bundle_root=str(bundle_root),
        received_at=spec.received_at,
        sender=f"{spec.sender_name} <{spec.sender_email}>",
        subject=spec.subject,
        attachment_count=len(artifacts),
        triage_label=spec.triage_label,
        triage_reason=spec.triage_reason,
        triage_confidence=spec.triage_confidence,
        analysis_source="sample_seed",
        export_status=export_status,
        unresolved_columns=list(projected_row.unresolved_columns),
        company_name=_field_value(field_map, "company_name"),
        contact_name=_field_value(field_map, "contact_name"),
        email_address=_field_value(field_map, "email_address"),
        application_purpose=_field_value(field_map, "application_purpose"),
        request_summary=_field_value(field_map, "request_summary"),
        extracted_record_path=str(extracted_record_path),
        projected_row_path=str(projected_row_path),
        summary_path=str(bundle_root / "summary.md"),
        preview_path=str(bundle_root / "preview.html"),
        notes=["sample workspace seed data"],
    )
    return {
        "bundle_id": bundle_id,
        "item": item,
    }


def _build_sample_extracted_record(*, bundle_id: str, spec: SampleMessageSpec) -> ExtractedRecord:
    fields = [
        _field("company_name", spec.company_name),
        _field("contact_name", spec.contact_name),
        _field("phone_number", spec.phone_number),
        _field("email_address", spec.email_address),
        _field("website_or_social", spec.website_or_social),
        _field("industry", spec.industry),
        _field("product_or_service", spec.product_or_service),
        _field("application_purpose", spec.application_purpose),
        _field("company_intro_one_line", _one_line_intro(spec)),
        _field("business_summary", spec.business_summary),
        _field("request_summary", spec.request_summary),
        _field("source_message_subject", spec.subject),
        _field("received_at", spec.received_at),
    ]
    populated_fields = [field for field in fields if field.value]
    return ExtractedRecord(
        bundle_id=bundle_id,
        message_key=spec.message_key,
        record_type="email_application_record",
        category="sample_workspace",
        fields=populated_fields,
        evidence=[],
        summary_one_line=f"{spec.subject} | {spec.triage_label}",
        summary_short=spec.request_summary or spec.body_text[:120],
        triage_label=spec.triage_label,
        triage_reason=spec.triage_reason,
        triage_confidence=spec.triage_confidence,
        overall_confidence=spec.triage_confidence,
        action_hints=["review_center"] if spec.triage_label != "not_application" else [],
        unresolved_questions=[],
        source_artifact_ids=["attachment_1"] if spec.attachment_filename else [],
    )


def _field(field_name: str, value: str) -> ExtractedField:
    return ExtractedField(
        field_name=field_name,
        value=value,
        normalized_value=value,
        confidence=0.92 if value else 0.0,
    )


def _one_line_intro(spec: SampleMessageSpec) -> str:
    if not spec.company_name or not spec.product_or_service:
        return ""
    return f"{spec.company_name}은 {spec.product_or_service}를 제공하는 기업이다."


def _sample_export_status(*, spec: SampleMessageSpec) -> str:
    if spec.triage_label != "application":
        return f"skipped_{spec.triage_label}"
    if not spec.company_name or not (spec.contact_name and (spec.phone_number or spec.email_address)):
        return "skipped_missing_required_signal"
    return "exported"


def _field_value(field_map: dict[str, ExtractedField], field_name: str) -> str:
    field = field_map.get(field_name)
    if field is None:
        return ""
    return field.normalized_value or field.value


def _build_preview_html(spec: SampleMessageSpec) -> str:
    return (
        "<!doctype html>\n"
        "<html lang=\"ko\">\n"
        "<head><meta charset=\"utf-8\"><title>Sample Preview</title></head>\n"
        "<body>\n"
        f"<h1>{spec.subject}</h1>\n"
        f"<p><strong>보낸 사람:</strong> {spec.sender_name} &lt;{spec.sender_email}&gt;</p>\n"
        f"<p>{spec.body_text}</p>\n"
        "</body>\n"
        "</html>\n"
    )


def _build_raw_eml(spec: SampleMessageSpec) -> str:
    return (
        f"From: {spec.sender_name} <{spec.sender_email}>\n"
        "To: 운영자 <pilot@example.com>\n"
        f"Subject: {spec.subject}\n"
        f"Date: {spec.received_at}\n"
        f"Message-ID: <{spec.message_key}@sample-workspace>\n"
        "Content-Type: text/plain; charset=utf-8\n"
        "\n"
        f"{spec.body_text}\n"
    )


def _build_summary_markdown(spec: SampleMessageSpec) -> str:
    return (
        f"# {spec.subject}\n\n"
        f"- triage: {spec.triage_label}\n"
        f"- sender: {spec.sender_name} <{spec.sender_email}>\n"
        f"- company: {spec.company_name or '(미확정)'}\n"
        f"- request_summary: {spec.request_summary or '(없음)'}\n"
    )


def _default_sample_messages() -> list[SampleMessageSpec]:
    return [
        SampleMessageSpec(
            message_key="sample-alpha-application-001",
            received_at="2026-04-05T09:15:00+09:00",
            sender_name="박서연",
            sender_email="seoyeon@acralight.co.kr",
            subject="[샘플] 아크라이트 참가 신청",
            body_text="안녕하세요. 아크라이트 참가 신청서를 전달드립니다. 담당자는 박서연이며 연락처와 회사 소개를 함께 보냅니다.",
            company_name="주식회사 아크라이트",
            contact_name="박서연",
            phone_number="010-2222-3333",
            email_address="seoyeon@acralight.co.kr",
            website_or_social="https://acralight.co.kr",
            industry="산업용 센서",
            product_or_service="산업 안전 센서 솔루션",
            application_purpose="산업 안전 센서 솔루션을 소개하고 파트너 상담을 진행하려는 신청이다.",
            business_summary="산업 현장의 위험 감지를 돕는 센서와 관제 소프트웨어를 공급한다.",
            request_summary="전시 부스 참가와 바이어 상담 일정을 요청했다.",
            triage_label="application",
            triage_reason="참가 신청 의사와 기업/연락처 정보가 모두 확인된다.",
            triage_confidence=0.96,
            attachment_filename="아크라이트_신청서.txt",
            attachment_content="아크라이트 신청서 샘플",
        ),
        SampleMessageSpec(
            message_key="sample-alpha-application-002",
            received_at="2026-04-06T14:25:00+09:00",
            sender_name="박서연",
            sender_email="seoyeon@acralight.co.kr",
            subject="[샘플] 아크라이트 참가 신청서 수정본",
            body_text="수정된 참가 신청서를 다시 전달드립니다. 이전 메일 대신 이번 메일을 기준으로 검토 부탁드립니다.",
            company_name="(주) 아크라이트",
            contact_name="박서연",
            phone_number="010-2222-3333",
            email_address="seoyeon@acralight.co.kr",
            website_or_social="https://acralight.co.kr",
            industry="산업용 센서",
            product_or_service="산업 안전 센서 솔루션",
            application_purpose="수정된 신청 정보를 기준으로 참가 확정을 요청하는 신청이다.",
            business_summary="산업 안전 센서와 관제 솔루션을 공급한다.",
            request_summary="수정본 기준으로 참가 검토를 요청했다.",
            triage_label="application",
            triage_reason="수정본 신청 메일로 보이며 최신 메일이 대표 후보가 된다.",
            triage_confidence=0.94,
            attachment_filename="아크라이트_신청서_수정본.txt",
            attachment_content="아크라이트 신청서 수정본 샘플",
        ),
        SampleMessageSpec(
            message_key="sample-beta-notice-001",
            received_at="2026-04-06T17:40:00+09:00",
            sender_name="운영사무국",
            sender_email="notice@expo-example.kr",
            subject="[샘플] 행사 일정 안내",
            body_text="참가 신청과 무관한 일반 안내 메일입니다. 일정 공지와 준비물 안내만 포함합니다.",
            company_name="",
            contact_name="",
            phone_number="",
            email_address="",
            website_or_social="",
            industry="",
            product_or_service="",
            application_purpose="",
            business_summary="",
            request_summary="행사 일정과 공지사항을 전달한 안내 메일이다.",
            triage_label="not_application",
            triage_reason="일반 안내 메일로 신청서 대상이 아니다.",
            triage_confidence=0.98,
        ),
        SampleMessageSpec(
            message_key="sample-gamma-review-001",
            received_at="2026-04-07T11:05:00+09:00",
            sender_name="이하준",
            sender_email="hajun@gammalabs.ai",
            subject="[샘플] 참가 문의",
            body_text="참가 가능 여부를 문의드립니다. 회사 소개는 있으나 담당 연락처가 충분하지 않아 검토가 필요합니다.",
            company_name="감마랩스",
            contact_name="이하준",
            phone_number="",
            email_address="hajun@gammalabs.ai",
            website_or_social="https://gammalabs.ai",
            industry="AI 소프트웨어",
            product_or_service="생성형 AI 분석 도구",
            application_purpose="참가 가능 여부를 먼저 문의하는 성격의 메일이다.",
            business_summary="생성형 AI 기반 분석 도구를 개발한다.",
            request_summary="정식 신청인지 확인이 필요하다.",
            triage_label="needs_human_review",
            triage_reason="회사 정보는 있으나 신청 의사와 필수 연락 신호가 약하다.",
            triage_confidence=0.63,
        ),
    ]


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
