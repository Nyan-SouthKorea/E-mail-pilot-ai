"""Mailbox 계층에서 공통으로 사용하는 데이터 계약."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

MAIL_BUNDLE_SCHEMA_VERSION = "mailbox.mail_bundle.v1"
NORMALIZED_MESSAGE_SCHEMA_VERSION = "mailbox.normalized_message.v1"


@dataclass(slots=True)
class Address:
    """기능: 이메일 주소 한 개를 표현한다.

    입력:
    - name: 표시 이름
    - email: 실제 이메일 주소

    반환:
    - dataclass 인스턴스
    """

    email: str
    name: str | None = None


@dataclass(slots=True)
class BodyPart:
    """기능: 정규화된 본문 파트를 표현한다.

    입력:
    - part_id: MIME 파트 식별자
    - mime_type: `text/plain`, `text/html` 같은 타입
    - content: 본문 문자열
    - charset: 원본 charset 힌트
    - content_path: bundle 루트 기준 상대경로
    - is_primary: 대표 본문 여부

    반환:
    - dataclass 인스턴스
    """

    part_id: str
    mime_type: str
    content: str = ""
    charset: str | None = None
    content_path: str | None = None
    is_primary: bool = False


@dataclass(slots=True)
class StoredArtifact:
    """기능: 메일 번들 안의 첨부 또는 파생 자산을 표현한다.

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
    - dataclass 인스턴스
    """

    artifact_id: str
    role: str
    filename: str
    media_type: str
    relative_path: str
    size_bytes: int | None = None
    sha256: str | None = None
    content_id: str | None = None
    archive_member_path: str | None = None
    derived_from_artifact_id: str | None = None


@dataclass(slots=True)
class MailBundlePaths:
    """기능: 메일 번들의 표준 파일 레이아웃을 표현한다.

    입력:
    - root_dir: bundle 루트 경로
    - raw_eml_path: 원본 EML 상대경로
    - preview_html_path: HTML preview 상대경로
    - normalized_json_path: 공통 JSON snapshot 상대경로
    - summary_md_path: 사람용 summary 상대경로
    - attachments_dir: 첨부 자산 디렉토리 상대경로

    반환:
    - dataclass 인스턴스
    """

    root_dir: str
    raw_eml_path: str = "raw.eml"
    preview_html_path: str = "preview.html"
    normalized_json_path: str = "normalized.json"
    summary_md_path: str = "summary.md"
    attachments_dir: str = "attachments"


@dataclass(slots=True)
class MailBundle:
    """기능: 메일 1건의 원본 보관 단위를 표현한다.

    입력:
    - 메일 메타데이터, 본문 파트, artifact inventory, 표준 경로 정보

    반환:
    - dataclass 인스턴스
    """

    bundle_id: str
    provider: str
    account_id: str
    folder: str
    fetched_at: str
    from_address: Address
    paths: MailBundlePaths
    internet_message_id: str = ""
    remote_message_id: str | None = None
    remote_thread_id: str | None = None
    subject: str = ""
    sent_at: str | None = None
    received_at: str | None = None
    reply_to: list[Address] = field(default_factory=list)
    to: list[Address] = field(default_factory=list)
    cc: list[Address] = field(default_factory=list)
    bcc: list[Address] = field(default_factory=list)
    body_parts: list[BodyPart] = field(default_factory=list)
    artifacts: list[StoredArtifact] = field(default_factory=list)
    headers: dict[str, str] = field(default_factory=dict)
    labels: list[str] = field(default_factory=list)
    schema_version: str = MAIL_BUNDLE_SCHEMA_VERSION

    def primary_text(self) -> str:
        """기능: 대표 plain text 본문을 반환한다.

        입력:
        - 없음

        반환:
        - 대표 text/plain 문자열
        """

        primary = next(
            (
                part
                for part in self.body_parts
                if part.mime_type == "text/plain" and part.is_primary
            ),
            None,
        )
        if primary is not None:
            return primary.content

        fallback = next(
            (part for part in self.body_parts if part.mime_type == "text/plain"),
            None,
        )
        return fallback.content if fallback is not None else ""

    def primary_html(self) -> str:
        """기능: 대표 HTML 본문을 반환한다.

        입력:
        - 없음

        반환:
        - 대표 text/html 문자열
        """

        primary = next(
            (
                part
                for part in self.body_parts
                if part.mime_type == "text/html" and part.is_primary
            ),
            None,
        )
        if primary is not None:
            return primary.content

        fallback = next(
            (part for part in self.body_parts if part.mime_type == "text/html"),
            None,
        )
        return fallback.content if fallback is not None else ""

    def to_dict(self) -> dict[str, object]:
        """기능: 메일 번들을 JSON 직렬화용 dict로 바꾼다.

        입력:
        - 없음

        반환:
        - 중첩 dataclass가 풀린 dict
        """

        return asdict(self)


@dataclass(slots=True)
class NormalizedMessage:
    """기능: 분석 계층에 넘기는 공통 메일 입력을 표현한다.

    입력:
    - 공통 키, 본문 텍스트/HTML, 참여자, artifact id 목록, dedup 정보

    반환:
    - dataclass 인스턴스
    """

    bundle_id: str
    message_key: str
    thread_key: str
    sender: Address
    subject: str = ""
    sent_at: str | None = None
    received_at: str | None = None
    reply_to: list[Address] = field(default_factory=list)
    to: list[Address] = field(default_factory=list)
    cc: list[Address] = field(default_factory=list)
    bcc: list[Address] = field(default_factory=list)
    body_text: str = ""
    body_html: str = ""
    attachment_artifact_ids: list[str] = field(default_factory=list)
    inline_artifact_ids: list[str] = field(default_factory=list)
    other_artifact_ids: list[str] = field(default_factory=list)
    detected_languages: list[str] = field(default_factory=list)
    dedup_keys: list[str] = field(default_factory=list)
    labels: list[str] = field(default_factory=list)
    schema_version: str = NORMALIZED_MESSAGE_SCHEMA_VERSION

    @classmethod
    def from_bundle(cls, bundle: MailBundle) -> "NormalizedMessage":
        """기능: `MailBundle`에서 분석 입력용 공통 메일을 만든다.

        입력:
        - bundle: 원본 보관 단위

        반환:
        - `NormalizedMessage` 인스턴스
        """

        message_key = bundle.remote_message_id or bundle.internet_message_id or bundle.bundle_id
        thread_key = bundle.remote_thread_id or bundle.internet_message_id or message_key

        attachment_ids = [
            artifact.artifact_id
            for artifact in bundle.artifacts
            if artifact.role == "attachment"
        ]
        inline_ids = [
            artifact.artifact_id
            for artifact in bundle.artifacts
            if artifact.role == "inline"
        ]
        other_ids = [
            artifact.artifact_id
            for artifact in bundle.artifacts
            if artifact.role not in {"attachment", "inline"}
        ]

        dedup_keys: list[str] = []
        for value in [message_key, bundle.internet_message_id]:
            if value and value not in dedup_keys:
                dedup_keys.append(value)

        return cls(
            bundle_id=bundle.bundle_id,
            message_key=message_key,
            thread_key=thread_key,
            sender=bundle.from_address,
            subject=bundle.subject,
            sent_at=bundle.sent_at,
            received_at=bundle.received_at,
            reply_to=list(bundle.reply_to),
            to=list(bundle.to),
            cc=list(bundle.cc),
            bcc=list(bundle.bcc),
            body_text=bundle.primary_text(),
            body_html=bundle.primary_html(),
            attachment_artifact_ids=attachment_ids,
            inline_artifact_ids=inline_ids,
            other_artifact_ids=other_ids,
            dedup_keys=dedup_keys,
            labels=list(bundle.labels),
        )

    def to_dict(self) -> dict[str, object]:
        """기능: 공통 메일 입력을 JSON 직렬화용 dict로 바꾼다.

        입력:
        - 없음

        반환:
        - 중첩 dataclass가 풀린 dict
        """

        return asdict(self)
