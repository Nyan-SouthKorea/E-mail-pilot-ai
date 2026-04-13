"""이 PC 전용의 민감한 보조 설정을 암호화 저장한다."""

from __future__ import annotations

import base64
import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


DEVICE_SECRETS_SCHEMA_VERSION = "runtime.device_secrets.v1"


@dataclass(slots=True)
class LocalDeviceSecrets:
    """기능: 이 PC에서만 재사용할 민감한 보조 설정을 표현한다."""

    last_workspace_root: str = ""
    last_workspace_password: str = ""
    default_openai_api_key: str = ""

    def to_dict(self) -> dict[str, object]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "LocalDeviceSecrets":
        return cls(
            last_workspace_root=str(payload.get("last_workspace_root") or ""),
            last_workspace_password=str(payload.get("last_workspace_password") or ""),
            default_openai_api_key=str(payload.get("default_openai_api_key") or ""),
        )


def default_device_secrets_path() -> Path:
    if os.name == "nt":
        appdata = Path(os.environ.get("APPDATA") or Path.home() / "AppData" / "Roaming")
        return appdata / "EmailPilotAI" / "device_secrets.json"
    return Path.home() / ".config" / "email-pilot-ai" / "device_secrets.json"


def _default_linux_fallback_key_path() -> Path:
    return default_device_secrets_path().with_suffix(".key")


def load_local_device_secrets(path: str | Path | None = None) -> LocalDeviceSecrets:
    target = Path(path or default_device_secrets_path())
    if not target.exists():
        return LocalDeviceSecrets()
    try:
        payload = json.loads(target.read_text(encoding="utf-8"))
        plaintext = _decrypt_blob(payload=payload)
        return LocalDeviceSecrets.from_dict(json.loads(plaintext.decode("utf-8")))
    except Exception:
        return LocalDeviceSecrets()


def save_local_device_secrets(
    settings: LocalDeviceSecrets,
    path: str | Path | None = None,
) -> Path:
    target = Path(path or default_device_secrets_path())
    target.parent.mkdir(parents=True, exist_ok=True)
    plaintext = json.dumps(settings.to_dict(), ensure_ascii=False, indent=2).encode("utf-8")
    envelope = _encrypt_blob(plaintext=plaintext)
    target.write_text(json.dumps(envelope, ensure_ascii=False, indent=2), encoding="utf-8")
    return target


def remember_last_workspace_secret(
    *,
    workspace_root: str,
    workspace_password: str,
    path: str | Path | None = None,
) -> LocalDeviceSecrets:
    settings = load_local_device_secrets(path)
    settings.last_workspace_root = workspace_root
    settings.last_workspace_password = workspace_password
    save_local_device_secrets(settings, path)
    return settings


def remember_default_openai_api_key(
    *,
    api_key: str,
    path: str | Path | None = None,
) -> LocalDeviceSecrets:
    settings = load_local_device_secrets(path)
    settings.default_openai_api_key = api_key
    save_local_device_secrets(settings, path)
    return settings


def clear_last_workspace_secret(path: str | Path | None = None) -> LocalDeviceSecrets:
    settings = load_local_device_secrets(path)
    settings.last_workspace_root = ""
    settings.last_workspace_password = ""
    save_local_device_secrets(settings, path)
    return settings


def _encrypt_blob(*, plaintext: bytes) -> dict[str, Any]:
    if os.name == "nt":
        protected = _windows_dpapi_protect(plaintext)
        return {
            "schema_version": DEVICE_SECRETS_SCHEMA_VERSION,
        "cipher": {"name": "windows-dpapi"},
            "ciphertext_b64": base64.b64encode(protected).decode("ascii"),
        }
    key = _linux_fallback_key()
    nonce = os.urandom(12)
    ciphertext = AESGCM(key).encrypt(nonce, plaintext, None)
    return {
        "schema_version": DEVICE_SECRETS_SCHEMA_VERSION,
        "cipher": {"name": "aes-256-gcm-local-key"},
        "nonce_b64": base64.b64encode(nonce).decode("ascii"),
        "ciphertext_b64": base64.b64encode(ciphertext).decode("ascii"),
    }


def _decrypt_blob(*, payload: dict[str, Any]) -> bytes:
    cipher_name = str((payload.get("cipher") or {}).get("name") or "")
    ciphertext = base64.b64decode(str(payload.get("ciphertext_b64") or "").encode("ascii"))
    if cipher_name == "windows-dpapi":
        return _windows_dpapi_unprotect(ciphertext)
    nonce = base64.b64decode(str(payload.get("nonce_b64") or "").encode("ascii"))
    return AESGCM(_linux_fallback_key()).decrypt(nonce, ciphertext, None)


def _linux_fallback_key() -> bytes:
    key_path = _default_linux_fallback_key_path()
    if key_path.exists():
        return key_path.read_bytes()
    key_path.parent.mkdir(parents=True, exist_ok=True)
    key = AESGCM.generate_key(bit_length=256)
    key_path.write_bytes(key)
    try:
        os.chmod(key_path, 0o600)
    except OSError:
        pass
    return key


def _windows_dpapi_protect(plaintext: bytes) -> bytes:
    import ctypes
    from ctypes import POINTER, Structure, byref, c_char, c_void_p, wintypes

    class DATA_BLOB(Structure):
        _fields_ = [
            ("cbData", wintypes.DWORD),
            ("pbData", POINTER(c_char)),
        ]

    crypt32 = ctypes.windll.crypt32
    kernel32 = ctypes.windll.kernel32

    input_buffer = ctypes.create_string_buffer(plaintext)
    input_blob = DATA_BLOB(len(plaintext), ctypes.cast(input_buffer, POINTER(c_char)))
    output_blob = DATA_BLOB()

    if not crypt32.CryptProtectData(
        byref(input_blob),
            ctypes.c_wchar_p("EmailPilotAI"),
        None,
        None,
        None,
        0,
        byref(output_blob),
    ):
        raise OSError("Windows DPAPI 암호화에 실패했습니다.")

    try:
        return ctypes.string_at(output_blob.pbData, output_blob.cbData)
    finally:
        kernel32.LocalFree(c_void_p(ctypes.addressof(output_blob.pbData.contents)))


def _windows_dpapi_unprotect(ciphertext: bytes) -> bytes:
    import ctypes
    from ctypes import POINTER, Structure, byref, c_char, c_void_p, wintypes

    class DATA_BLOB(Structure):
        _fields_ = [
            ("cbData", wintypes.DWORD),
            ("pbData", POINTER(c_char)),
        ]

    crypt32 = ctypes.windll.crypt32
    kernel32 = ctypes.windll.kernel32

    input_buffer = ctypes.create_string_buffer(ciphertext)
    input_blob = DATA_BLOB(len(ciphertext), ctypes.cast(input_buffer, POINTER(c_char)))
    output_blob = DATA_BLOB()

    if not crypt32.CryptUnprotectData(
        byref(input_blob),
        None,
        None,
        None,
        None,
        0,
        byref(output_blob),
    ):
        raise OSError("Windows DPAPI 복호화에 실패했습니다.")

    try:
        return ctypes.string_at(output_blob.pbData, output_blob.cbData)
    finally:
        kernel32.LocalFree(c_void_p(ctypes.addressof(output_blob.pbData.contents)))
