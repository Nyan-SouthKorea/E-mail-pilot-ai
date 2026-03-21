"""참고자료 fixture 이메일 디렉토리를 읽는 공용 helper."""

from __future__ import annotations

from email.utils import parseaddr
from html import escape
from pathlib import Path

FIXTURE_ATTACHMENT_DIR_CANDIDATES = (
    "첨부파일",
    "첨부파일(파일들일지 zip일지 모름)",
)


def read_fixture_email_text(fixture_dir: str | Path) -> str:
    """기능: fixture 이메일 원문 텍스트 파일을 읽는다.

    입력:
    - fixture_dir: fixture 이메일 디렉토리 경로

    반환:
    - `이메일 내용.txt` 전체 문자열
    """

    root = Path(fixture_dir)
    return (root / "이메일 내용.txt").read_text(encoding="utf-8")


def find_fixture_attachment_dir(fixture_dir: str | Path) -> Path | None:
    """기능: fixture 첨부 디렉토리를 이름 변형까지 고려해 찾는다.

    입력:
    - fixture_dir: fixture 이메일 디렉토리 경로

    반환:
    - 찾은 첨부 디렉토리 `Path`, 없으면 `None`
    """

    root = Path(fixture_dir)
    for candidate in FIXTURE_ATTACHMENT_DIR_CANDIDATES:
        path = root / candidate
        if path.exists() and path.is_dir():
            return path
    return None


def extract_fixture_header(raw_text: str, key: str) -> str:
    """기능: fixture 텍스트에서 헤더 값을 추출한다.

    입력:
    - raw_text: 이메일 내용 텍스트
    - key: `제목`, `보낸사람`, `받는사람` 같은 헤더명

    반환:
    - 추출된 문자열. 없으면 빈 문자열
    """

    prefix_variants = [f"{key}:", f"{key} :"]
    for line in raw_text.splitlines():
        normalized = line.strip()
        for prefix in prefix_variants:
            if normalized.startswith(prefix):
                return normalized.split(":", 1)[1].strip()
    return ""


def extract_fixture_body(raw_text: str) -> str:
    """기능: fixture 텍스트에서 본문 구간을 추출한다.

    입력:
    - raw_text: 이메일 내용 텍스트

    반환:
    - 본문 문자열
    """

    marker = "내용:"
    if marker not in raw_text:
        return raw_text.strip()
    return raw_text.split(marker, 1)[1].strip()


def parse_fixture_address(raw_value: str) -> tuple[str | None, str]:
    """기능: fixture 헤더 문자열을 이름과 이메일 주소로 나눈다.

    입력:
    - raw_value: `홍길동 <test@example.com>` 같은 문자열

    반환:
    - `(이름 또는 None, 이메일 주소)`
    """

    name, email = parseaddr(raw_value)
    normalized_name = name.strip().strip("'\"") or None
    return normalized_name, email.strip()


def build_fixture_preview_html(*, subject: str, sender: str, recipient: str, body_text: str) -> str:
    """기능: fixture 이메일용 간단한 HTML preview를 만든다.

    입력:
    - subject: 제목
    - sender: 발신자
    - recipient: 수신자
    - body_text: 본문 텍스트

    반환:
    - HTML 문자열
    """

    escaped_body = escape(body_text).replace("\n", "<br>\n")
    return (
        "<!doctype html>\n"
        "<html lang=\"ko\">\n"
        "<head>\n"
        "  <meta charset=\"utf-8\">\n"
        "  <title>Fixture Mail Preview</title>\n"
        "  <style>body{font-family:'Malgun Gothic',sans-serif;line-height:1.6;margin:24px;} "
        ".meta{margin-bottom:20px;padding-bottom:12px;border-bottom:1px solid #ddd;} "
        ".label{font-weight:700;display:inline-block;min-width:72px;}</style>\n"
        "</head>\n"
        "<body>\n"
        "  <div class=\"meta\">\n"
        f"    <div><span class=\"label\">제목</span>{escape(subject)}</div>\n"
        f"    <div><span class=\"label\">보낸사람</span>{escape(sender)}</div>\n"
        f"    <div><span class=\"label\">받는사람</span>{escape(recipient)}</div>\n"
        "  </div>\n"
        f"  <div class=\"body\">{escaped_body}</div>\n"
        "</body>\n"
        "</html>\n"
    )


def build_fixture_surrogate_eml(*, subject: str, sender: str, recipient: str, body_text: str, fixture_id: str) -> str:
    """기능: fixture용 surrogate raw.eml 텍스트를 만든다.

    입력:
    - subject: 제목
    - sender: 발신자
    - recipient: 수신자
    - body_text: 본문 텍스트
    - fixture_id: fixture 식별자

    반환:
    - RFC822 유사 텍스트
    """

    return (
        f"X-Fixture-Source: {fixture_id}\n"
        f"Subject: {subject}\n"
        f"From: {sender}\n"
        f"To: {recipient}\n"
        "MIME-Version: 1.0\n"
        "Content-Type: text/plain; charset=UTF-8\n"
        "\n"
        f"{body_text.strip()}\n"
    )
