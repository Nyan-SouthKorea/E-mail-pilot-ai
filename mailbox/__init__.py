"""Mailbox 계층의 기본 데이터 계약을 노출한다."""

from .autoconfig import (
    MailboxAutoConfigPlan,
    MailboxAutoConfigSmokeReport,
    MailServerCandidate,
    MailServerProbeResult,
    build_mailbox_autoconfig_plan,
    run_mailbox_autoconfig_smoke,
    save_mailbox_autoconfig_report,
)
from .bundle_storage import (
    build_mail_bundle_id,
    build_mail_bundle_paths,
    create_mail_bundle_skeleton,
)
from .fixture_reference import (
    FIXTURE_ATTACHMENT_DIR_CANDIDATES,
    build_fixture_preview_html,
    build_fixture_surrogate_eml,
    extract_fixture_body,
    extract_fixture_header,
    find_fixture_attachment_dir,
    parse_fixture_address,
    read_fixture_email_text,
)
from .schema import (
    MAIL_BUNDLE_SCHEMA_VERSION,
    NORMALIZED_MESSAGE_SCHEMA_VERSION,
    Address,
    BodyPart,
    MailBundle,
    MailBundlePaths,
    NormalizedMessage,
    StoredArtifact,
)

__all__ = [
    "MAIL_BUNDLE_SCHEMA_VERSION",
    "NORMALIZED_MESSAGE_SCHEMA_VERSION",
    "Address",
    "BodyPart",
    "MailBundle",
    "MailboxAutoConfigPlan",
    "MailboxAutoConfigSmokeReport",
    "MailBundlePaths",
    "MailServerCandidate",
    "MailServerProbeResult",
    "NormalizedMessage",
    "StoredArtifact",
    "build_mailbox_autoconfig_plan",
    "build_mail_bundle_id",
    "build_mail_bundle_paths",
    "run_mailbox_autoconfig_smoke",
    "save_mailbox_autoconfig_report",
    "FIXTURE_ATTACHMENT_DIR_CANDIDATES",
    "build_fixture_preview_html",
    "build_fixture_surrogate_eml",
    "create_mail_bundle_skeleton",
    "extract_fixture_body",
    "extract_fixture_header",
    "find_fixture_attachment_dir",
    "parse_fixture_address",
    "read_fixture_email_text",
]
