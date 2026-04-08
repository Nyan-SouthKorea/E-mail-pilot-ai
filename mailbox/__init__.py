"""Mailbox 계층의 기본 데이터 계약을 노출한다."""

from .autoconfig import (
    MailboxAutoConfigPlan,
    MailboxAutoConfigSmokeReport,
    MailServerCandidate,
    MailServerProbeResult,
    build_mailbox_autoconfig_plan,
    resolve_login_username,
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
from .imap_fetch_smoke import (
    MailboxImapFetchSmokeReport,
    choose_successful_imap_candidate,
    fetch_latest_imap_message,
    materialize_fetched_imap_message,
    run_imap_latest_mail_fetch_smoke,
    save_imap_fetch_report,
)
from .local_account_config import (
    LocalMailboxAccountConfig,
    default_local_account_config_path,
    load_local_mailbox_account_config,
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
    "MailboxImapFetchSmokeReport",
    "NormalizedMessage",
    "StoredArtifact",
    "build_mailbox_autoconfig_plan",
    "build_mail_bundle_id",
    "build_mail_bundle_paths",
    "choose_successful_imap_candidate",
    "default_local_account_config_path",
    "fetch_latest_imap_message",
    "run_mailbox_autoconfig_smoke",
    "run_imap_latest_mail_fetch_smoke",
    "save_mailbox_autoconfig_report",
    "save_imap_fetch_report",
    "resolve_login_username",
    "FIXTURE_ATTACHMENT_DIR_CANDIDATES",
    "LocalMailboxAccountConfig",
    "build_fixture_preview_html",
    "build_fixture_surrogate_eml",
    "create_mail_bundle_skeleton",
    "extract_fixture_body",
    "extract_fixture_header",
    "load_local_mailbox_account_config",
    "materialize_fetched_imap_message",
    "find_fixture_attachment_dir",
    "parse_fixture_address",
    "read_fixture_email_text",
]
