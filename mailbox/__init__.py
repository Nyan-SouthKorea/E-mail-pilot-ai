"""Mailbox 계층의 기본 데이터 계약을 노출한다."""

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
    "MailBundlePaths",
    "NormalizedMessage",
    "StoredArtifact",
]
