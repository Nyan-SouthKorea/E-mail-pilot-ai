"""Mailbox 계층에서 공통으로 사용하는 데이터 계약 helper."""

import copy

MAIL_BUNDLE_SCHEMA_VERSION = "mailbox.mail_bundle.v1"
NORMALIZED_MESSAGE_SCHEMA_VERSION = "mailbox.normalized_message.v1"


def make_address(email, name=""):
    """기능: 이메일 주소 정보를 만든다.

    입력:
    - email: 실제 이메일 주소
    - name: 표시 이름

    반환:
    - 주소 dict
    """

    return {
        "email": email,
        "name": name,
    }


def make_body_part(
    part_id,
    mime_type,
    content="",
    charset="",
    content_path="",
    is_primary=False,
):
    """기능: 정규화된 본문 파트 dict를 만든다.

    입력:
    - part_id: MIME 파트 식별자
    - mime_type: `text/plain`, `text/html` 같은 타입
    - content: 본문 문자열
    - charset: 원본 charset 힌트
    - content_path: bundle 루트 기준 상대경로
    - is_primary: 대표 본문 여부

    반환:
    - 본문 파트 dict
    """

    return {
        "part_id": part_id,
        "mime_type": mime_type,
        "content": content,
        "charset": charset,
        "content_path": content_path,
        "is_primary": is_primary,
    }


def make_stored_artifact(
    artifact_id,
    role,
    filename,
    media_type,
    relative_path,
    size_bytes=None,
    sha256="",
    content_id="",
    archive_member_path="",
    derived_from_artifact_id="",
):
    """기능: 첨부 또는 파생 자산 dict를 만든다.

    입력:
    - artifact_id: bundle 내부 식별자
    - role: `attachment`, `inline`, `derived` 같은 역할
    - filename: 표시 파일명
    - media_type: MIME 타입
    - relative_path: bundle 루트 기준 상대경로
    - size_bytes: 파일 크기
    - sha256: 내용 해시
    - content_id: inline 자산의 CID
    - archive_member_path: zip 내부 원본 경로
    - derived_from_artifact_id: 파생 자산의 원본 artifact id

    반환:
    - 자산 dict
    """

    return {
        "artifact_id": artifact_id,
        "role": role,
        "filename": filename,
        "media_type": media_type,
        "relative_path": relative_path,
        "size_bytes": size_bytes,
        "sha256": sha256,
        "content_id": content_id,
        "archive_member_path": archive_member_path,
        "derived_from_artifact_id": derived_from_artifact_id,
    }


def make_mail_bundle_paths(
    root_dir,
    raw_eml_path="raw.eml",
    preview_html_path="preview.html",
    normalized_json_path="normalized.json",
    summary_md_path="summary.md",
    attachments_dir="attachments",
):
    """기능: 메일 번들의 표준 경로 dict를 만든다.

    입력:
    - root_dir: bundle 루트 경로
    - raw_eml_path: 원본 EML 상대경로
    - preview_html_path: HTML preview 상대경로
    - normalized_json_path: 공통 JSON snapshot 상대경로
    - summary_md_path: 사람용 summary 상대경로
    - attachments_dir: 첨부 자산 디렉토리 상대경로

    반환:
    - 경로 dict
    """

    return {
        "root_dir": root_dir,
        "raw_eml_path": raw_eml_path,
        "preview_html_path": preview_html_path,
        "normalized_json_path": normalized_json_path,
        "summary_md_path": summary_md_path,
        "attachments_dir": attachments_dir,
    }


def make_mail_bundle(
    bundle_id,
    provider,
    account_id,
    folder,
    fetched_at,
    from_address,
    paths,
    internet_message_id="",
    remote_message_id="",
    remote_thread_id="",
    subject="",
    sent_at="",
    received_at="",
    reply_to=None,
    to=None,
    cc=None,
    bcc=None,
    body_parts=None,
    artifacts=None,
    headers=None,
    labels=None,
    schema_version=MAIL_BUNDLE_SCHEMA_VERSION,
):
    """기능: 메일 1건의 원본 보관 단위 dict를 만든다.

    입력:
    - 메일 메타데이터, 본문 파트, artifact inventory, 표준 경로 정보

    반환:
    - 메일 번들 dict
    """

    if reply_to is None:
        reply_to = []
    if to is None:
        to = []
    if cc is None:
        cc = []
    if bcc is None:
        bcc = []
    if body_parts is None:
        body_parts = []
    if artifacts is None:
        artifacts = []
    if headers is None:
        headers = {}
    if labels is None:
        labels = []

    return {
        "bundle_id": bundle_id,
        "provider": provider,
        "account_id": account_id,
        "folder": folder,
        "fetched_at": fetched_at,
        "from_address": copy.deepcopy(from_address),
        "paths": copy.deepcopy(paths),
        "internet_message_id": internet_message_id,
        "remote_message_id": remote_message_id,
        "remote_thread_id": remote_thread_id,
        "subject": subject,
        "sent_at": sent_at,
        "received_at": received_at,
        "reply_to": copy.deepcopy(reply_to),
        "to": copy.deepcopy(to),
        "cc": copy.deepcopy(cc),
        "bcc": copy.deepcopy(bcc),
        "body_parts": copy.deepcopy(body_parts),
        "artifacts": copy.deepcopy(artifacts),
        "headers": copy.deepcopy(headers),
        "labels": copy.deepcopy(labels),
        "schema_version": schema_version,
    }


def get_primary_text(bundle):
    """기능: 대표 plain text 본문을 반환한다.

    입력:
    - bundle: 메일 번들 dict

    반환:
    - 대표 text/plain 문자열
    """

    for part in bundle.get("body_parts", []):
        if part.get("mime_type") == "text/plain" and part.get("is_primary"):
            return part.get("content", "")

    for part in bundle.get("body_parts", []):
        if part.get("mime_type") == "text/plain":
            return part.get("content", "")

    return ""


def get_primary_html(bundle):
    """기능: 대표 HTML 본문을 반환한다.

    입력:
    - bundle: 메일 번들 dict

    반환:
    - 대표 text/html 문자열
    """

    for part in bundle.get("body_parts", []):
        if part.get("mime_type") == "text/html" and part.get("is_primary"):
            return part.get("content", "")

    for part in bundle.get("body_parts", []):
        if part.get("mime_type") == "text/html":
            return part.get("content", "")

    return ""


def make_normalized_message(
    bundle_id,
    message_key,
    thread_key,
    sender,
    subject="",
    sent_at="",
    received_at="",
    reply_to=None,
    to=None,
    cc=None,
    bcc=None,
    body_text="",
    body_html="",
    attachment_artifact_ids=None,
    inline_artifact_ids=None,
    other_artifact_ids=None,
    detected_languages=None,
    dedup_keys=None,
    labels=None,
    schema_version=NORMALIZED_MESSAGE_SCHEMA_VERSION,
):
    """기능: 분석 계층에 넘길 공통 메일 입력 dict를 만든다.

    입력:
    - 공통 키, 본문 텍스트/HTML, 참여자, artifact id 목록, dedup 정보

    반환:
    - 정규화된 메일 dict
    """

    if reply_to is None:
        reply_to = []
    if to is None:
        to = []
    if cc is None:
        cc = []
    if bcc is None:
        bcc = []
    if attachment_artifact_ids is None:
        attachment_artifact_ids = []
    if inline_artifact_ids is None:
        inline_artifact_ids = []
    if other_artifact_ids is None:
        other_artifact_ids = []
    if detected_languages is None:
        detected_languages = []
    if dedup_keys is None:
        dedup_keys = []
    if labels is None:
        labels = []

    return {
        "bundle_id": bundle_id,
        "message_key": message_key,
        "thread_key": thread_key,
        "sender": copy.deepcopy(sender),
        "subject": subject,
        "sent_at": sent_at,
        "received_at": received_at,
        "reply_to": copy.deepcopy(reply_to),
        "to": copy.deepcopy(to),
        "cc": copy.deepcopy(cc),
        "bcc": copy.deepcopy(bcc),
        "body_text": body_text,
        "body_html": body_html,
        "attachment_artifact_ids": list(attachment_artifact_ids),
        "inline_artifact_ids": list(inline_artifact_ids),
        "other_artifact_ids": list(other_artifact_ids),
        "detected_languages": list(detected_languages),
        "dedup_keys": list(dedup_keys),
        "labels": list(labels),
        "schema_version": schema_version,
    }


def mail_bundle_to_normalized_message(bundle):
    """기능: 메일 번들에서 분석 입력용 공통 메일 dict를 만든다.

    입력:
    - bundle: 메일 번들 dict

    반환:
    - 정규화된 메일 dict
    """

    message_key = bundle.get("remote_message_id")
    if not message_key:
        message_key = bundle.get("internet_message_id")
    if not message_key:
        message_key = bundle.get("bundle_id", "")

    thread_key = bundle.get("remote_thread_id")
    if not thread_key:
        thread_key = bundle.get("internet_message_id")
    if not thread_key:
        thread_key = message_key

    attachment_artifact_ids = []
    inline_artifact_ids = []
    other_artifact_ids = []
    for artifact in bundle.get("artifacts", []):
        artifact_id = artifact.get("artifact_id", "")
        role = artifact.get("role", "")
        if role == "attachment":
            attachment_artifact_ids.append(artifact_id)
        elif role == "inline":
            inline_artifact_ids.append(artifact_id)
        else:
            other_artifact_ids.append(artifact_id)

    dedup_keys = []
    for value in [message_key, bundle.get("internet_message_id", "")]:
        if value and value not in dedup_keys:
            dedup_keys.append(value)

    return make_normalized_message(
        bundle_id=bundle.get("bundle_id", ""),
        message_key=message_key,
        thread_key=thread_key,
        sender=bundle.get("from_address", make_address("")),
        subject=bundle.get("subject", ""),
        sent_at=bundle.get("sent_at", ""),
        received_at=bundle.get("received_at", ""),
        reply_to=bundle.get("reply_to", []),
        to=bundle.get("to", []),
        cc=bundle.get("cc", []),
        bcc=bundle.get("bcc", []),
        body_text=get_primary_text(bundle),
        body_html=get_primary_html(bundle),
        attachment_artifact_ids=attachment_artifact_ids,
        inline_artifact_ids=inline_artifact_ids,
        other_artifact_ids=other_artifact_ids,
        dedup_keys=dedup_keys,
        labels=bundle.get("labels", []),
    )


def copy_mail_bundle(bundle):
    """기능: 메일 번들 dict의 깊은 복사본을 만든다.

    입력:
    - bundle: 메일 번들 dict

    반환:
    - 복사된 메일 번들 dict
    """

    return copy.deepcopy(bundle)


def copy_normalized_message(message):
    """기능: 정규화된 메일 dict의 깊은 복사본을 만든다.

    입력:
    - message: 정규화된 메일 dict

    반환:
    - 복사된 정규화 메일 dict
    """

    return copy.deepcopy(message)
