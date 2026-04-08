#!/usr/bin/env python3
"""Show a lightweight inventory before creating new files or folders."""

from __future__ import annotations

import argparse
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
KIND_MAP = {
    "docs": "docs",
    "logbook": "docs/logbook.md",
    "archive": "docs/logbook_archive",
    "reports": "docs/보고서",
    "env": "docs/환경",
    "results": "results",
    "skills": ".agents/skills",
    "tools": "tools",
    "templates": "templates",
}
SKIP_NAMES = {".git", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inspect the current repo structure before adding new files or folders."
    )
    parser.add_argument(
        "--module",
        default="root",
        help="Top-level module name such as mailbox, analysis, exports, llm, or root.",
    )
    parser.add_argument(
        "--kind",
        default="docs",
        help="Kind hint such as docs, archive, reports, env, results, skills, tools, templates.",
    )
    parser.add_argument(
        "--candidate-name",
        default="",
        help="Optional candidate name to search for similar existing paths.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Maximum number of entries to print per section.",
    )
    return parser.parse_args()


def resolve_module_path(module: str) -> Path:
    if module in {"root", ".", "/"}:
        return REPO_ROOT
    return REPO_ROOT / module


def resolve_kind_path(module_path: Path, kind: str) -> Path:
    suffix = KIND_MAP.get(kind, kind)
    return module_path / suffix if module_path != REPO_ROOT else REPO_ROOT / suffix


def list_entries(path: Path, limit: int) -> list[str]:
    if not path.exists():
        return []
    if path.is_file():
        return [path.name]
    entries = []
    for entry in sorted(path.iterdir(), key=lambda item: (item.is_file(), item.name.lower())):
        if entry.name in SKIP_NAMES:
            continue
        marker = "/" if entry.is_dir() else ""
        entries.append(f"{entry.name}{marker}")
        if len(entries) >= limit:
            break
    return entries


def find_similar_paths(candidate: str, limit: int) -> list[Path]:
    if not candidate:
        return []
    needle = candidate.lower()
    matches: list[Path] = []
    for path in REPO_ROOT.rglob("*"):
        if any(part in SKIP_NAMES for part in path.parts):
            continue
        rel = path.relative_to(REPO_ROOT)
        if needle in rel.name.lower():
            matches.append(rel)
        if len(matches) >= limit:
            break
    return matches


def print_section(title: str, lines: list[str]) -> None:
    print(f"\n[{title}]")
    if not lines:
        print("(no entries)")
        return
    for line in lines:
        print(f"- {line}")


def main() -> int:
    args = parse_args()
    module_path = resolve_module_path(args.module)
    kind_path = resolve_kind_path(module_path, args.kind)

    print(f"repo_root: {REPO_ROOT}")
    print(f"module: {args.module}")
    print(f"module_path: {module_path}")
    print(f"kind: {args.kind}")
    print(f"kind_path: {kind_path}")

    if not module_path.exists():
        print("\n[warning]")
        print("- requested module path does not exist")
        print_section(
            "top-level directories",
            [p.name + "/" for p in sorted(REPO_ROOT.iterdir()) if p.is_dir() and not p.name.startswith(".")],
        )
        return 1

    print_section("module entries", list_entries(module_path, args.limit))
    print_section("kind entries", list_entries(kind_path, args.limit))

    similar = [str(path) for path in find_similar_paths(args.candidate_name, args.limit)]
    print_section("similar paths", similar)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
