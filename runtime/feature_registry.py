"""기능 카탈로그와 관리도구/CLI 실행 진입점을 정의한다."""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
import importlib.util
import os
from pathlib import Path
import subprocess
from typing import Any, Iterator

from analysis import run_inbox_review_board_smoke
from llm import OpenAIResponsesConfig, OpenAIResponsesWrapper
from mailbox import build_local_mailbox_account_config, run_imap_inbox_backfill_smoke
from mailbox.imap_backfill_smoke import default_backfill_report_path
from runtime.lockfile import WorkspaceWriteLockHandle, acquire_workspace_write_lock
from runtime.review_state import ingest_review_report_into_state
from runtime.sample_workspace import create_sample_workspace
from runtime.secrets_store import WorkspaceSecretsStore
from runtime.state_store import WorkspaceStateStore
from runtime.sync_service import rebuild_operating_workbook, run_workspace_sync, update_latest_review_pointers
from runtime.workspace import SharedWorkspace, load_shared_workspace


@dataclass(frozen=True, slots=True)
class FeatureSpec:
    """기능: 제품/운영 기능 1개의 canonical 정의를 표현한다."""

    feature_id: str
    title: str
    summary: str
    owner_module: str
    audience: str
    access_modes: tuple[str, ...]
    ui_route: str | None = None
    admin_route: str | None = None
    cli_command: str | None = None
    service_entry: str | None = None
    prerequisites: tuple[str, ...] = ()
    outputs: tuple[str, ...] = ()
    result_paths: tuple[str, ...] = ()
    test_scenarios: tuple[str, ...] = ()
    manual_acceptance_required: bool = False
    supports_run: bool = False
    supports_check: bool = True
    requires_workspace: bool = True
    requires_write_lock: bool = False
    windows_only: bool = False

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(slots=True)
class FeatureCheckResult:
    """기능: feature prerequisite check 한 줄 결과를 표현한다."""

    label: str
    status: str
    detail: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(slots=True)
class FeatureRunResult:
    """기능: feature run 결과를 표현한다."""

    feature_id: str
    title: str
    status: str
    summary: str
    outputs: dict[str, object] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)
    feature_run_id: int | None = None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(slots=True)
class WorkspaceFeatureContext:
    """기능: workspace 기반 feature 실행에 필요한 공통 문맥을 묶는다."""

    workspace: SharedWorkspace
    secrets_store: WorkspaceSecretsStore
    state_store: WorkspaceStateStore
    secrets_payload: dict[str, Any]
    app_kind: str
    existing_lock_handle: WorkspaceWriteLockHandle | None = None
    force_lock_takeover: bool = False


REPO_ROOT = Path(__file__).resolve().parents[1]
PORTABLE_SPEC_PATH = REPO_ROOT / "app" / "packaging" / "EmailPilotAI.spec"
PORTABLE_BUILD_SCRIPT_PATH = REPO_ROOT / "app" / "packaging" / "build_portable_exe.ps1"
PORTABLE_SMOKE_SCRIPT_PATH = REPO_ROOT / "app" / "packaging" / "smoke_portable_exe.ps1"


def _safe_find_spec(module_name: str):
    try:
        return importlib.util.find_spec(module_name)
    except ModuleNotFoundError:
        return None


FEATURE_SPECS: tuple[FeatureSpec, ...] = (
    FeatureSpec(
        feature_id="app.desktop.launch",
        title="데스크톱 앱 실행",
        summary="전용 창 기준으로 앱 UI를 띄우고, 필요할 때만 브라우저 fallback을 쓴다.",
        owner_module="app",
        audience="user",
        access_modes=("ui", "cli"),
        ui_route="/",
        cli_command="python app/main.py [--browser-fallback|--no-window]",
        service_entry="app.main:main",
        prerequisites=("Python dependencies installed", "workspace optional"),
        outputs=("local desktop window",),
        result_paths=("local server process only",),
        test_scenarios=("앱 창 열기", "홈/설정/리뷰/관리 화면 이동"),
        manual_acceptance_required=True,
        supports_run=False,
        requires_workspace=False,
    ),
    FeatureSpec(
        feature_id="diagnostics.picker_bridge",
        title="파일 탐색기 진단",
        summary="네이티브 파일 탐색기 self-test와 picker 호출 경로를 확인한다.",
        owner_module="runtime",
        audience="operator",
        access_modes=("ui", "cli"),
        ui_route="/",
        cli_command="python -m runtime.cli diagnostics picker-bridge",
        service_entry="runtime.diagnostics_service:picker_bridge_self_test",
        prerequisites=("Windows host for real dialog",),
        outputs=("bridge diagnostics",),
        result_paths=("none",),
        test_scenarios=("native dialog self-test", "picker route smoke", "manual acceptance"),
        manual_acceptance_required=True,
        supports_run=False,
        requires_workspace=False,
    ),
    FeatureSpec(
        feature_id="diagnostics.pick_folder",
        title="폴더 선택 호출",
        summary="네이티브 폴더 선택창을 열어 선택 결과를 반환한다.",
        owner_module="runtime",
        audience="operator",
        access_modes=("ui", "cli"),
        ui_route="/",
        cli_command="python -m runtime.cli diagnostics pick-folder --workspace-root <path>",
        service_entry="runtime.diagnostics_service:pick_folder_native",
        prerequisites=("Windows host for real dialog",),
        outputs=("selected folder path",),
        result_paths=("none",),
        test_scenarios=("picker route smoke", "Windows manual dialog open"),
        manual_acceptance_required=True,
        supports_run=False,
        requires_workspace=False,
    ),
    FeatureSpec(
        feature_id="diagnostics.pick_file",
        title="파일 선택 호출",
        summary="네이티브 파일 선택창을 열어 선택 결과를 반환한다.",
        owner_module="runtime",
        audience="operator",
        access_modes=("ui", "cli"),
        ui_route="/settings",
        cli_command="python -m runtime.cli diagnostics pick-file --workspace-root <path>",
        service_entry="runtime.diagnostics_service:pick_file_native",
        prerequisites=("Windows host for real dialog",),
        outputs=("selected file path",),
        result_paths=("none",),
        test_scenarios=("picker route smoke", "Windows manual dialog open"),
        manual_acceptance_required=True,
        supports_run=False,
        requires_workspace=False,
    ),
    FeatureSpec(
        feature_id="mailbox.connection_check",
        title="계정 연결 확인",
        summary="저장된 메일 계정으로 실제 로그인 가능 여부와 추천 폴더를 확인한다.",
        owner_module="mailbox",
        audience="user",
        access_modes=("ui", "cli"),
        ui_route="/settings",
        cli_command="python -m runtime.cli mailbox connect-check --workspace-root <path> --workspace-password <pw>",
        service_entry="runtime.mailbox_service:run_mailbox_connection_check_service",
        prerequisites=("email address", "mail password"),
        outputs=("connection status", "available folders", "recommended folder"),
        result_paths=("secure/secrets.enc.json",),
        test_scenarios=("실제 로그인 확인", "폴더 목록 추천", "친화적 오류 메시지"),
        supports_run=False,
    ),
    FeatureSpec(
        feature_id="runtime.workspace.create_sample",
        title="샘플 워크스페이스 생성",
        summary="실메일 없이도 리뷰센터와 workbook 재반영을 검증할 수 있는 샘플 세이브를 만든다.",
        owner_module="runtime",
        audience="operator",
        access_modes=("cli",),
        cli_command="python -m runtime.cli create-sample-workspace --workspace-root <path> --workspace-password <pw>",
        service_entry="runtime.sample_workspace:create_sample_workspace",
        prerequisites=("target workspace root writable",),
        outputs=("workspace manifest", "sample bundles", "review board", "operating workbook"),
        result_paths=("workspace/mail/*", "workspace/exports/*", "workspace/logs/*"),
        test_scenarios=("샘플 세이브 생성", "앱에서 세이브 불러오기", "리뷰센터/재반영 검증"),
        supports_run=True,
        requires_workspace=False,
    ),
    FeatureSpec(
        feature_id="runtime.workspace.inspect",
        title="워크스페이스 점검",
        summary="현재 세이브의 설정, state counts, 최신 sync 상태를 읽는다.",
        owner_module="runtime",
        audience="operator",
        access_modes=("admin", "cli"),
        admin_route="/admin/features",
        cli_command="python -m runtime.cli workspace status --workspace-root <path> --workspace-password <pw>",
        service_entry="runtime.workspace_service:inspect_workspace_entry",
        prerequisites=("workspace manifest exists",),
        outputs=("workspace summary",),
        result_paths=("state/state.sqlite", "secure/secrets.enc.json", "workspace.epa-workspace.json"),
        test_scenarios=("상태 점검", "최근 결과 링크 확인"),
        supports_run=True,
    ),
    FeatureSpec(
        feature_id="mailbox.live_backfill",
        title="실메일 INBOX backfill",
        summary="현재 공유 설정으로 IMAP INBOX를 read-only backfill 해 runtime bundle을 채운다.",
        owner_module="mailbox",
        audience="operator",
        access_modes=("admin", "cli"),
        admin_route="/admin/features",
        cli_command="python -m runtime.cli mailbox fetch --workspace-root <path> --workspace-password <pw> --limit N|--all",
        service_entry="runtime.mailbox_service:run_mailbox_fetch_service",
        prerequisites=("mailbox credentials saved", "workspace write access"),
        outputs=("backfill report", "runtime bundles"),
        result_paths=("mail/bundles/", "logs/mailbox/"),
        test_scenarios=("실메일 read-only fetch", "중복 bundle skip", "report 생성"),
        supports_run=True,
        requires_write_lock=True,
    ),
    FeatureSpec(
        feature_id="analysis.review_board_refresh",
        title="리뷰보드 재생성",
        summary="현재 bundle 전체를 재분석하고 review board JSON/HTML과 state DB를 새로 만든다.",
        owner_module="analysis",
        audience="operator",
        access_modes=("admin", "cli"),
        admin_route="/admin/features",
        cli_command="python -m runtime.cli analysis review-refresh --workspace-root <path> --workspace-password <pw> --limit N|--all",
        service_entry="runtime.analysis_service:refresh_review_board_service",
        prerequisites=("template workbook exists", "OpenAI API key saved", "at least one valid bundle"),
        outputs=("review board json/html", "updated sqlite review state"),
        result_paths=("logs/review/", "state/state.sqlite"),
        test_scenarios=("전량 triage 재실행", "latest pointer 갱신", "리뷰센터 반영"),
        supports_run=True,
        requires_write_lock=True,
    ),
    FeatureSpec(
        feature_id="analysis.review_list",
        title="리뷰 목록 조회",
        summary="현재 필터와 페이지 기준으로 가벼운 리뷰 목록 1페이지를 읽는다.",
        owner_module="analysis",
        audience="user",
        access_modes=("ui", "cli"),
        ui_route="/review",
        cli_command="python -m runtime.cli analysis review-list --workspace-root <path> --page 1 --page-size 50 --sort received_desc",
        service_entry="runtime.analysis_service:load_review_center_page_service",
        prerequisites=("workspace manifest exists", "review state available"),
        outputs=("paged review items", "filtered total count", "selected bundle id"),
        result_paths=("state/state.sqlite",),
        test_scenarios=("리뷰 1페이지 조회", "필터/정렬/페이지네이션", "selected bundle 선택"),
        supports_run=False,
    ),
    FeatureSpec(
        feature_id="analysis.review_item",
        title="리뷰 상세 조회",
        summary="선택한 bundle 1건의 상세와 원본/산출물 상대경로를 읽는다.",
        owner_module="analysis",
        audience="user",
        access_modes=("ui", "cli"),
        ui_route="/review",
        cli_command="python -m runtime.cli analysis review-item --workspace-root <path> --bundle-id <bundle_id>",
        service_entry="runtime.analysis_service:load_review_detail_service",
        prerequisites=("workspace manifest exists", "review state available", "bundle id"),
        outputs=("selected review item",),
        result_paths=("state/state.sqlite", "mail/bundles/", "logs/analysis/", "logs/app/exports/"),
        test_scenarios=("리뷰 상세 1건 조회", "앱 안 미리보기 source 확인"),
        supports_run=False,
    ),
    FeatureSpec(
        feature_id="exports.operating_workbook.rebuild",
        title="운영 workbook 재반영",
        summary="현재 review state 기준 엑셀 반영 대상으로 선택된 신청 메일만 운영 workbook과 검토 인덱스로 다시 쓴다.",
        owner_module="exports",
        audience="operator",
        access_modes=("ui", "admin", "cli"),
        ui_route="/review",
        admin_route="/admin/features",
        cli_command="python -m runtime.cli exports rebuild --workspace-root <path> --workspace-password <pw>",
        service_entry="runtime.exports_service:rebuild_operating_workbook_service",
        prerequisites=("template workbook exists", "review state available"),
        outputs=("operating workbook", "snapshot workbook", "review index sheet"),
        result_paths=("exports/output/", "state/state.sqlite"),
        test_scenarios=("엑셀 반영 대상만 workbook 반영", "검토_인덱스 시트 확인"),
        supports_run=True,
        requires_write_lock=True,
    ),
    FeatureSpec(
        feature_id="exports.summary",
        title="엑셀 반영 요약",
        summary="현재 운영본, 스냅샷, 반영 대상 수를 보조 결과물 관점에서 읽는다.",
        owner_module="exports",
        audience="user",
        access_modes=("ui", "cli"),
        ui_route="/review",
        cli_command="python -m runtime.cli exports summary --workspace-root <path>",
        service_entry="runtime.exports_service:load_exports_summary_service",
        prerequisites=("workspace manifest exists",),
        outputs=("operating workbook summary", "snapshot list"),
        result_paths=("exports/output/", "state/state.sqlite"),
        test_scenarios=("운영본 경로 확인", "스냅샷 목록 확인", "엑셀 반영 대상 수 확인"),
        supports_run=False,
    ),
    FeatureSpec(
        feature_id="runtime.workspace.sync.quick_smoke",
        title="빠른 테스트 동기화",
        summary="최근 10건만 증분으로 가져와 review와 workbook까지 빠르게 점검한다.",
        owner_module="runtime",
        audience="user",
        access_modes=("ui", "admin", "cli"),
        ui_route="/sync",
        admin_route="/admin/features",
        cli_command="python -m runtime.cli pipeline sync --workspace-root <path> --workspace-password <pw> --scope recent --limit 10",
        service_entry="runtime.pipeline_service:run_pipeline_sync_service",
        prerequisites=("mailbox credentials saved", "template workbook exists", "OpenAI API key saved", "workspace write access"),
        outputs=("backfill report", "review board", "operating workbook"),
        result_paths=("logs/", "exports/output/"),
        test_scenarios=("최근 10건 smoke", "기존 bundle/analysis 재사용", "review center 갱신"),
        supports_run=True,
        requires_write_lock=True,
    ),
    FeatureSpec(
        feature_id="runtime.workspace.sync",
        title="전체 동기화",
        summary="backfill -> review board -> workbook 재구성을 한 번에 수행한다.",
        owner_module="runtime",
        audience="user",
        access_modes=("ui", "admin", "cli"),
        ui_route="/",
        admin_route="/admin/features",
        cli_command="python -m runtime.cli pipeline sync --workspace-root <path> --workspace-password <pw> --scope recent --limit 500|1000 or --scope all",
        service_entry="runtime.pipeline_service:run_pipeline_sync_service",
        prerequisites=("mailbox credentials saved", "template workbook exists", "OpenAI API key saved", "workspace write access"),
        outputs=("backfill report", "review board", "operating workbook"),
        result_paths=("logs/", "exports/output/"),
        test_scenarios=("실메일 동기화", "review center 갱신", "workbook 재반영"),
        supports_run=True,
        requires_write_lock=True,
    ),
    FeatureSpec(
        feature_id="packaging.portable_exe.build",
        title="포터블 exe 빌드 준비",
        summary="오프라인 자산과 PyInstaller spec 기준으로 Windows 포터블 exe를 빌드하고 공식 D 로컬 실행본으로 publish 한다.",
        owner_module="app",
        audience="operator",
        access_modes=("admin", "cli", "docs"),
        admin_route="/admin/features",
        cli_command="python -m runtime.cli feature-run --feature-id packaging.portable_exe.build",
        service_entry="app/packaging/build_portable_exe.ps1",
        prerequisites=("Windows host or Windows CI", "PyInstaller installed", "offline static assets present"),
        outputs=(
            "D:/EmailPilotAI/portable/EmailPilotAI/EmailPilotAI.exe",
            "D:/EmailPilotAI/portable/EmailPilotAI/portable_bundle_manifest.json",
        ),
        result_paths=(
            "app/packaging/EmailPilotAI.spec",
            "app/packaging/build_windows_portable_and_publish.sh",
            "app/packaging/publish_portable_to_runtime.ps1",
            "app/packaging/portable_bundle_manifest.py",
            "app/packaging/smoke_portable_exe.ps1",
            "app/static/",
            "D:/EmailPilotAI/portable/EmailPilotAI/",
        ),
        test_scenarios=(
            "Windows onedir build",
            "offline UI boot",
            "official runtime publish and smoke",
            "required DLL check",
            "temporary build artifact cleanup",
            "backports warning check",
        ),
        supports_run=True,
        supports_check=True,
        requires_workspace=False,
        windows_only=True,
    ),
)


def list_feature_specs() -> list[FeatureSpec]:
    return list(FEATURE_SPECS)


def get_feature_spec(feature_id: str) -> FeatureSpec:
    for spec in FEATURE_SPECS:
        if spec.feature_id == feature_id:
            return spec
    raise KeyError(f"알 수 없는 feature_id다: {feature_id}")


def feature_catalog_rows() -> list[dict[str, object]]:
    return [spec.to_dict() for spec in FEATURE_SPECS]


def check_feature(
    *,
    feature_id: str,
    workspace_root: str | Path | None = None,
    workspace_password: str | None = None,
) -> list[FeatureCheckResult]:
    spec = get_feature_spec(feature_id)
    if feature_id == "packaging.portable_exe.build":
        return _check_packaging_feature()

    if feature_id == "app.desktop.launch":
        return [
            FeatureCheckResult(
                label="pywebview_installed",
                status="pass" if importlib.util.find_spec("webview") is not None else "fail",
                detail="전용 창 실행에는 pywebview가 필요하다.",
            ),
            FeatureCheckResult(
                label="workspace_optional",
                status="pass" if workspace_root else "warn",
                detail="앱은 워크스페이스 없이도 시작되지만, 실제 검증은 공유 워크스페이스를 열고 진행한다.",
            ),
            FeatureCheckResult(
                label="offline_static_assets",
                status="pass" if (REPO_ROOT / "app" / "static").exists() else "fail",
                detail=str(REPO_ROOT / "app" / "static"),
            ),
        ]

    if feature_id == "runtime.workspace.create_sample":
        return [
            FeatureCheckResult(
                label="workspace_root",
                status="pass" if workspace_root else "warn",
                detail="새 sample workspace를 만들 대상 폴더가 있으면 바로 생성할 수 있다.",
            )
        ]

    context = _load_workspace_context(
        workspace_root=workspace_root,
        workspace_password=workspace_password,
        app_kind="feature-check",
    )
    checks = [
        FeatureCheckResult(
            label="workspace_manifest",
            status="pass",
            detail=str(context.workspace.manifest_path()),
        ),
    ]
    if feature_id == "mailbox.connection_check":
        return [
            FeatureCheckResult(
                label="ui_only_feature",
                status="pass",
                detail="계정 연결 확인은 설정 화면에서 직접 실행한다.",
            )
        ]

    if feature_id in {"runtime.workspace.inspect", "runtime.workspace.sync", "runtime.workspace.sync.quick_smoke"}:
        checks.extend(_workspace_common_checks(context))
    if feature_id in {"mailbox.live_backfill", "runtime.workspace.sync", "runtime.workspace.sync.quick_smoke"}:
        checks.extend(_mailbox_checks(context))
    if feature_id in {"analysis.review_board_refresh", "runtime.workspace.sync", "runtime.workspace.sync.quick_smoke"}:
        checks.extend(_analysis_checks(context))
    if feature_id in {"exports.operating_workbook.rebuild", "runtime.workspace.sync", "runtime.workspace.sync.quick_smoke"}:
        checks.extend(_exports_checks(context))
    return checks


def run_feature(
    *,
    feature_id: str,
    workspace_root: str | Path | None = None,
    workspace_password: str | None = None,
    app_kind: str = "server-tool",
    trigger_source: str = "cli",
    force_lock_takeover: bool = False,
    existing_lock_handle: WorkspaceWriteLockHandle | None = None,
) -> FeatureRunResult:
    spec = get_feature_spec(feature_id)
    if not spec.supports_run:
        raise RuntimeError(f"이 feature는 직접 run을 지원하지 않는다: {feature_id}")

    if feature_id == "runtime.workspace.create_sample":
        if workspace_root is None or workspace_password is None:
            raise RuntimeError("샘플 워크스페이스 생성에는 root와 password가 필요하다.")
        result = create_sample_workspace(
            workspace_root=workspace_root,
            workspace_password=workspace_password,
        )
        return FeatureRunResult(
            feature_id=spec.feature_id,
            title=spec.title,
            status="completed",
            summary="샘플 워크스페이스를 생성했다.",
            outputs=result.to_dict(),
            notes=result.notes,
        )
    if feature_id == "packaging.portable_exe.build":
        return _run_packaging_build(spec=spec)

    context = _load_workspace_context(
        workspace_root=workspace_root,
        workspace_password=workspace_password,
        app_kind=app_kind,
        existing_lock_handle=existing_lock_handle,
        force_lock_takeover=force_lock_takeover,
    )
    feature_run_id = context.state_store.start_feature_run(
        feature_id=feature_id,
        app_kind=app_kind,
        trigger_source=trigger_source,
        metadata={"workspace_id": context.workspace.manifest.workspace_id},
    )
    try:
        if feature_id == "runtime.workspace.inspect":
            result = _run_workspace_inspect(context=context, spec=spec)
        elif feature_id == "mailbox.live_backfill":
            result = _run_mailbox_backfill(context=context, spec=spec)
        elif feature_id == "analysis.review_board_refresh":
            result = _run_review_refresh(context=context, spec=spec)
        elif feature_id == "exports.operating_workbook.rebuild":
            result = _run_workbook_rebuild(context=context, spec=spec)
        elif feature_id == "runtime.workspace.sync.quick_smoke":
            result = _run_workspace_sync_feature(
                context=context,
                spec=spec,
                sync_mode="quick_smoke",
            )
        elif feature_id == "runtime.workspace.sync":
            result = _run_workspace_sync_feature(
                context=context,
                spec=spec,
                sync_mode="incremental_full",
            )
        else:
            raise RuntimeError(f"runner가 정의되지 않은 feature다: {feature_id}")

        result.feature_run_id = feature_run_id
        context.state_store.finish_feature_run(
            feature_run_id,
            status=result.status,
            outputs=result.outputs,
            notes=result.notes,
        )
        return result
    except Exception as exc:
        context.state_store.finish_feature_run(
            feature_run_id,
            status="failed",
            outputs={},
            notes=[],
            error_summary=f"{exc.__class__.__name__}: {exc}",
        )
        raise


def _run_workspace_inspect(
    *,
    context: WorkspaceFeatureContext,
    spec: FeatureSpec,
) -> FeatureRunResult:
    latest_feature_runs = [
        item
        for item in context.state_store.latest_feature_runs()
        if not (item.get("feature_id") == spec.feature_id and item.get("status") == "running")
    ]
    outputs = {
        "workspace_root": str(context.workspace.root()),
        "manifest_path": context.workspace.to_workspace_relative(context.workspace.manifest_path()),
        "state_counts": context.state_store.summary_counts(),
        "latest_sync_run": context.state_store.latest_sync_run(),
        "latest_feature_runs": latest_feature_runs,
    }
    return FeatureRunResult(
        feature_id=spec.feature_id,
        title=spec.title,
        status="completed",
        summary="현재 워크스페이스 상태를 읽었다.",
        outputs=outputs,
        notes=[],
    )


def _run_mailbox_backfill(
    *,
    context: WorkspaceFeatureContext,
    spec: FeatureSpec,
) -> FeatureRunResult:
    mailbox_settings = dict(context.secrets_payload.get("mailbox") or {})
    account_config = build_local_mailbox_account_config(
        email_address=str(mailbox_settings.get("email_address") or ""),
        login_username=str(mailbox_settings.get("login_username") or ""),
        password=str(mailbox_settings.get("password") or ""),
        profile_root=context.workspace.profile_root(),
        source_path="workspace.encrypted_settings",
        notes=["공유 워크스페이스 관리 화면 또는 CLI에서 backfill을 실행했다."],
    )
    with _workspace_lock(context):
        report = run_imap_inbox_backfill_smoke(
            account_config=account_config,
            folder=str(mailbox_settings.get("default_folder") or "INBOX"),
        )
        if context.existing_lock_handle is not None:
            context.existing_lock_handle.refresh()
    report_path = default_backfill_report_path(
        str(context.workspace.profile_root()),
        account_config.email_address,
    )
    outputs = {
        "backfill_report_path": context.workspace.to_workspace_relative(report_path),
        "success": report.success,
        "total_message_count": report.total_message_count,
        "fetched_count": report.fetched_count,
        "skipped_existing_count": report.skipped_existing_count,
        "failed_count": report.failed_count,
    }
    return FeatureRunResult(
        feature_id=spec.feature_id,
        title=spec.title,
        status="completed" if report.success else "failed",
        summary="실메일 INBOX backfill을 실행했다.",
        outputs=outputs,
        notes=report.notes,
    )


def _run_review_refresh(
    *,
    context: WorkspaceFeatureContext,
    spec: FeatureSpec,
) -> FeatureRunResult:
    template_path = _resolve_template_workbook_path(context)
    wrapper = _build_wrapper(context)
    with _workspace_lock(context):
        report = run_inbox_review_board_smoke(
            profile_id="shared-workspace",
            profile_root=str(context.workspace.profile_root()),
            template_path=str(template_path),
            reuse_existing_analysis=True,
            wrapper=wrapper,
        )
        update_latest_review_pointers(workspace=context.workspace, review_report=report)
        items = ingest_review_report_into_state(
            workspace=context.workspace,
            state_store=context.state_store,
            report_path=report.review_json_path,
            wrapper=wrapper,
        )
        if context.existing_lock_handle is not None:
            context.existing_lock_handle.refresh()
    outputs = {
        "review_json_path": context.workspace.to_workspace_relative(report.review_json_path),
        "review_html_path": context.workspace.to_workspace_relative(report.review_html_path),
        "total_bundle_count": report.total_bundle_count,
        "application_count": report.application_count,
        "not_application_count": report.not_application_count,
        "needs_human_review_count": report.needs_human_review_count,
        "state_item_count": len(items),
    }
    return FeatureRunResult(
        feature_id=spec.feature_id,
        title=spec.title,
        status="completed",
        summary="review board와 sqlite review state를 새로 만들었다.",
        outputs=outputs,
        notes=report.notes,
    )


def _run_workbook_rebuild(
    *,
    context: WorkspaceFeatureContext,
    spec: FeatureSpec,
) -> FeatureRunResult:
    template_path = _resolve_template_workbook_path(context)
    wrapper = _build_wrapper(context)
    latest_review_json = context.workspace.review_logs_root() / "latest_inbox_review_board.json"
    with _workspace_lock(context):
        if context.state_store.summary_counts().get("total", 0) == 0 and latest_review_json.exists():
            ingest_review_report_into_state(
                workspace=context.workspace,
                state_store=context.state_store,
                report_path=latest_review_json,
                wrapper=wrapper,
            )
        result = rebuild_operating_workbook(
            workspace=context.workspace,
            state_store=context.state_store,
            template_path=template_path,
            wrapper=wrapper,
        )
        if context.existing_lock_handle is not None:
            context.existing_lock_handle.refresh()
    outputs = {
        "operating_workbook_path": result["operating_workbook_relpath"],
        "export_included_count": result["export_included_count"],
    }
    return FeatureRunResult(
        feature_id=spec.feature_id,
        title=spec.title,
        status="completed",
        summary="운영 workbook과 검토 인덱스를 다시 썼다.",
        outputs=outputs,
        notes=[],
    )


def _run_workspace_sync_feature(
    *,
    context: WorkspaceFeatureContext,
    spec: FeatureSpec,
    sync_mode: str,
) -> FeatureRunResult:
    result = run_workspace_sync(
        workspace_root=context.workspace.root(),
        workspace_password=str(context.secrets_payload.get("__workspace_password__") or ""),
        app_kind=context.app_kind,
        sync_mode=sync_mode,
        force_lock_takeover=context.force_lock_takeover,
        write_lock_handle=context.existing_lock_handle,
    )
    return FeatureRunResult(
        feature_id=spec.feature_id,
        title=spec.title,
        status="completed",
        summary=(
            "최근 10건 기준 빠른 테스트 동기화를 완료했다."
            if sync_mode == "quick_smoke"
            else "backfill -> review board -> workbook 재구성을 한 번에 완료했다."
        ),
        outputs=result.to_dict(),
        notes=result.notes,
    )


def _load_workspace_context(
    *,
    workspace_root: str | Path | None,
    workspace_password: str | None,
    app_kind: str,
    existing_lock_handle: WorkspaceWriteLockHandle | None = None,
    force_lock_takeover: bool = False,
) -> WorkspaceFeatureContext:
    if workspace_root is None:
        raise RuntimeError("workspace_root가 필요하다.")
    if workspace_password is None:
        raise RuntimeError("workspace_password가 필요하다.")
    workspace = load_shared_workspace(workspace_root)
    secrets_store = WorkspaceSecretsStore(
        path=str(workspace.secure_blob_path()),
        password=workspace_password,
    )
    state_store = WorkspaceStateStore(workspace.state_db_path())
    state_store.ensure_schema()
    payload = secrets_store.read()
    payload["__workspace_password__"] = workspace_password
    return WorkspaceFeatureContext(
        workspace=workspace,
        secrets_store=secrets_store,
        state_store=state_store,
        secrets_payload=payload,
        app_kind=app_kind,
        existing_lock_handle=existing_lock_handle,
        force_lock_takeover=force_lock_takeover,
    )


def _build_wrapper(context: WorkspaceFeatureContext) -> OpenAIResponsesWrapper:
    llm_settings = dict(context.secrets_payload.get("llm") or {})
    return OpenAIResponsesWrapper(
        OpenAIResponsesConfig(
            model=str(llm_settings.get("model") or "gpt-5.4"),
            api_key=str(llm_settings.get("api_key") or ""),
            usage_log_path=str(context.workspace.profile_paths().llm_usage_log_path()),
        )
    )


def _resolve_template_workbook_path(context: WorkspaceFeatureContext) -> Path:
    relative_path = str(
        (context.secrets_payload.get("exports") or {}).get("template_workbook_relative_path") or ""
    ).strip()
    if relative_path:
        return context.workspace.from_workspace_relative(relative_path)
    default_template = context.workspace.profile_paths().template_workbook_path()
    if default_template.exists():
        return default_template
    raise RuntimeError("template workbook 경로가 없어 feature를 실행할 수 없다.")


def _workspace_common_checks(context: WorkspaceFeatureContext) -> list[FeatureCheckResult]:
    latest_review_json = context.workspace.review_logs_root() / "latest_inbox_review_board.json"
    return [
        FeatureCheckResult(
            label="state_db",
            status="pass" if context.workspace.state_db_path().exists() else "warn",
            detail=str(context.workspace.state_db_path()),
        ),
        FeatureCheckResult(
            label="latest_review_json",
            status="pass" if latest_review_json.exists() else "warn",
            detail=str(latest_review_json),
        ),
    ]


def _mailbox_checks(context: WorkspaceFeatureContext) -> list[FeatureCheckResult]:
    mailbox_settings = dict(context.secrets_payload.get("mailbox") or {})
    return [
        FeatureCheckResult(
            label="email_address",
            status="pass" if str(mailbox_settings.get("email_address") or "").strip() else "fail",
            detail="공유 설정에 메일 주소가 저장되어야 한다.",
        ),
        FeatureCheckResult(
            label="login_username",
            status="pass" if str(mailbox_settings.get("login_username") or "").strip() else "warn",
            detail="로그인 ID가 비어 있으면 email_address fallback을 쓴다.",
        ),
        FeatureCheckResult(
            label="mailbox_password",
            status="pass" if str(mailbox_settings.get("password") or "").strip() else "fail",
            detail="공유 설정에 메일 비밀번호 또는 앱 비밀번호가 필요하다.",
        ),
    ]


def _analysis_checks(context: WorkspaceFeatureContext) -> list[FeatureCheckResult]:
    llm_settings = dict(context.secrets_payload.get("llm") or {})
    bundle_count = sum(
        1
        for _ in context.workspace.profile_paths().runtime_mail_bundles_root().glob("*")
    )
    template_path = _resolve_template_candidate(context)
    return [
        FeatureCheckResult(
            label="openai_api_key",
            status="pass" if str(llm_settings.get("api_key") or "").strip() else "fail",
            detail="LLM 재분석에는 OpenAI API key가 필요하다.",
        ),
        FeatureCheckResult(
            label="template_workbook",
            status="pass" if template_path and Path(template_path).exists() else "fail",
            detail=str(template_path or "(없음)"),
        ),
        FeatureCheckResult(
            label="runtime_bundles",
            status="pass" if bundle_count > 0 else "fail",
            detail=f"현재 받은 메일 bundle 디렉토리 수: {bundle_count}",
        ),
    ]


def _exports_checks(context: WorkspaceFeatureContext) -> list[FeatureCheckResult]:
    template_path = _resolve_template_candidate(context)
    state_total = context.state_store.summary_counts().get("total", 0)
    latest_review_json = context.workspace.review_logs_root() / "latest_inbox_review_board.json"
    return [
        FeatureCheckResult(
            label="template_workbook",
            status="pass" if template_path and Path(template_path).exists() else "fail",
            detail=str(template_path or "(없음)"),
        ),
        FeatureCheckResult(
            label="review_state",
            status="pass" if state_total > 0 or latest_review_json.exists() else "fail",
            detail=f"state_items={state_total}, latest_review_json={latest_review_json.exists()}",
        ),
    ]


def _resolve_template_candidate(context: WorkspaceFeatureContext) -> str:
    try:
        return str(_resolve_template_workbook_path(context))
    except Exception:
        return ""


def _check_packaging_feature() -> list[FeatureCheckResult]:
    pyinstaller_spec = _safe_find_spec("PyInstaller")
    backports_tarfile_spec = _safe_find_spec("backports.tarfile")
    is_windows_host = os.name == "nt"
    return [
        FeatureCheckResult(
            label="windows_host",
            status="pass" if is_windows_host else "warn",
            detail="Windows 호스트나 Windows CI runner에서 빌드하는 것을 기본으로 본다.",
        ),
        FeatureCheckResult(
            label="pyinstaller_installed",
            status=(
                "pass"
                if pyinstaller_spec is not None
                else ("warn" if not is_windows_host else "fail")
            ),
            detail=(
                "Windows 빌드 환경에서는 PyInstaller가 설치되어 있어야 한다."
                if is_windows_host
                else "현재 호스트는 Windows 빌드 환경이 아니므로 참고용 경고로만 본다."
            ),
        ),
        FeatureCheckResult(
            label="backports_tarfile_installed",
            status=(
                "pass"
                if backports_tarfile_spec is not None
                else ("warn" if not is_windows_host else "fail")
            ),
            detail=(
                "Windows 패키징 호스트에서는 setuptools/pkg_resources runtime hook 대응을 위해 backports.tarfile이 필요하다."
                if is_windows_host
                else "현재 호스트는 Windows 패키징 검증기가 아니므로 참고용 경고로만 본다."
            ),
        ),
        FeatureCheckResult(
            label="portable_spec",
            status="pass" if PORTABLE_SPEC_PATH.exists() else "fail",
            detail=str(PORTABLE_SPEC_PATH),
        ),
        FeatureCheckResult(
            label="portable_smoke_script",
            status="pass" if PORTABLE_SMOKE_SCRIPT_PATH.exists() else "fail",
            detail=str(PORTABLE_SMOKE_SCRIPT_PATH),
        ),
        FeatureCheckResult(
            label="portable_manifest_helper",
            status="pass" if (REPO_ROOT / "app" / "packaging" / "portable_bundle_manifest.py").exists() else "fail",
            detail=str(REPO_ROOT / "app" / "packaging" / "portable_bundle_manifest.py"),
        ),
        FeatureCheckResult(
            label="portable_runtime_publish_script",
            status="pass" if (REPO_ROOT / "app" / "packaging" / "publish_portable_to_runtime.ps1").exists() else "fail",
            detail=str(REPO_ROOT / "app" / "packaging" / "publish_portable_to_runtime.ps1"),
        ),
        FeatureCheckResult(
            label="offline_static_assets",
            status="pass" if (REPO_ROOT / "app" / "static").exists() else "fail",
            detail=str(REPO_ROOT / "app" / "static"),
        ),
        FeatureCheckResult(
            label="build_script",
            status="pass" if PORTABLE_BUILD_SCRIPT_PATH.exists() else "fail",
            detail=str(PORTABLE_BUILD_SCRIPT_PATH),
        ),
    ]


def _run_packaging_build(*, spec: FeatureSpec) -> FeatureRunResult:
    if os.name != "nt":
        raise RuntimeError("포터블 exe build run은 Windows 호스트나 Windows CI runner에서만 실행할 수 있다.")
    if importlib.util.find_spec("PyInstaller") is None:
        raise RuntimeError("PyInstaller가 설치되어 있지 않아 포터블 exe build를 실행할 수 없다.")
    if not PORTABLE_BUILD_SCRIPT_PATH.exists():
        raise RuntimeError(f"포터블 exe build 스크립트를 찾을 수 없다: {PORTABLE_BUILD_SCRIPT_PATH}")

    command = [
        "powershell",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(PORTABLE_BUILD_SCRIPT_PATH),
    ]
    completed = subprocess.run(
        command,
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=True,
    )
    runtime_dir = Path("D:/EmailPilotAI/portable/EmailPilotAI")
    exe_path = runtime_dir / "EmailPilotAI.exe"
    outputs = {
        "portable_exe_path": str(exe_path),
        "runtime_directory": str(runtime_dir),
        "portable_manifest_path": str(runtime_dir / "portable_bundle_manifest.json"),
        "stdout_tail": completed.stdout.strip().splitlines()[-20:],
        "stderr_tail": completed.stderr.strip().splitlines()[-20:],
        "portable_smoke_script": str(PORTABLE_SMOKE_SCRIPT_PATH),
    }
    return FeatureRunResult(
        feature_id=spec.feature_id,
        title=spec.title,
        status="completed" if exe_path.exists() else "failed",
        summary="Windows 포터블 exe 빌드를 실행했다.",
        outputs=outputs,
        notes=[
            "Windows 호스트에서는 PowerShell build script를 직접 호출해 PyInstaller onedir bundle을 만든 뒤 D 로컬 실행본으로 publish 한다.",
            "CI runner에서는 같은 script를 workflow에서 재사용한다.",
            "A100 운영에서는 build 후 Linux 쪽 임시 dist mirror를 정리해 Z 경로 실행본이 다시 생기지 않게 유지한다.",
            "공식 실행 경로는 D:/EmailPilotAI/portable/EmailPilotAI/EmailPilotAI.exe 하나다.",
        ],
    )


@contextmanager
def _workspace_lock(context: WorkspaceFeatureContext) -> Iterator[WorkspaceWriteLockHandle | None]:
    if context.existing_lock_handle is not None:
        yield context.existing_lock_handle
        return
    handle = acquire_workspace_write_lock(
        lock_path=context.workspace.lock_path(),
        workspace_id=context.workspace.manifest.workspace_id,
        app_kind=context.app_kind,
        force_takeover=context.force_lock_takeover,
    )
    try:
        yield handle
    finally:
        handle.release()
