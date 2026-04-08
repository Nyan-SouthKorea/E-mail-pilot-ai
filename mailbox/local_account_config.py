"""로컬 secret 파일에서 실제 메일 계정 입력을 읽는다."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from project_paths import default_example_profile_root, workspace_root


@dataclass(slots=True)
class LocalMailboxAccountConfig:
    """기능: 실제 메일 계정 입력을 표현한다.

    입력:
    - email_address: 계정 이메일 주소
    - login_username: 실제 로그인 id
    - password: 비밀번호 또는 앱 비밀번호
    - profile_root: 사용할 사용자 프로필 루트
    - source_path: 설정을 읽은 local 파일 경로
    - notes: 보조 메모

    반환:
    - dataclass 인스턴스
    """

    email_address: str
    login_username: str
    password: str
    profile_root: str
    source_path: str
    notes: list[str] = field(default_factory=list)

    @property
    def login_username_kind(self) -> str:
        normalized_login_username = self.login_username.strip()
        if normalized_login_username and normalized_login_username != self.email_address:
            return "explicit_login_username"
        return "email_address_fallback"

    def resolved_login_username(self) -> str:
        return self.login_username.strip() or self.email_address.strip()

    def to_safe_dict(self) -> dict[str, object]:
        return {
            "email_address": self.email_address,
            "login_username_kind": self.login_username_kind,
            "profile_root": self.profile_root,
            "source_path": self.source_path,
            "notes": list(self.notes),
        }


KEY_ALIASES = {
    "email": "email_address",
    "emailaddress": "email_address",
    "mail": "email_address",
    "이메일": "email_address",
    "주소": "email_address",
    "id": "login_username",
    "userid": "login_username",
    "username": "login_username",
    "loginid": "login_username",
    "loginusername": "login_username",
    "user": "login_username",
    "계정": "login_username",
    "아이디": "login_username",
    "password": "password",
    "passwd": "password",
    "pw": "password",
    "비밀번호": "password",
    "암호": "password",
    "profileroot": "profile_root",
    "profile": "profile_root",
    "프로필": "profile_root",
}


def build_local_mailbox_account_config(
    *,
    email_address: str,
    login_username: str,
    password: str,
    profile_root: str | Path,
    source_path: str = "workspace_shared_settings",
    notes: list[str] | None = None,
) -> LocalMailboxAccountConfig:
    """기능: 명시 값들로 `LocalMailboxAccountConfig`를 바로 만든다.

    입력:
    - email_address: 계정 이메일 주소
    - login_username: 실제 로그인 id
    - password: 비밀번호 또는 앱 비밀번호
    - profile_root: 사용자 프로필 루트
    - source_path: 설정 출처 설명 문자열
    - notes: 추가 메모

    반환:
    - `LocalMailboxAccountConfig`
    """

    resolved_email = email_address.strip()
    resolved_login_username = login_username.strip() or resolved_email
    resolved_password = password.strip()
    if not resolved_email:
        raise ValueError("이메일 주소가 비어 있어 mailbox 계정 구성을 만들 수 없다.")
    if not resolved_password:
        raise ValueError("비밀번호가 비어 있어 mailbox 계정 구성을 만들 수 없다.")

    resolved_notes = list(notes or [])
    if resolved_login_username == resolved_email:
        resolved_notes.append("별도 로그인 id가 없어 이메일 주소를 login username으로 사용한다.")
    else:
        resolved_notes.append("별도 로그인 id를 명시적으로 사용한다.")

    return LocalMailboxAccountConfig(
        email_address=resolved_email,
        login_username=resolved_login_username,
        password=resolved_password,
        profile_root=str(_resolve_profile_root(explicit_profile_root=profile_root, configured_profile_root=None)),
        source_path=source_path,
        notes=resolved_notes,
    )


def default_local_account_config_path() -> Path:
    """기능: 기본 local 계정 정보 파일 경로를 반환한다.

    입력:
    - 없음

    반환:
    - `secrets/이메일 정보.txt`
    """

    return workspace_root() / "secrets" / "이메일 정보.txt"


def load_local_mailbox_account_config(
    credentials_path: str | Path | None = None,
    *,
    profile_root: str | Path | None = None,
) -> LocalMailboxAccountConfig:
    """기능: local secret 파일에서 실제 메일 계정 입력을 읽는다.

    입력:
    - credentials_path: 계정 정보 파일 경로
    - profile_root: 강제로 사용할 프로필 루트

    반환:
    - `LocalMailboxAccountConfig`
    """

    path = Path(credentials_path or default_local_account_config_path())
    lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]

    values: dict[str, str] = {}
    notes: list[str] = []

    for line in lines:
        if ":" in line:
            raw_key, raw_value = line.split(":", 1)
            field_name = KEY_ALIASES.get(_normalize_key(raw_key))
            if field_name is not None and raw_value.strip():
                values[field_name] = raw_value.strip()
                continue
        if "@" in line and "email_address" not in values:
            values["email_address"] = line

    email_address = values.get("email_address", "").strip()
    if not email_address:
        raise ValueError("local 계정 정보 파일에서 이메일 주소를 찾지 못했다.")

    login_username = values.get("login_username", "").strip() or email_address
    if login_username == email_address:
        notes.append("별도 로그인 id가 없어 이메일 주소를 login username으로 사용한다.")
    else:
        notes.append("별도 로그인 id를 명시적으로 사용한다.")

    password = values.get("password", "").strip()
    if not password:
        raise ValueError("local 계정 정보 파일에서 password를 찾지 못했다.")

    resolved_profile_root = _resolve_profile_root(
        explicit_profile_root=profile_root,
        configured_profile_root=values.get("profile_root"),
    )

    return LocalMailboxAccountConfig(
        email_address=email_address,
        login_username=login_username,
        password=password,
        profile_root=str(resolved_profile_root),
        source_path=str(path),
        notes=notes,
    )


def _normalize_key(raw_key: str) -> str:
    return (
        raw_key.strip()
        .lower()
        .replace(" ", "")
        .replace("_", "")
        .replace("-", "")
    )


def _resolve_profile_root(
    *,
    explicit_profile_root: str | Path | None,
    configured_profile_root: str | None,
) -> Path:
    chosen = explicit_profile_root or configured_profile_root or default_example_profile_root()
    path = Path(chosen)
    if path.is_absolute():
        return path
    return workspace_root() / path
