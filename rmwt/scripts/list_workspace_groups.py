#!/usr/bin/env python3
"""List handoff chat groups for a specific workspace."""

import argparse
import json
import os
import sys


def _find_handoff_scripts():
    """Find the handoff scripts directory."""
    candidates = [
        os.path.join(os.getcwd(), ".claude/skills/handoff/scripts"),
        os.path.expanduser("~/.agents/skills/handoff/scripts"),
    ]
    for p in candidates:
        if os.path.isdir(p):
            return p
    return None


def get_workspace_id_from_path(worktree_path: str) -> str:
    """Compute the workspace ID from machine name + worktree path."""
    handoff_dir = _find_handoff_scripts()
    if not handoff_dir:
        print("Error: handoff skill not found", file=sys.stderr)
        sys.exit(1)
    sys.path.insert(0, handoff_dir)
    from handoff_config import _get_machine_name

    machine = _get_machine_name()
    folder = worktree_path.replace("/", "-").strip("-")
    return f"{machine}-{folder}"


def list_workspace_groups(worktree_path: str):
    """List all bot-owned chat groups tagged with the workspace."""
    workspace_id = get_workspace_id_from_path(worktree_path)
    tag = f"workspace:{workspace_id}"

    handoff_dir = _find_handoff_scripts()
    sys.path.insert(0, handoff_dir)
    from handoff_config import load_credentials
    from lark_im import get_tenant_token, list_bot_chats, get_chat_info

    creds = load_credentials()
    token = get_tenant_token(creds["app_id"], creds["app_secret"])
    chats = list_bot_chats(token)

    groups = []
    for c in chats:
        cid = c.get("chat_id", "")
        name = c.get("name", "")
        try:
            info = get_chat_info(token, cid)
            # Skip groups with an owner (not bot-owned)
            if info.get("owner_id"):
                continue
            desc = info.get("description") or ""
            if tag in desc:
                groups.append({"name": name, "chat_id": cid, "description": desc})
        except Exception:
            continue

    result = {"workspace_id": workspace_id, "groups": groups}
    print(json.dumps(result, indent=2))


def main():
    parser = argparse.ArgumentParser(
        description="List handoff chat groups for a workspace"
    )
    parser.add_argument("worktree", help="Path to the worktree")
    args = parser.parse_args()

    list_workspace_groups(args.worktree)


if __name__ == "__main__":
    main()
