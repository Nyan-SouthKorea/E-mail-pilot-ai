from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

MANIFEST_BASENAME = "portable_bundle_manifest"
MANIFEST_FILENAME = f"{MANIFEST_BASENAME}.json"
REQUIRED_RELATIVE_PATHS = (
    "EmailPilotAI.exe",
    "portable_build_info.json",
    "_internal/python310.dll",
    "_internal/python3.dll",
    "_internal/VCRUNTIME140.dll",
    "_internal/VCRUNTIME140_1.dll",
    "_internal/ucrtbase.dll",
)


def _bundle_root(path_text: str) -> Path:
    path = Path(path_text).expanduser().resolve()
    if not path.exists():
        raise FileNotFoundError(f"bundle root를 찾을 수 없다: {path}")
    if not path.is_dir():
        raise NotADirectoryError(f"bundle root는 디렉토리여야 한다: {path}")
    return path


def _is_manifest_path(path: Path) -> bool:
    return path.name.startswith(MANIFEST_BASENAME) and path.suffix == ".json"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _collect_file_entries(bundle_root: Path) -> list[dict[str, object]]:
    entries: list[dict[str, object]] = []
    for path in sorted(item for item in bundle_root.rglob("*") if item.is_file()):
        if _is_manifest_path(path):
            continue
        entries.append(
            {
                "relative_path": path.relative_to(bundle_root).as_posix(),
                "size": path.stat().st_size,
                "sha256": _sha256(path),
            }
        )
    return entries


def _missing_required_paths(bundle_root: Path) -> list[str]:
    missing: list[str] = []
    for relative_path in REQUIRED_RELATIVE_PATHS:
        if not (bundle_root / relative_path).exists():
            missing.append(relative_path)
    return missing


def _build_manifest(bundle_root: Path) -> dict[str, object]:
    return {
        "schema_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "bundle_root_name": bundle_root.name,
        "required_relative_paths": list(REQUIRED_RELATIVE_PATHS),
        "file_count": 0,
        "files": [],
    } | _build_manifest_files(bundle_root)


def _build_manifest_files(bundle_root: Path) -> dict[str, object]:
    files = _collect_file_entries(bundle_root)
    return {
        "file_count": len(files),
        "files": files,
    }


def _write_manifest(bundle_root: Path, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    manifest = _build_manifest(bundle_root)
    output_path.write_text(
        json.dumps(manifest, ensure_ascii=True, indent=2) + "\n",
        encoding="utf-8",
    )


def _load_manifest(path_text: str) -> dict[str, object]:
    path = Path(path_text).expanduser().resolve()
    if not path.exists():
        raise FileNotFoundError(f"manifest를 찾을 수 없다: {path}")
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"manifest 형식이 올바르지 않다: {path}")
    return data


def _file_map(manifest: dict[str, object]) -> dict[str, tuple[int, str]]:
    files = manifest.get("files")
    if not isinstance(files, list):
        raise ValueError("manifest files 필드가 list가 아니다.")
    mapping: dict[str, tuple[int, str]] = {}
    for entry in files:
        if not isinstance(entry, dict):
            raise ValueError("manifest file entry가 dict가 아니다.")
        relative_path = entry.get("relative_path")
        size = entry.get("size")
        sha256 = entry.get("sha256")
        if not isinstance(relative_path, str) or not isinstance(size, int) or not isinstance(sha256, str):
            raise ValueError("manifest file entry 필드가 올바르지 않다.")
        mapping[relative_path] = (size, sha256)
    return mapping


def _check_required_command(args: argparse.Namespace) -> int:
    bundle_root = _bundle_root(args.bundle_root)
    missing = _missing_required_paths(bundle_root)
    if missing:
        print("portable bundle required file check failed:", file=sys.stderr)
        for relative_path in missing:
            print(f"- missing: {relative_path}", file=sys.stderr)
        return 1
    print(f"portable bundle required file check passed: {bundle_root}")
    return 0


def _write_command(args: argparse.Namespace) -> int:
    bundle_root = _bundle_root(args.bundle_root)
    missing = _missing_required_paths(bundle_root)
    if missing:
        print("required files are missing before manifest write:", file=sys.stderr)
        for relative_path in missing:
            print(f"- missing: {relative_path}", file=sys.stderr)
        return 1
    output_path = Path(args.output).expanduser().resolve()
    _write_manifest(bundle_root, output_path)
    print(f"portable bundle manifest written: {output_path}")
    return 0


def _compare_command(args: argparse.Namespace) -> int:
    expected = _load_manifest(args.expected)
    actual = _load_manifest(args.actual)
    expected_map = _file_map(expected)
    actual_map = _file_map(actual)

    expected_paths = set(expected_map)
    actual_paths = set(actual_map)
    missing_paths = sorted(expected_paths - actual_paths)
    extra_paths = sorted(actual_paths - expected_paths)
    mismatched_paths = sorted(
        path
        for path in expected_paths & actual_paths
        if expected_map[path] != actual_map[path]
    )

    if not missing_paths and not extra_paths and not mismatched_paths:
        print("portable bundle manifest compare passed")
        return 0

    print("portable bundle manifest compare failed:", file=sys.stderr)
    for path in missing_paths:
        print(f"- missing in actual: {path}", file=sys.stderr)
    for path in extra_paths:
        print(f"- extra in actual: {path}", file=sys.stderr)
    for path in mismatched_paths:
        expected_size, expected_hash = expected_map[path]
        actual_size, actual_hash = actual_map[path]
        print(
            f"- mismatch: {path} "
            f"(expected size={expected_size} sha256={expected_hash}, "
            f"actual size={actual_size} sha256={actual_hash})",
            file=sys.stderr,
        )
    return 1


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="PyInstaller portable bundle의 필수 파일과 해시 manifest를 점검한다."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    check_required = subparsers.add_parser(
        "check-required",
        help="필수 실행 파일과 DLL이 모두 있는지 확인한다.",
    )
    check_required.add_argument("--bundle-root", required=True)
    check_required.set_defaults(func=_check_required_command)

    write = subparsers.add_parser(
        "write",
        help="portable bundle manifest를 생성한다.",
    )
    write.add_argument("--bundle-root", required=True)
    write.add_argument("--output", required=True)
    write.set_defaults(func=_write_command)

    compare = subparsers.add_parser(
        "compare",
        help="두 manifest의 파일 목록과 sha256이 같은지 비교한다.",
    )
    compare.add_argument("--expected", required=True)
    compare.add_argument("--actual", required=True)
    compare.set_defaults(func=_compare_command)

    return parser


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
