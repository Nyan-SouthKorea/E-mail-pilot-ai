"""공유 워크스페이스의 암호화된 secret blob을 관리한다."""

from __future__ import annotations

import base64
from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
from os import urandom

SECRETS_SCHEMA_VERSION = "runtime.workspace_secrets.v1"


def _b64encode(raw: bytes) -> str:
    return base64.b64encode(raw).decode("ascii")


def _b64decode(text: str) -> bytes:
    return base64.b64decode(text.encode("ascii"))


def _derive_key(*, password: str, salt: bytes) -> bytes:
    kdf = Scrypt(salt=salt, length=32, n=2**14, r=8, p=1)
    return kdf.derive(password.encode("utf-8"))


@dataclass(slots=True)
class WorkspaceSecretsStore:
    """기능: 암호화 secret 파일 읽기/쓰기 helper다."""

    path: str
    password: str

    def read(self) -> dict[str, Any]:
        payload = json.loads(Path(self.path).read_text(encoding="utf-8"))
        salt = _b64decode(str(payload["kdf"]["salt_b64"]))
        nonce = _b64decode(str(payload["nonce_b64"]))
        ciphertext = _b64decode(str(payload["ciphertext_b64"]))
        key = _derive_key(password=self.password, salt=salt)
        plaintext = AESGCM(key).decrypt(nonce, ciphertext, None)
        return json.loads(plaintext.decode("utf-8"))

    def write(self, payload: dict[str, Any]) -> None:
        save_encrypted_secrets_file(
            path=self.path,
            password=self.password,
            payload=payload,
        )

    def update_section(self, section: str, values: dict[str, Any]) -> dict[str, Any]:
        payload = self.read()
        current = dict(payload.get(section) or {})
        current.update(values)
        payload[section] = current
        self.write(payload)
        return payload

    def masked_summary(self) -> dict[str, object]:
        payload = self.read()
        return {
            "workspace": dict(payload.get("workspace") or {}),
            "llm": {
                "model": str((payload.get("llm") or {}).get("model") or ""),
                "api_key_saved": bool((payload.get("llm") or {}).get("api_key")),
            },
            "mailbox": {
                "email_address": str((payload.get("mailbox") or {}).get("email_address") or ""),
                "login_username": str((payload.get("mailbox") or {}).get("login_username") or ""),
                "password_saved": bool((payload.get("mailbox") or {}).get("password")),
                "default_folder": str((payload.get("mailbox") or {}).get("default_folder") or ""),
                "available_folders": list((payload.get("mailbox") or {}).get("available_folders") or []),
                "recommended_folder": str((payload.get("mailbox") or {}).get("recommended_folder") or ""),
                "connection_status": str((payload.get("mailbox") or {}).get("connection_status") or "unknown"),
                "connection_checked_at": str((payload.get("mailbox") or {}).get("connection_checked_at") or ""),
                "last_error": str((payload.get("mailbox") or {}).get("last_error") or ""),
                "login_username_kind": str((payload.get("mailbox") or {}).get("login_username_kind") or "email_address_fallback"),
            },
            "exports": dict(payload.get("exports") or {}),
        }


def create_encrypted_secrets_file(
    *,
    path: str | Path,
    password: str,
    payload: dict[str, Any],
) -> None:
    destination = Path(path)
    if destination.exists():
        return
    save_encrypted_secrets_file(path=destination, password=password, payload=payload)


def save_encrypted_secrets_file(
    *,
    path: str | Path,
    password: str,
    payload: dict[str, Any],
) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)

    salt = urandom(16)
    nonce = urandom(12)
    key = _derive_key(password=password, salt=salt)
    plaintext = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
    ciphertext = AESGCM(key).encrypt(nonce, plaintext, None)
    envelope = {
        "schema_version": SECRETS_SCHEMA_VERSION,
        "kdf": {
            "name": "scrypt",
            "salt_b64": _b64encode(salt),
            "n": 2**14,
            "r": 8,
            "p": 1,
        },
        "cipher": {
            "name": "AES-256-GCM",
        },
        "nonce_b64": _b64encode(nonce),
        "ciphertext_b64": _b64encode(ciphertext),
    }
    destination.write_text(
        json.dumps(envelope, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
