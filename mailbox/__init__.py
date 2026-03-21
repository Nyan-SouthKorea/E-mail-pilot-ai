"""Mailbox 계층의 기본 데이터 계약과 helper를 노출한다."""

from .schema import (
    MAIL_BUNDLE_SCHEMA_VERSION,
    NORMALIZED_MESSAGE_SCHEMA_VERSION,
    copy_mail_bundle,
    copy_normalized_message,
    get_primary_html,
    get_primary_text,
    mail_bundle_to_normalized_message,
    make_address,
    make_body_part,
    make_mail_bundle,
    make_mail_bundle_paths,
    make_normalized_message,
    make_stored_artifact,
)

__all__ = [
    "MAIL_BUNDLE_SCHEMA_VERSION",
    "NORMALIZED_MESSAGE_SCHEMA_VERSION",
    "copy_mail_bundle",
    "copy_normalized_message",
    "get_primary_html",
    "get_primary_text",
    "mail_bundle_to_normalized_message",
    "make_address",
    "make_body_part",
    "make_mail_bundle",
    "make_mail_bundle_paths",
    "make_normalized_message",
    "make_stored_artifact",
]
