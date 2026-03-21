"""메일 자동 설정 후보 생성과 probe helper."""

from __future__ import annotations

import imaplib
import json
import poplib
import smtplib
import socket
import ssl
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass, field
from pathlib import Path


@dataclass(slots=True)
class MailServerCandidate:
    """기능: 메일 서버 설정 후보 1개를 표현한다.

    입력:
    - protocol: `imap`, `pop3`, `smtp`
    - host: 서버 호스트
    - port: 포트 번호
    - security: `ssl`, `starttls`, `plain`
    - username_hint: 사용자 이름 형식 힌트
    - auth_hint: 인증 힌트
    - source: 후보 출처
    - score: 우선순위 점수
    - notes: 보조 메모

    반환:
    - dataclass 인스턴스
    """

    protocol: str
    host: str
    port: int
    security: str
    username_hint: str = "%EMAILADDRESS%"
    auth_hint: str | None = None
    source: str = "unknown"
    score: int = 0
    notes: list[str] = field(default_factory=list)

    def key(self) -> tuple[str, str, int, str]:
        """기능: 중복 제거용 키를 반환한다.

        입력:
        - 없음

        반환:
        - 후보 고유 키
        """

        return (self.protocol, self.host, self.port, self.security)

    def to_dict(self) -> dict[str, object]:
        """기능: 후보를 dict로 바꾼다.

        입력:
        - 없음

        반환:
        - 직렬화용 dict
        """

        return asdict(self)


@dataclass(slots=True)
class MailboxAutoConfigPlan:
    """기능: 이메일 주소 기준 자동 설정 계획 전체를 표현한다."""

    email_address: str
    domain: str
    provider_key: str
    provider_label: str
    imap_candidates: list[MailServerCandidate] = field(default_factory=list)
    pop3_candidates: list[MailServerCandidate] = field(default_factory=list)
    smtp_candidates: list[MailServerCandidate] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        """기능: 계획을 dict로 바꾼다.

        입력:
        - 없음

        반환:
        - 직렬화용 dict
        """

        payload = asdict(self)
        payload["imap_candidates"] = [item.to_dict() for item in self.imap_candidates]
        payload["pop3_candidates"] = [item.to_dict() for item in self.pop3_candidates]
        payload["smtp_candidates"] = [item.to_dict() for item in self.smtp_candidates]
        return payload


@dataclass(slots=True)
class MailServerProbeResult:
    """기능: 후보 1개에 대한 연결 또는 로그인 probe 결과를 표현한다."""

    protocol: str
    host: str
    port: int
    security: str
    mode: str
    success: bool
    stage: str
    latency_ms: int
    source: str
    message: str = ""

    def to_dict(self) -> dict[str, object]:
        """기능: probe 결과를 dict로 바꾼다.

        입력:
        - 없음

        반환:
        - 직렬화용 dict
        """

        return asdict(self)


@dataclass(slots=True)
class MailboxAutoConfigSmokeReport:
    """기능: 자동 설정 smoke 전체 결과를 표현한다."""

    email_address: str
    mode: str
    plan: MailboxAutoConfigPlan
    probe_results: list[MailServerProbeResult] = field(default_factory=list)
    recommended_incoming: MailServerCandidate | None = None
    recommended_outgoing: MailServerCandidate | None = None
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        """기능: smoke 결과를 dict로 바꾼다.

        입력:
        - 없음

        반환:
        - 직렬화용 dict
        """

        return {
            "email_address": self.email_address,
            "mode": self.mode,
            "plan": self.plan.to_dict(),
            "probe_results": [item.to_dict() for item in self.probe_results],
            "recommended_incoming": (
                self.recommended_incoming.to_dict()
                if self.recommended_incoming is not None
                else None
            ),
            "recommended_outgoing": (
                self.recommended_outgoing.to_dict()
                if self.recommended_outgoing is not None
                else None
            ),
            "notes": list(self.notes),
        }


PROVIDER_PRESETS: dict[str, dict[str, object]] = {
    "gmail": {
        "domains": {"gmail.com", "googlemail.com"},
        "label": "Gmail",
        "incoming": [
            MailServerCandidate(
                protocol="imap",
                host="imap.gmail.com",
                port=993,
                security="ssl",
                source="provider_preset",
                score=100,
                notes=["Google 공식 IMAP 기본값"],
            ),
            MailServerCandidate(
                protocol="pop3",
                host="pop.gmail.com",
                port=995,
                security="ssl",
                source="provider_preset",
                score=80,
                notes=["Google 공식 POP3 기본값"],
            ),
        ],
        "outgoing": [
            MailServerCandidate(
                protocol="smtp",
                host="smtp.gmail.com",
                port=587,
                security="starttls",
                source="provider_preset",
                score=100,
                notes=["Google 공식 SMTP 기본값"],
            ),
            MailServerCandidate(
                protocol="smtp",
                host="smtp.gmail.com",
                port=465,
                security="ssl",
                source="provider_preset",
                score=95,
                notes=["Google 공식 SMTP SSL 대안"],
            ),
        ],
        "notes": [
            "Gmail 계정은 일반 비밀번호 대신 앱 비밀번호 또는 OAuth가 필요할 수 있다."
        ],
    },
    "outlook": {
        "domains": {"outlook.com", "hotmail.com", "live.com", "msn.com"},
        "label": "Outlook.com",
        "incoming": [
            MailServerCandidate(
                protocol="imap",
                host="outlook.office365.com",
                port=993,
                security="ssl",
                source="provider_preset",
                score=100,
                notes=["Microsoft IMAP 기본값"],
            ),
            MailServerCandidate(
                protocol="pop3",
                host="outlook.office365.com",
                port=995,
                security="ssl",
                source="provider_preset",
                score=80,
                notes=["Microsoft POP3 기본값"],
            ),
        ],
        "outgoing": [
            MailServerCandidate(
                protocol="smtp",
                host="smtp-mail.outlook.com",
                port=587,
                security="starttls",
                source="provider_preset",
                score=100,
                notes=["Microsoft SMTP 기본값"],
            )
        ],
        "notes": [
            "Outlook 계정은 보안 정책에 따라 일반 비밀번호 로그인이 막힐 수 있다."
        ],
    },
}


def build_mailbox_autoconfig_plan(
    email_address: str,
    *,
    timeout_seconds: float = 5.0,
) -> MailboxAutoConfigPlan:
    """기능: 이메일 주소 기준 자동 설정 후보 계획을 만든다.

    입력:
    - email_address: 사용자 이메일 주소
    - timeout_seconds: autodiscover 요청 timeout

    반환:
    - `MailboxAutoConfigPlan`
    """

    normalized_email = email_address.strip()
    domain = normalized_email.split("@", 1)[1].lower()
    provider_key, provider_label, preset_notes = detect_provider(domain)

    incoming_candidates: list[MailServerCandidate] = []
    outgoing_candidates: list[MailServerCandidate] = []
    notes: list[str] = []

    preset = PROVIDER_PRESETS.get(provider_key)
    if preset is not None:
        incoming_candidates.extend(preset["incoming"])
        outgoing_candidates.extend(preset["outgoing"])
        notes.extend(list(preset.get("notes") or []))

    autodiscover_candidates, autodiscover_notes = fetch_mozilla_autoconfig_candidates(
        email_address=normalized_email,
        timeout_seconds=timeout_seconds,
    )
    incoming_candidates.extend(
        [item for item in autodiscover_candidates if item.protocol in {"imap", "pop3"}]
    )
    outgoing_candidates.extend(
        [item for item in autodiscover_candidates if item.protocol == "smtp"]
    )
    notes.extend(autodiscover_notes)

    generic_incoming, generic_outgoing = build_generic_domain_candidates(domain)
    incoming_candidates.extend(generic_incoming)
    outgoing_candidates.extend(generic_outgoing)
    notes.extend(preset_notes)

    imap_candidates = [
        item
        for item in dedupe_and_sort_candidates(incoming_candidates)
        if item.protocol == "imap"
    ]
    pop3_candidates = [
        item
        for item in dedupe_and_sort_candidates(incoming_candidates)
        if item.protocol == "pop3"
    ]
    smtp_candidates = dedupe_and_sort_candidates(outgoing_candidates)

    if not notes:
        notes.append("provider preset이 없어서 generic pattern 중심으로 후보를 만들었다.")

    return MailboxAutoConfigPlan(
        email_address=normalized_email,
        domain=domain,
        provider_key=provider_key,
        provider_label=provider_label,
        imap_candidates=imap_candidates,
        pop3_candidates=pop3_candidates,
        smtp_candidates=smtp_candidates,
        notes=notes,
    )


def detect_provider(domain: str) -> tuple[str, str, list[str]]:
    """기능: 도메인으로 provider preset 힌트를 추정한다.

    입력:
    - domain: 이메일 도메인

    반환:
    - `(provider_key, provider_label, notes)`
    """

    for provider_key, preset in PROVIDER_PRESETS.items():
        if domain in set(preset["domains"]):
            return provider_key, str(preset["label"]), [
                f"`{domain}` 도메인에 맞는 provider preset을 적용했다."
            ]
    return "generic", "Generic", [
        f"`{domain}` 도메인에 대한 전용 preset이 없어 generic/autodiscover 후보를 사용한다."
    ]


def build_generic_domain_candidates(
    domain: str,
) -> tuple[list[MailServerCandidate], list[MailServerCandidate]]:
    """기능: 일반 도메인 패턴으로 incoming/outgoing 후보를 만든다.

    입력:
    - domain: 이메일 도메인

    반환:
    - `(incoming 후보 목록, outgoing 후보 목록)`
    """

    incoming_candidates = [
        MailServerCandidate(
            protocol="imap",
            host=f"imap.{domain}",
            port=993,
            security="ssl",
            source="generic_pattern",
            score=60,
        ),
        MailServerCandidate(
            protocol="imap",
            host=f"mail.{domain}",
            port=993,
            security="ssl",
            source="generic_pattern",
            score=45,
        ),
        MailServerCandidate(
            protocol="pop3",
            host=f"pop.{domain}",
            port=995,
            security="ssl",
            source="generic_pattern",
            score=40,
        ),
    ]
    outgoing_candidates = [
        MailServerCandidate(
            protocol="smtp",
            host=f"smtp.{domain}",
            port=587,
            security="starttls",
            source="generic_pattern",
            score=60,
        ),
        MailServerCandidate(
            protocol="smtp",
            host=f"mail.{domain}",
            port=587,
            security="starttls",
            source="generic_pattern",
            score=45,
        ),
        MailServerCandidate(
            protocol="smtp",
            host=f"smtp.{domain}",
            port=465,
            security="ssl",
            source="generic_pattern",
            score=55,
        ),
    ]
    return incoming_candidates, outgoing_candidates


def fetch_mozilla_autoconfig_candidates(
    *,
    email_address: str,
    timeout_seconds: float = 5.0,
) -> tuple[list[MailServerCandidate], list[str]]:
    """기능: Mozilla autoconfig XML에서 후보를 읽어온다.

    입력:
    - email_address: 사용자 이메일 주소
    - timeout_seconds: 요청 timeout

    반환:
    - `(후보 목록, notes)`
    """

    domain = email_address.split("@", 1)[1].lower()
    urls = [
        f"https://autoconfig.{domain}/mail/config-v1.1.xml?emailaddress={urllib.parse.quote(email_address)}",
        f"https://{domain}/.well-known/autoconfig/mail/config-v1.1.xml?emailaddress={urllib.parse.quote(email_address)}",
    ]

    for url in urls:
        try:
            with urllib.request.urlopen(url, timeout=timeout_seconds) as response:
                xml_text = response.read().decode("utf-8", errors="replace")
            candidates = parse_mozilla_autoconfig_xml(xml_text)
            if candidates:
                return candidates, [f"Mozilla autoconfig에서 후보를 읽었다: {url}"]
        except Exception:
            continue

    return [], ["Mozilla autoconfig에서 유효한 설정을 찾지 못했다."]


def parse_mozilla_autoconfig_xml(xml_text: str) -> list[MailServerCandidate]:
    """기능: Mozilla autoconfig XML 문자열을 후보 목록으로 바꾼다.

    입력:
    - xml_text: XML 문자열

    반환:
    - 후보 목록
    """

    root = ET.fromstring(xml_text)
    email_provider = root.find(".//emailProvider")
    if email_provider is None:
        return []

    candidates: list[MailServerCandidate] = []
    for server_tag, protocol in (
        ("incomingServer", None),
        ("outgoingServer", "smtp"),
    ):
        for server in email_provider.findall(server_tag):
            resolved_protocol = protocol or str(server.attrib.get("type") or "").lower()
            if resolved_protocol == "pop3":
                resolved_protocol = "pop3"
            elif resolved_protocol == "imap":
                resolved_protocol = "imap"
            elif resolved_protocol == "smtp":
                resolved_protocol = "smtp"
            else:
                continue

            hostname = _xml_text(server, "hostname")
            port_text = _xml_text(server, "port")
            socket_type = _xml_text(server, "socketType").lower()
            username_hint = _xml_text(server, "username") or "%EMAILADDRESS%"
            auth_hint = _xml_text(server, "authentication")
            if not hostname or not port_text.isdigit():
                continue

            candidates.append(
                MailServerCandidate(
                    protocol=resolved_protocol,
                    host=hostname,
                    port=int(port_text),
                    security=normalize_security(socket_type),
                    username_hint=username_hint,
                    auth_hint=auth_hint or None,
                    source="mozilla_autoconfig",
                    score=90,
                )
            )
    return candidates


def dedupe_and_sort_candidates(
    candidates: list[MailServerCandidate],
) -> list[MailServerCandidate]:
    """기능: 후보 목록을 중복 제거 후 점수 순으로 정렬한다.

    입력:
    - candidates: 후보 목록

    반환:
    - 정렬된 후보 목록
    """

    by_key: dict[tuple[str, str, int, str], MailServerCandidate] = {}
    for candidate in candidates:
        current = by_key.get(candidate.key())
        if current is None or candidate.score > current.score:
            by_key[candidate.key()] = candidate

    return sorted(
        by_key.values(),
        key=lambda item: (-item.score, item.protocol, item.host, item.port),
    )


def run_mailbox_autoconfig_smoke(
    *,
    email_address: str,
    password: str = "",
    timeout_seconds: float = 8.0,
    max_probes_per_protocol: int = 2,
) -> MailboxAutoConfigSmokeReport:
    """기능: 자동 설정 후보 생성과 실제 probe까지 포함한 smoke를 실행한다.

    입력:
    - email_address: 테스트할 이메일 주소
    - password: 비밀번호 또는 앱 비밀번호
    - timeout_seconds: probe timeout
    - max_probes_per_protocol: 프로토콜별 probe 최대 개수

    반환:
    - `MailboxAutoConfigSmokeReport`
    """

    plan = build_mailbox_autoconfig_plan(
        email_address=email_address,
        timeout_seconds=timeout_seconds,
    )
    mode = "auth" if password else "connect"
    probe_results: list[MailServerProbeResult] = []

    candidates_by_protocol = {
        "imap": plan.imap_candidates[:max_probes_per_protocol],
        "pop3": plan.pop3_candidates[:max_probes_per_protocol],
        "smtp": plan.smtp_candidates[:max_probes_per_protocol],
    }

    for protocol_candidates in candidates_by_protocol.values():
        for candidate in protocol_candidates:
            probe_results.append(
                probe_mail_server_candidate(
                    email_address=email_address,
                    password=password,
                    candidate=candidate,
                    timeout_seconds=timeout_seconds,
                    mode=mode,
                )
            )

    recommended_incoming = choose_recommended_candidate(
        candidates=plan.imap_candidates or plan.pop3_candidates,
        probe_results=probe_results,
    )
    recommended_outgoing = choose_recommended_candidate(
        candidates=plan.smtp_candidates,
        probe_results=probe_results,
    )

    notes = list(plan.notes)
    if not password:
        notes.append("비밀번호가 없어 연결 가능 여부만 확인했다. 실제 로그인 성공 여부는 아직 미검증 상태다.")

    return MailboxAutoConfigSmokeReport(
        email_address=email_address,
        mode=mode,
        plan=plan,
        probe_results=probe_results,
        recommended_incoming=recommended_incoming,
        recommended_outgoing=recommended_outgoing,
        notes=notes,
    )


def probe_mail_server_candidate(
    *,
    email_address: str,
    password: str,
    candidate: MailServerCandidate,
    timeout_seconds: float,
    mode: str,
) -> MailServerProbeResult:
    """기능: 후보 1개에 대해 연결 또는 로그인 probe를 수행한다.

    입력:
    - email_address: 로그인 이메일 주소
    - password: 비밀번호 또는 앱 비밀번호
    - candidate: probe 대상 후보
    - timeout_seconds: timeout
    - mode: `connect` 또는 `auth`

    반환:
    - `MailServerProbeResult`
    """

    started = time.perf_counter()
    try:
        if mode == "auth":
            _probe_with_auth(
                candidate=candidate,
                email_address=email_address,
                password=password,
                timeout_seconds=timeout_seconds,
            )
            stage = "login"
            message = "로그인 성공"
        else:
            _probe_connect_only(
                host=candidate.host,
                port=candidate.port,
                timeout_seconds=timeout_seconds,
            )
            stage = "connect"
            message = "소켓 연결 성공"
        latency_ms = int((time.perf_counter() - started) * 1000)
        return MailServerProbeResult(
            protocol=candidate.protocol,
            host=candidate.host,
            port=candidate.port,
            security=candidate.security,
            mode=mode,
            success=True,
            stage=stage,
            latency_ms=latency_ms,
            source=candidate.source,
            message=message,
        )
    except Exception as exc:
        latency_ms = int((time.perf_counter() - started) * 1000)
        return MailServerProbeResult(
            protocol=candidate.protocol,
            host=candidate.host,
            port=candidate.port,
            security=candidate.security,
            mode=mode,
            success=False,
            stage="error",
            latency_ms=latency_ms,
            source=candidate.source,
            message=f"{exc.__class__.__name__}: {exc}",
        )


def choose_recommended_candidate(
    *,
    candidates: list[MailServerCandidate],
    probe_results: list[MailServerProbeResult],
) -> MailServerCandidate | None:
    """기능: 후보와 probe 결과를 바탕으로 추천 후보를 고른다.

    입력:
    - candidates: 후보 목록
    - probe_results: probe 결과 목록

    반환:
    - 추천 후보 또는 `None`
    """

    if not candidates:
        return None

    success_keys = {
        (item.protocol, item.host, item.port, item.security)
        for item in probe_results
        if item.success
    }
    for candidate in candidates:
        if candidate.key() in success_keys:
            return candidate
    return candidates[0]


def save_mailbox_autoconfig_report(
    report: MailboxAutoConfigSmokeReport,
    output_path: str | Path,
) -> Path:
    """기능: 자동 설정 smoke 결과를 JSON 파일로 저장한다.

    입력:
    - report: 저장할 smoke 결과
    - output_path: 저장 경로

    반환:
    - 저장된 `Path`
    """

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(report.to_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return path


def _probe_connect_only(*, host: str, port: int, timeout_seconds: float) -> None:
    with socket.create_connection((host, port), timeout=timeout_seconds):
        return


def _probe_with_auth(
    *,
    candidate: MailServerCandidate,
    email_address: str,
    password: str,
    timeout_seconds: float,
) -> None:
    if candidate.protocol == "imap":
        _probe_imap_auth(
            candidate=candidate,
            email_address=email_address,
            password=password,
            timeout_seconds=timeout_seconds,
        )
        return
    if candidate.protocol == "pop3":
        _probe_pop3_auth(
            candidate=candidate,
            email_address=email_address,
            password=password,
            timeout_seconds=timeout_seconds,
        )
        return
    if candidate.protocol == "smtp":
        _probe_smtp_auth(
            candidate=candidate,
            email_address=email_address,
            password=password,
            timeout_seconds=timeout_seconds,
        )
        return
    raise RuntimeError(f"지원하지 않는 protocol: {candidate.protocol}")


def _probe_imap_auth(
    *,
    candidate: MailServerCandidate,
    email_address: str,
    password: str,
    timeout_seconds: float,
) -> None:
    if candidate.security == "ssl":
        client = imaplib.IMAP4_SSL(candidate.host, candidate.port, timeout=timeout_seconds)
    else:
        client = imaplib.IMAP4(candidate.host, candidate.port, timeout=timeout_seconds)
        if candidate.security == "starttls":
            client.starttls(ssl_context=ssl.create_default_context())
    try:
        client.login(email_address, password)
    finally:
        try:
            client.logout()
        except Exception:
            pass


def _probe_pop3_auth(
    *,
    candidate: MailServerCandidate,
    email_address: str,
    password: str,
    timeout_seconds: float,
) -> None:
    if candidate.security == "ssl":
        client = poplib.POP3_SSL(candidate.host, candidate.port, timeout=timeout_seconds)
    else:
        client = poplib.POP3(candidate.host, candidate.port, timeout=timeout_seconds)
        if candidate.security == "starttls":
            client.stls(ssl.create_default_context())
    try:
        client.user(email_address)
        client.pass_(password)
    finally:
        try:
            client.quit()
        except Exception:
            pass


def _probe_smtp_auth(
    *,
    candidate: MailServerCandidate,
    email_address: str,
    password: str,
    timeout_seconds: float,
) -> None:
    if candidate.security == "ssl":
        client = smtplib.SMTP_SSL(candidate.host, candidate.port, timeout=timeout_seconds)
    else:
        client = smtplib.SMTP(candidate.host, candidate.port, timeout=timeout_seconds)
    try:
        client.ehlo()
        if candidate.security == "starttls":
            client.starttls(context=ssl.create_default_context())
            client.ehlo()
        client.login(email_address, password)
    finally:
        try:
            client.quit()
        except Exception:
            pass


def normalize_security(socket_type: str) -> str:
    """기능: provider별 보안 표기를 내부 표준값으로 맞춘다.

    입력:
    - socket_type: XML 또는 preset에서 온 보안 표기

    반환:
    - `ssl`, `starttls`, `plain`
    """

    text = socket_type.strip().lower()
    if text in {"ssl", "ssl/tls"}:
        return "ssl"
    if text in {"starttls", "tls"}:
        return "starttls"
    return "plain"


def _xml_text(element: ET.Element, tag_name: str) -> str:
    tag = element.find(tag_name)
    if tag is None or tag.text is None:
        return ""
    return tag.text.strip()
