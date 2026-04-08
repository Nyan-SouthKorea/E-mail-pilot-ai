#!/usr/bin/env python3
"""Archive a logbook if it grows beyond a configured line limit."""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Archive one logbook when it exceeds the line limit."
    )
    parser.add_argument(
        "--path",
        default="docs/logbook.md",
        help="Logbook path relative to the repo root.",
    )
    parser.add_argument(
        "--max-lines",
        type=int,
        default=1000,
        help="Archive when the file exceeds this line count.",
    )
    parser.add_argument(
        "--archive-if-needed",
        action="store_true",
        help="Perform the archive instead of only printing the current status.",
    )
    return parser.parse_args()


def infer_context(logbook_path: Path) -> tuple[str, str]:
    if logbook_path == REPO_ROOT / "docs" / "logbook.md":
        return "project", "project"
    module_name = logbook_path.parent.parent.name
    return "module", module_name


def build_skeleton(kind: str, name: str) -> str:
    if kind == "project":
        return """# Logbook

> 이 문서는 프로젝트 레벨의 단일 기록 문서다.
> 읽을 때는 항상 현재 `docs/logbook.md`와 최신 `docs/logbook_archive/logbook_*.md` 1개를 함께 본다.

## 읽기 규칙

- 이 문서는 `현재 프로젝트 스냅샷`, `현재 전역 결정`, `현재 활성 체크리스트`, `최근 로그`를 함께 유지한다.
- 새 로그를 쓰기 전에는 항상 아래 명령을 먼저 실행한다.
  - `python tools/logbook_archive_guard.py --archive-if-needed`
- active logbook 줄 수가 `1000`을 넘으면 현재 파일을 `docs/logbook_archive/logbook_YYMMDD_HHMM_*.md`로 archive하고, active logbook는 고정 섹션만 남긴 채 다시 시작한다.

## 현재 프로젝트 스냅샷

- archive 뒤 다시 채울 current truth를 여기에 적는다.

## 현재 전역 결정

- archive 뒤에도 유효한 전역 결정만 남긴다.

## 현재 활성 체크리스트

- [ ] archive 뒤 current truth와 checklist를 다시 채운다.

## 최근 로그

### {date} | Logbook Archive Guard

- 이전 active logbook를 archive로 내리고, 새 active logbook를 고정 섹션만 남긴 상태로 다시 시작했다.
""".format(date=datetime.now().strftime("%Y-%m-%d"))

    return """# {name_title} Logbook

> 이 문서는 `{name}` 모듈의 현재 상태, 활성 체크리스트, 최근 기록을 유지한다.

## 읽기 규칙

- 비사소한 작업 전에는 `../../AGENTS.md -> ../../README.md -> ../../docs/logbook.md -> ../README.md -> ./logbook.md` 순서로 다시 읽는다.
- 새 로그를 쓰기 전에는 가능하면 `python tools/logbook_archive_guard.py --path {name}/docs/logbook.md --archive-if-needed`를 먼저 실행한다.

## 현재 스냅샷

- archive 뒤 다시 채울 current truth를 여기에 적는다.

## 현재 활성 체크리스트

- [ ] archive 뒤 모듈 current truth와 checklist를 다시 채운다.

## 최근 로그

### {date} | Logbook Archive Guard

- 이전 active logbook를 archive로 내리고, 새 active logbook를 고정 섹션만 남긴 상태로 다시 시작했다.
""".format(
        name=name,
        name_title=name.capitalize(),
        date=datetime.now().strftime("%Y-%m-%d"),
    )


def archive_if_needed(logbook_path: Path, max_lines: int, do_archive: bool) -> int:
    if not logbook_path.exists():
        print(f"missing: {logbook_path}")
        return 1

    content = logbook_path.read_text(encoding="utf-8")
    line_count = len(content.splitlines())
    print(f"path: {logbook_path.relative_to(REPO_ROOT)}")
    print(f"lines: {line_count}")
    print(f"max_lines: {max_lines}")

    if line_count <= max_lines:
        print("status: within_limit")
        return 0

    print("status: over_limit")
    if not do_archive:
        return 0

    kind, name = infer_context(logbook_path)
    archive_dir = logbook_path.parent / "logbook_archive"
    archive_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%y%m%d_%H%M")
    suffix = "project" if kind == "project" else name
    archive_path = archive_dir / f"logbook_{timestamp}_{suffix}.md"
    archive_path.write_text(content, encoding="utf-8")
    logbook_path.write_text(build_skeleton(kind, name), encoding="utf-8")
    print(f"archived_to: {archive_path.relative_to(REPO_ROOT)}")
    return 0


def main() -> int:
    args = parse_args()
    logbook_path = (REPO_ROOT / args.path).resolve()
    return archive_if_needed(
        logbook_path=logbook_path,
        max_lines=args.max_lines,
        do_archive=args.archive_if_needed,
    )


if __name__ == "__main__":
    raise SystemExit(main())
