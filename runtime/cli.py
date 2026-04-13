"""공유 워크스페이스와 제품 기능을 위한 명시적 CLI."""

from __future__ import annotations

import argparse
import json

from runtime.feature_harness_smoke import run_feature_harness_smoke
from runtime import (
    check_feature,
    create_sample_workspace,
    feature_catalog_rows,
    get_feature_spec,
    run_feature,
)
from runtime.analysis_service import refresh_review_board_service
from runtime.diagnostics_service import (
    pick_file_native,
    pick_folder_native,
    picker_bridge_self_test,
)
from runtime.exports_service import rebuild_operating_workbook_service
from runtime.mailbox_service import (
    run_mailbox_connection_check_service,
    run_mailbox_fetch_service,
)
from runtime.pipeline_service import run_pipeline_sync_service
from runtime.settings_service import (
    load_workspace_settings_summary,
    save_workspace_settings,
)
from runtime.workspace_service import (
    close_workspace_entry,
    create_workspace_entry,
    inspect_workspace_entry,
    list_recent_workspaces,
    open_workspace_entry,
)


def _print(payload: object) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description="Email Pilot AI runtime CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    workspace_parser = subparsers.add_parser("workspace")
    workspace_sub = workspace_parser.add_subparsers(dest="workspace_command", required=True)

    workspace_create = workspace_sub.add_parser("create")
    workspace_create.add_argument("--save-parent-dir", required=True)
    workspace_create.add_argument("--workspace-password", required=True)
    workspace_create.add_argument("--workspace-label", default="")
    workspace_create.add_argument("--no-remember", action="store_true")

    workspace_open = workspace_sub.add_parser("open")
    workspace_open.add_argument("--workspace-root", required=True)
    workspace_open.add_argument("--workspace-password", required=True)
    workspace_open.add_argument("--readonly", action="store_true")
    workspace_open.add_argument("--no-remember", action="store_true")

    workspace_close = workspace_sub.add_parser("close")
    workspace_close.add_argument("--workspace-root", default="")

    workspace_status = workspace_sub.add_parser("status")
    workspace_status.add_argument("--workspace-root", required=True)
    workspace_status.add_argument("--workspace-password", required=True)

    workspace_recent = workspace_sub.add_parser("recent")

    settings_parser = subparsers.add_parser("settings")
    settings_sub = settings_parser.add_subparsers(dest="settings_command", required=True)

    settings_show = settings_sub.add_parser("show")
    settings_show.add_argument("--workspace-root", required=True)
    settings_show.add_argument("--workspace-password", required=True)

    settings_save = settings_sub.add_parser("save")
    settings_save.add_argument("--workspace-root", required=True)
    settings_save.add_argument("--workspace-password", required=True)
    settings_save.add_argument("--llm-model", default="gpt-5.4")
    settings_save.add_argument("--llm-api-key", default="")
    settings_save.add_argument("--email-address", default="")
    settings_save.add_argument("--login-username", default="")
    settings_save.add_argument("--mailbox-password", default="")
    settings_save.add_argument("--default-folder", default="")
    settings_save.add_argument("--template-workbook-relative-path", default="")

    mailbox_parser = subparsers.add_parser("mailbox")
    mailbox_sub = mailbox_parser.add_subparsers(dest="mailbox_command", required=True)

    mailbox_connect = mailbox_sub.add_parser("connect-check")
    mailbox_connect.add_argument("--workspace-root", required=True)
    mailbox_connect.add_argument("--workspace-password", required=True)
    mailbox_connect.add_argument("--llm-model", default="gpt-5.4")
    mailbox_connect.add_argument("--llm-api-key", default="")
    mailbox_connect.add_argument("--email-address", default="")
    mailbox_connect.add_argument("--login-username", default="")
    mailbox_connect.add_argument("--mailbox-password", default="")
    mailbox_connect.add_argument("--default-folder", default="")
    mailbox_connect.add_argument("--template-workbook-relative-path", default="")

    mailbox_fetch = mailbox_sub.add_parser("fetch")
    mailbox_fetch.add_argument("--workspace-root", required=True)
    mailbox_fetch.add_argument("--workspace-password", required=True)
    mailbox_fetch.add_argument("--limit", type=int)
    mailbox_fetch.add_argument("--all", action="store_true")

    analysis_parser = subparsers.add_parser("analysis")
    analysis_sub = analysis_parser.add_subparsers(dest="analysis_command", required=True)

    review_refresh = analysis_sub.add_parser("review-refresh")
    review_refresh.add_argument("--workspace-root", required=True)
    review_refresh.add_argument("--workspace-password", required=True)
    review_refresh.add_argument("--limit", type=int)
    review_refresh.add_argument("--all", action="store_true")

    exports_parser = subparsers.add_parser("exports")
    exports_sub = exports_parser.add_subparsers(dest="exports_command", required=True)

    exports_rebuild = exports_sub.add_parser("rebuild")
    exports_rebuild.add_argument("--workspace-root", required=True)
    exports_rebuild.add_argument("--workspace-password", required=True)

    pipeline_parser = subparsers.add_parser("pipeline")
    pipeline_sub = pipeline_parser.add_subparsers(dest="pipeline_command", required=True)

    pipeline_sync = pipeline_sub.add_parser("sync")
    pipeline_sync.add_argument("--workspace-root", required=True)
    pipeline_sync.add_argument("--workspace-password", required=True)
    pipeline_sync.add_argument("--scope", choices=["recent", "all"], default="recent")
    pipeline_sync.add_argument("--limit", type=int)
    pipeline_sync.add_argument("--all", action="store_true")
    pipeline_sync.add_argument("--app-kind", default="server-tool")

    diagnostics_parser = subparsers.add_parser("diagnostics")
    diagnostics_sub = diagnostics_parser.add_subparsers(dest="diagnostics_command", required=True)

    picker_bridge = diagnostics_sub.add_parser("picker-bridge")
    picker_bridge.add_argument("--shell-mode", default="desktop_window")
    picker_bridge.add_argument("--window-attached", action="store_true")

    picker_folder = diagnostics_sub.add_parser("pick-folder")
    picker_folder.add_argument("--current-path", default="")
    picker_folder.add_argument("--workspace-root", default="")

    picker_file = diagnostics_sub.add_parser("pick-file")
    picker_file.add_argument("--current-path", default="")
    picker_file.add_argument("--workspace-root", default="")

    sample_parser = subparsers.add_parser("create-sample-workspace")
    sample_parser.add_argument("--workspace-root", required=True)
    sample_parser.add_argument("--workspace-password", required=True)
    sample_parser.add_argument("--workspace-label", default="샘플 워크스페이스")

    feature_list_parser = subparsers.add_parser("feature-list")
    feature_list_parser.add_argument("--json", action="store_true")

    feature_inspect_parser = subparsers.add_parser("feature-inspect")
    feature_inspect_parser.add_argument("--feature-id", required=True)

    feature_check_parser = subparsers.add_parser("feature-check")
    feature_check_parser.add_argument("--feature-id", required=True)
    feature_check_parser.add_argument("--workspace-root")
    feature_check_parser.add_argument("--workspace-password")

    feature_check_all_parser = subparsers.add_parser("feature-check-all")
    feature_check_all_parser.add_argument("--workspace-root")
    feature_check_all_parser.add_argument("--workspace-password")

    feature_run_parser = subparsers.add_parser("feature-run")
    feature_run_parser.add_argument("--feature-id", required=True)
    feature_run_parser.add_argument("--workspace-root")
    feature_run_parser.add_argument("--workspace-password")
    feature_run_parser.add_argument("--app-kind", default="server-tool")
    feature_run_parser.add_argument("--trigger-source", default="cli")
    feature_run_parser.add_argument("--force-lock-takeover", action="store_true")

    feature_harness_parser = subparsers.add_parser("feature-harness-smoke")
    feature_harness_parser.add_argument("--workspace-root", required=True)
    feature_harness_parser.add_argument("--workspace-password", required=True)
    feature_harness_parser.add_argument("--create-sample-if-missing", action="store_true")

    args = parser.parse_args()

    if args.command == "workspace":
        if args.workspace_command == "create":
            _print(
                create_workspace_entry(
                    save_parent_dir=args.save_parent_dir,
                    workspace_password=args.workspace_password,
                    workspace_label=args.workspace_label,
                    remember_local=not args.no_remember,
                ).to_dict()
            )
            return
        if args.workspace_command == "open":
            _print(
                open_workspace_entry(
                    workspace_root=args.workspace_root,
                    workspace_password=args.workspace_password,
                    readonly_requested=args.readonly,
                    remember_local=not args.no_remember,
                ).to_dict()
            )
            return
        if args.workspace_command == "close":
            _print(close_workspace_entry(workspace_root=args.workspace_root))
            return
        if args.workspace_command == "status":
            _print(
                inspect_workspace_entry(
                    workspace_root=args.workspace_root,
                    workspace_password=args.workspace_password,
                ).to_dict()
            )
            return
        if args.workspace_command == "recent":
            _print([item.to_dict() for item in list_recent_workspaces()])
            return

    if args.command == "settings":
        if args.settings_command == "show":
            _print(
                load_workspace_settings_summary(
                    workspace_root=args.workspace_root,
                    workspace_password=args.workspace_password,
                ).to_dict()
            )
            return
        if args.settings_command == "save":
            _print(
                save_workspace_settings(
                    workspace_root=args.workspace_root,
                    workspace_password=args.workspace_password,
                    llm_model=args.llm_model,
                    llm_api_key=args.llm_api_key,
                    email_address=args.email_address,
                    login_username=args.login_username,
                    mailbox_password=args.mailbox_password,
                    default_folder=args.default_folder,
                    template_workbook_relative_path=args.template_workbook_relative_path,
                ).to_dict()
            )
            return

    if args.command == "mailbox":
        if args.mailbox_command == "connect-check":
            _print(
                run_mailbox_connection_check_service(
                    workspace_root=args.workspace_root,
                    workspace_password=args.workspace_password,
                    llm_model=args.llm_model,
                    llm_api_key=args.llm_api_key,
                    email_address=args.email_address,
                    login_username=args.login_username,
                    mailbox_password=args.mailbox_password,
                    default_folder=args.default_folder,
                    template_workbook_relative_path=args.template_workbook_relative_path,
                ).to_dict()
            )
            return
        if args.mailbox_command == "fetch":
            _print(
                run_mailbox_fetch_service(
                    workspace_root=args.workspace_root,
                    workspace_password=args.workspace_password,
                    limit=None if args.all else args.limit,
                    app_kind_note="CLI에서 mailbox fetch를 실행했습니다.",
                ).to_dict()
            )
            return

    if args.command == "analysis" and args.analysis_command == "review-refresh":
        _print(
            refresh_review_board_service(
                workspace_root=args.workspace_root,
                workspace_password=args.workspace_password,
                limit=None if args.all else args.limit,
                reuse_existing_analysis=True,
            ).to_dict()
        )
        return

    if args.command == "exports" and args.exports_command == "rebuild":
        _print(
            rebuild_operating_workbook_service(
                workspace_root=args.workspace_root,
                workspace_password=args.workspace_password,
            ).to_dict()
        )
        return

    if args.command == "pipeline" and args.pipeline_command == "sync":
        scope = "all" if args.all else args.scope
        _print(
            run_pipeline_sync_service(
                workspace_root=args.workspace_root,
                workspace_password=args.workspace_password,
                scope=scope,
                limit=args.limit,
                app_kind=args.app_kind,
            ).to_dict()
        )
        return

    if args.command == "diagnostics" and args.diagnostics_command == "picker-bridge":
        _print(
            picker_bridge_self_test(
                shell_mode=args.shell_mode,
                window_attached=args.window_attached,
            ).to_dict()
        )
        return
    if args.command == "diagnostics" and args.diagnostics_command == "pick-folder":
        _print(
            pick_folder_native(
                current_path=args.current_path,
                workspace_root=args.workspace_root,
            ).to_dict()
        )
        return
    if args.command == "diagnostics" and args.diagnostics_command == "pick-file":
        _print(
            pick_file_native(
                current_path=args.current_path,
                workspace_root=args.workspace_root,
            ).to_dict()
        )
        return

    if args.command == "create-sample-workspace":
        _print(
            create_sample_workspace(
                workspace_root=args.workspace_root,
                workspace_password=args.workspace_password,
                workspace_label=args.workspace_label,
            ).to_dict()
        )
        return

    if args.command == "feature-list":
        rows = feature_catalog_rows()
        if args.json:
            _print(rows)
            return
        for row in rows:
            access_modes = ",".join(row["access_modes"])
            print(f"{row['feature_id']}\t{row['owner_module']}\t{access_modes}\t{row['title']}")
        return

    if args.command == "feature-inspect":
        _print(get_feature_spec(args.feature_id).to_dict())
        return

    if args.command == "feature-check":
        _print(
            [
                item.to_dict()
                for item in check_feature(
                    feature_id=args.feature_id,
                    workspace_root=args.workspace_root,
                    workspace_password=args.workspace_password,
                )
            ]
        )
        return

    if args.command == "feature-check-all":
        payload = {
            row["feature_id"]: [
                item.to_dict()
                for item in check_feature(
                    feature_id=str(row["feature_id"]),
                    workspace_root=args.workspace_root,
                    workspace_password=args.workspace_password,
                )
            ]
            for row in feature_catalog_rows()
        }
        _print(payload)
        return

    if args.command == "feature-run":
        _print(
            run_feature(
                feature_id=args.feature_id,
                workspace_root=args.workspace_root,
                workspace_password=args.workspace_password,
                app_kind=args.app_kind,
                trigger_source=args.trigger_source,
                force_lock_takeover=args.force_lock_takeover,
            ).to_dict()
        )
        return

    if args.command == "feature-harness-smoke":
        _print(
            run_feature_harness_smoke(
                workspace_root=args.workspace_root,
                workspace_password=args.workspace_password,
                create_sample_if_missing=args.create_sample_if_missing,
            ).to_dict()
        )
        return


if __name__ == "__main__":
    main()
