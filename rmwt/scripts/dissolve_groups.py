#!/usr/bin/env python3
"""Dissolve handoff chat groups."""

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


def dissolve_groups(groups_json: str):
    """Dissolve the specified chat groups."""
    groups = json.loads(groups_json)

    handoff_dir = _find_handoff_scripts()
    if not handoff_dir:
        print("Error: handoff skill not found", file=sys.stderr)
        sys.exit(1)
    sys.path.insert(0, handoff_dir)
    from handoff_config import load_credentials
    from lark_im import get_tenant_token, dissolve_chat

    creds = load_credentials()
    token = get_tenant_token(creds["app_id"], creds["app_secret"])

    for g in groups:
        chat_id = g["chat_id"]
        name = g.get("name", chat_id)
        try:
            dissolve_chat(token, chat_id)
            print(f"Dissolved {name} ({chat_id})")
        except Exception as e:
            print(f"Failed to dissolve {name} ({chat_id}): {e}", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(description="Dissolve handoff chat groups")
    parser.add_argument(
        "groups_json", help="JSON array of groups with name and chat_id"
    )
    args = parser.parse_args()

    dissolve_groups(args.groups_json)


if __name__ == "__main__":
    main()
