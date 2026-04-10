"""공유 워크스페이스 create/open/sync를 위한 CLI."""

from __future__ import annotations

import argparse
import json

from runtime.feature_harness_smoke import run_feature_harness_smoke
from runtime import (
    WorkspaceSecretsStore,
    WorkspaceStateStore,
    check_feature,
    create_shared_workspace,
    create_sample_workspace,
    feature_catalog_rows,
    get_feature_spec,
    load_shared_workspace,
    run_feature,
    run_workspace_sync,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="shared workspace runtime CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    create_parser = subparsers.add_parser("create-workspace")
    create_parser.add_argument("--workspace-root", required=True)
    create_parser.add_argument("--workspace-password", required=True)
    create_parser.add_argument("--workspace-label", default="")
    create_parser.add_argument("--import-profile-root")

    inspect_parser = subparsers.add_parser("inspect-workspace")
    inspect_parser.add_argument("--workspace-root", required=True)
    inspect_parser.add_argument("--workspace-password", required=True)

    sync_parser = subparsers.add_parser("sync")
    sync_parser.add_argument("--workspace-root", required=True)
    sync_parser.add_argument("--workspace-password", required=True)
    sync_parser.add_argument("--app-kind", default="server-tool")
    sync_parser.add_argument("--profile-id", default="shared-workspace")
    sync_parser.add_argument("--sync-mode", choices=["quick_smoke", "incremental_full"], default="incremental_full")
    sync_parser.add_argument("--force-lock-takeover", action="store_true")

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
    if args.command == "create-workspace":
        workspace = create_shared_workspace(
            workspace_root=args.workspace_root,
            workspace_password=args.workspace_password,
            workspace_label=args.workspace_label,
            import_profile_root=args.import_profile_root,
        )
        print(
            json.dumps(
                {
                    "workspace_root": str(workspace.root()),
                    "manifest_path": str(workspace.manifest_path()),
                    "profile_root": str(workspace.profile_root()),
                    "state_db_path": str(workspace.state_db_path()),
                    "secure_blob_path": str(workspace.secure_blob_path()),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return

    if args.command == "inspect-workspace":
        workspace = load_shared_workspace(args.workspace_root)
        secrets_store = WorkspaceSecretsStore(
            path=str(workspace.secure_blob_path()),
            password=args.workspace_password,
        )
        state_store = WorkspaceStateStore(workspace.state_db_path())
        summary = {
            "workspace_root": str(workspace.root()),
            "manifest": workspace.manifest.to_dict(),
            "shared_settings": secrets_store.masked_summary(),
            "state_counts": state_store.summary_counts(),
            "latest_sync_run": state_store.latest_sync_run(),
        }
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return

    if args.command == "sync":
        result = run_workspace_sync(
            workspace_root=args.workspace_root,
            workspace_password=args.workspace_password,
            app_kind=args.app_kind,
            profile_id=args.profile_id,
            sync_mode=args.sync_mode,
            force_lock_takeover=args.force_lock_takeover,
        )
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
        return

    if args.command == "create-sample-workspace":
        result = create_sample_workspace(
            workspace_root=args.workspace_root,
            workspace_password=args.workspace_password,
            workspace_label=args.workspace_label,
        )
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
        return

    if args.command == "feature-list":
        rows = feature_catalog_rows()
        if args.json:
            print(json.dumps(rows, ensure_ascii=False, indent=2))
            return
        for row in rows:
            access_modes = ",".join(row["access_modes"])
            print(f"{row['feature_id']}\t{row['owner_module']}\t{access_modes}\t{row['title']}")
        return

    if args.command == "feature-inspect":
        print(
            json.dumps(
                get_feature_spec(args.feature_id).to_dict(),
                ensure_ascii=False,
                indent=2,
            )
        )
        return

    if args.command == "feature-check":
        results = check_feature(
            feature_id=args.feature_id,
            workspace_root=args.workspace_root,
            workspace_password=args.workspace_password,
        )
        print(
            json.dumps(
                [item.to_dict() for item in results],
                ensure_ascii=False,
                indent=2,
            )
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
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return

    if args.command == "feature-run":
        result = run_feature(
            feature_id=args.feature_id,
            workspace_root=args.workspace_root,
            workspace_password=args.workspace_password,
            app_kind=args.app_kind,
            trigger_source=args.trigger_source,
            force_lock_takeover=args.force_lock_takeover,
        )
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
        return

    if args.command == "feature-harness-smoke":
        result = run_feature_harness_smoke(
            workspace_root=args.workspace_root,
            workspace_password=args.workspace_password,
            create_sample_if_missing=args.create_sample_if_missing,
        )
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
        return


if __name__ == "__main__":
    main()
