#!/usr/bin/env python3
"""Workspace operations for the wksp skill.

Provides resolve-spawn-path and pretrust commands, plus parse_spawn_command
for natural language model extraction.
"""

import argparse
import json
import os
import re
import subprocess
import sys


def _jprint(obj):
    print(json.dumps(obj, ensure_ascii=True))


def parse_spawn_command(args_str):
    """Parse spawn command with natural language model specification.

    Extracts path and optional model name from natural language input.

    Examples:
    - "spawn2" → ("spawn2", None)
    - "spawn2 with haiku" → ("spawn2", "haiku")
    - "spawn2 using sonnet" → ("spawn2", "sonnet")
    - "spawn2 as opus" → ("spawn2", "opus")
    """
    valid_models = ['haiku', 'sonnet', 'opus']

    patterns = [
        r'(?:with|using|as)\s+(haiku|sonnet|opus)',
        r'(haiku|sonnet|opus)\s+(?:model|mode)',
    ]

    model = None
    for pattern in patterns:
        match = re.search(pattern, args_str, re.IGNORECASE)
        if match:
            m = match.group(1).lower()
            if m in valid_models:
                model = m
            args_str = re.sub(pattern, '', args_str, flags=re.IGNORECASE).strip()
            break

    return args_str.strip(), model


def cmd_resolve_spawn_path(args):
    arg = args.arg
    path = os.path.abspath(os.path.expanduser(arg))
    if os.path.isdir(path):
        _jprint({"found": True, "path": path, "source": "path"})
        return 0

    wt = subprocess.run(
        ["git", "worktree", "list", "--porcelain"],
        capture_output=True,
        text=True,
        timeout=10,
    )
    if wt.returncode != 0:
        _jprint({"found": False, "matches": []})
        return 0

    matches = []
    key = arg.lower()
    for line in wt.stdout.splitlines():
        if not line.startswith("worktree "):
            continue
        p = line[len("worktree ") :].strip()
        name = os.path.basename(p).lower()
        if key in name:
            matches.append(p)
    _jprint({"found": len(matches) == 1, "matches": matches})
    return 0


def cmd_pretrust(args):
    path = args.path
    cfg_path = os.path.expanduser("~/.claude.json")
    data = {}
    try:
        with open(cfg_path) as f:
            data = json.load(f)
    except FileNotFoundError:
        data = {}
    except json.JSONDecodeError:
        # Bootstrap on corrupted config instead of failing spawn pretrust.
        data = {}
    projects = data.setdefault("projects", {})
    if path in projects:
        _jprint({"ok": True, "changed": False})
        return 0
    projects[path] = {
        "allowedTools": [],
        "mcpContextUris": [],
        "mcpServers": {},
        "enabledMcpjsonServers": [],
        "disabledMcpjsonServers": [],
        "hasTrustDialogAccepted": True,
        "projectOnboardingSeenCount": 0,
        "hasClaudeMdExternalIncludesApproved": False,
        "hasClaudeMdExternalIncludesWarningShown": False,
        "hasCompletedProjectOnboarding": False,
    }
    with open(cfg_path, "w") as f:
        json.dump(data, f, indent=2)
    _jprint({"ok": True, "changed": True})
    return 0


def cmd_ensure_skill_permission(args):
    path = args.path
    skill = args.skill
    entry = f"Skill({skill})"
    settings_path = os.path.join(path, ".claude", "settings.local.json")
    os.makedirs(os.path.dirname(settings_path), exist_ok=True)
    data = {}
    try:
        with open(settings_path) as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        data = {}
    allow = data.setdefault("permissions", {}).setdefault("allow", [])
    if entry in allow:
        _jprint({"ok": True, "changed": False})
        return 0
    allow.append(entry)
    with open(settings_path, "w") as f:
        json.dump(data, f, indent=2)
    _jprint({"ok": True, "changed": True, "path": settings_path})
    return 0


def build_parser():
    p = argparse.ArgumentParser(description="Workspace operations")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("resolve-spawn-path")
    s.add_argument("--arg", required=True)
    s.set_defaults(func=cmd_resolve_spawn_path)

    s = sub.add_parser("ensure-skill-permission")
    s.add_argument("--path", required=True)
    s.add_argument("--skill", required=True)
    s.set_defaults(func=cmd_ensure_skill_permission)

    s = sub.add_parser("pretrust")
    s.add_argument("--path", required=True)
    s.set_defaults(func=cmd_pretrust)

    return p


def main():
    parser = build_parser()
    args = parser.parse_args()
    try:
        return int(args.func(args) or 0)
    except Exception as e:
        _jprint({"error": str(e), "cmd": args.cmd})
        return 1


if __name__ == "__main__":
    sys.exit(main())
