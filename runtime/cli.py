"""공유 워크스페이스 create/open/sync를 위한 CLI."""

from __future__ import annotations

import argparse
import json

from runtime import (
    WorkspaceSecretsStore,
    WorkspaceStateStore,
    create_shared_workspace,
    load_shared_workspace,
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
    sync_parser.add_argument("--force-lock-takeover", action="store_true")

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
            force_lock_takeover=args.force_lock_takeover,
        )
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
        return


if __name__ == "__main__":
    main()
