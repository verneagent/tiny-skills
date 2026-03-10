#!/usr/bin/env python3
"""Calculate workspace ID from a worktree path."""

import argparse
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
    """Compute the workspace ID from machine name + worktree path.

    Similar to handoff_config.get_workspace_id() but takes the path as argument
    instead of reading from environment variables.
    """
    handoff_dir = _find_handoff_scripts()
    if not handoff_dir:
        print("Error: handoff skill not found", file=sys.stderr)
        sys.exit(1)
    sys.path.insert(0, handoff_dir)
    from handoff_config import _get_machine_name

    machine = _get_machine_name()
    folder = worktree_path.replace("/", "-").strip("-")
    return f"{machine}-{folder}"


def main():
    parser = argparse.ArgumentParser(
        description="Calculate workspace ID from worktree path"
    )
    parser.add_argument("worktree", help="Path to the worktree")
    args = parser.parse_args()

    workspace_id = get_workspace_id_from_path(args.worktree)
    print(workspace_id)


if __name__ == "__main__":
    main()
