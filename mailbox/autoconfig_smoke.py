"""메일 자동 설정 후보와 probe를 확인하는 CLI smoke."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from project_paths import ProfilePaths, default_example_profile_root

if __package__ in (None, ""):
    from mailbox.autoconfig import (
        build_mailbox_autoconfig_plan,
        run_mailbox_autoconfig_smoke,
        save_mailbox_autoconfig_report,
    )
else:
    from .autoconfig import (
        build_mailbox_autoconfig_plan,
        run_mailbox_autoconfig_smoke,
        save_mailbox_autoconfig_report,
    )


def default_profile_root() -> Path:
    """기능: 현재 예시 사용자 프로필 루트 기본 경로를 반환한다.

    입력:
    - 없음

    반환:
    - `secrets/사용자 설정/김정민`
    """

    return default_example_profile_root()


def default_output_report_path(profile_root: str, email_address: str) -> Path:
    """기능: 자동 설정 smoke report 기본 저장 경로를 만든다.

    입력:
    - profile_root: 사용자 프로필 루트
    - email_address: 테스트 이메일 주소

    반환:
    - JSON report 경로
    """

    profile_paths = ProfilePaths(profile_root)
    safe_name = email_address.replace("@", "_at_").replace(".", "_")
    return profile_paths.runtime_mailbox_logs_root() / f"{safe_name}_autoconfig_smoke.json"


def main() -> None:
    """기능: CLI에서 메일 자동 설정 smoke를 실행한다.

    입력:
    - 없음

    반환:
    - 없음
    """

    parser = argparse.ArgumentParser(description="mailbox autoconfig smoke")
    parser.add_argument("--email-address", required=True)
    parser.add_argument("--login-username", default="")
    parser.add_argument("--password", default="")
    parser.add_argument("--profile-root", default=str(default_profile_root()))
    parser.add_argument("--timeout-seconds", type=float, default=8.0)
    parser.add_argument("--max-probes-per-protocol", type=int, default=2)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="실제 probe 없이 후보 계획만 출력한다.",
    )
    args = parser.parse_args()

    if args.dry_run:
        plan = build_mailbox_autoconfig_plan(
            args.email_address,
            timeout_seconds=args.timeout_seconds,
        )
        print(json.dumps(plan.to_dict(), ensure_ascii=False, indent=2))
        return

    report = run_mailbox_autoconfig_smoke(
        email_address=args.email_address,
        login_username=args.login_username,
        password=args.password,
        timeout_seconds=args.timeout_seconds,
        max_probes_per_protocol=args.max_probes_per_protocol,
    )
    output_path = save_mailbox_autoconfig_report(
        report,
        default_output_report_path(args.profile_root, args.email_address),
    )
    payload = report.to_dict()
    payload["saved_report_path"] = str(output_path)
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
