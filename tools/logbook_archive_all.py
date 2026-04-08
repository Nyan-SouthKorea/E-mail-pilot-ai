#!/usr/bin/env python3
"""Archive the root and module logbooks when needed."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))

from logbook_archive_guard import archive_if_needed  # noqa: E402


SKIP_DIRS = {"docs", "tools", "templates"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check the root and module logbooks and archive the oversized ones."
    )
    parser.add_argument(
        "--max-lines",
        type=int,
        default=1000,
        help="Archive when a logbook exceeds this line count.",
    )
    parser.add_argument(
        "--archive-if-needed",
        action="store_true",
        help="Perform archive actions instead of only printing status.",
    )
    return parser.parse_args()


def discover_logbooks() -> list[Path]:
    logbooks = [REPO_ROOT / "docs" / "logbook.md"]
    for child in sorted(REPO_ROOT.iterdir()):
        if not child.is_dir() or child.name.startswith(".") or child.name in SKIP_DIRS:
            continue
        candidate = child / "docs" / "logbook.md"
        if candidate.exists():
            logbooks.append(candidate)
    return logbooks


def main() -> int:
    args = parse_args()
    exit_code = 0
    for logbook_path in discover_logbooks():
        print("=" * 60)
        result = archive_if_needed(
            logbook_path=logbook_path,
            max_lines=args.max_lines,
            do_archive=args.archive_if_needed,
        )
        exit_code = max(exit_code, result)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
