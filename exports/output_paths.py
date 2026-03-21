"""프로필별 Excel 산출물 파일명과 최신본 선택 규칙을 모은다."""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

from project_paths import ProfilePaths

TIMESTAMPED_EXPORT_FILENAME_PATTERN = re.compile(r"^\d{6}_\d{4}_.+\.xlsx$")


def build_timestamped_export_workbook_filename(
    template_workbook_path: str | Path,
    *,
    now: datetime | None = None,
) -> str:
    """기능: 현재 시각이 들어간 프로필 export workbook 파일명을 만든다.

    입력:
    - template_workbook_path: reference 템플릿 workbook 경로
    - now: 파일명에 사용할 시각. 없으면 현재 로컬 시각

    반환:
    - `YYMMDD_HHMM_<template>.xlsx` 형식 파일명
    """

    timestamp = (now or datetime.now()).strftime("%y%m%d_%H%M")
    template_stem = sanitize_export_workbook_stem(Path(template_workbook_path).stem)
    return f"{timestamp}_{template_stem}.xlsx"


def build_timestamped_export_workbook_path(
    *,
    profile_root: str,
    template_workbook_path: str | Path,
    now: datetime | None = None,
) -> Path:
    """기능: timestamped export workbook 전체 경로를 만든다.

    입력:
    - profile_root: 사용자 프로필 루트
    - template_workbook_path: reference 템플릿 workbook 경로
    - now: 파일명에 사용할 시각

    반환:
    - `실행결과/엑셀 산출물/<timestamped>.xlsx` 경로
    """

    profile_paths = ProfilePaths(profile_root)
    return profile_paths.runtime_exports_root() / build_timestamped_export_workbook_filename(
        template_workbook_path,
        now=now,
    )


def find_latest_runtime_export_workbook(
    *,
    profile_root: str,
    exclude_paths: list[str | Path] | None = None,
) -> Path | None:
    """기능: 현재 프로필 runtime export 중 가장 최신 workbook을 찾는다.

    입력:
    - profile_root: 사용자 프로필 루트
    - exclude_paths: 제외할 workbook 경로 목록

    반환:
    - 가장 최근 수정된 `.xlsx` 경로, 없으면 `None`
    """

    profile_paths = ProfilePaths(profile_root)
    exports_root = profile_paths.runtime_exports_root()
    if not exports_root.exists():
        return None

    excluded = {
        Path(path).resolve()
        for path in (exclude_paths or [])
    }
    candidates = [
        path
        for path in exports_root.iterdir()
        if path.is_file()
        and path.suffix.lower() == ".xlsx"
        and path.resolve() not in excluded
    ]
    if not candidates:
        return None

    candidates.sort(
        key=lambda path: (path.stat().st_mtime, path.name),
        reverse=True,
    )
    return candidates[0]


def cleanup_legacy_export_workbooks(
    *,
    profile_root: str,
    keep_paths: list[str | Path] | None = None,
) -> list[Path]:
    """기능: 새 파일명 규칙과 맞지 않는 legacy export workbook을 정리한다.

    입력:
    - profile_root: 사용자 프로필 루트
    - keep_paths: 삭제에서 제외할 workbook 경로 목록

    반환:
    - 실제로 삭제한 workbook 경로 목록
    """

    profile_paths = ProfilePaths(profile_root)
    exports_root = profile_paths.runtime_exports_root()
    if not exports_root.exists():
        return []

    keep_resolved = {
        Path(path).resolve()
        for path in (keep_paths or [])
    }
    removed_paths: list[Path] = []
    for path in sorted(exports_root.iterdir()):
        if not path.is_file() or path.suffix.lower() != ".xlsx":
            continue
        if path.resolve() in keep_resolved:
            continue
        if TIMESTAMPED_EXPORT_FILENAME_PATTERN.match(path.name):
            continue
        path.unlink()
        removed_paths.append(path)
    return removed_paths


def sanitize_export_workbook_stem(template_stem: str) -> str:
    """기능: workbook 파일명용 템플릿 stem을 공백 기준 underscore 형태로 바꾼다.

    입력:
    - template_stem: 원본 템플릿 stem

    반환:
    - 파일명용 정리 문자열
    """

    text = template_stem.strip().replace(" ", "_")
    text = re.sub(r"_+", "_", text)
    return text
