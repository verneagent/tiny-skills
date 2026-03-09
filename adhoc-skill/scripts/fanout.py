#!/usr/bin/env python3
"""Fan out a user-level skill from ~/.agents/skills/ to all agent-facing directories.

Usage:
    python3 fanout.py <skill-name>          # Install symlinks for one skill
    python3 fanout.py --check <skill-name>  # Check without creating
    python3 fanout.py --all                 # Fan out all skills in ~/.agents/skills/

Discovers agent-facing skill directories by scanning known roots for existing
symlinks that point into ~/.agents/skills/. Only creates symlinks in directories
that already participate in the fan-out pattern.
"""

import argparse
import os
import sys

AGENTS_SKILLS = os.path.expanduser("~/.agents/skills")

# Known agent-facing skill roots to check.
CANDIDATE_ROOTS = [
    os.path.expanduser("~/.claude/skills"),
    os.path.expanduser("~/.config/opencode/skills"),
    os.path.expanduser("~/.codex/skills"),
]


def discover_fanout_targets():
    """Return list of directories that already symlink into ~/.agents/skills/."""
    targets = []
    for root in CANDIDATE_ROOTS:
        if not os.path.isdir(root):
            continue
        for entry in os.listdir(root):
            full = os.path.join(root, entry)
            if os.path.islink(full):
                real = os.path.realpath(full)
                if real.startswith(os.path.realpath(AGENTS_SKILLS)):
                    targets.append(root)
                    break
    return targets


def relative_link(target_dir, skill_name):
    """Compute a relative symlink path from target_dir to ~/.agents/skills/<skill>."""
    source = os.path.join(AGENTS_SKILLS, skill_name)
    return os.path.relpath(source, target_dir)


def fanout_skill(skill_name, check_only=False):
    """Create symlinks for a skill in all fan-out targets. Returns (created, skipped, errors)."""
    source = os.path.join(AGENTS_SKILLS, skill_name)
    if not os.path.isdir(source):
        print(f"Error: {source} does not exist", file=sys.stderr)
        return 0, 0, 1

    targets = discover_fanout_targets()
    if not targets:
        print("No fan-out targets found. No agent directories symlink into ~/.agents/skills/.")
        return 0, 0, 0

    created, skipped, errors = 0, 0, 0
    for target_dir in targets:
        link_path = os.path.join(target_dir, skill_name)
        if os.path.exists(link_path) or os.path.islink(link_path):
            real = os.path.realpath(link_path) if os.path.islink(link_path) else link_path
            expected = os.path.realpath(source)
            if real == expected:
                print(f"  ✓ {link_path} (already exists)")
                skipped += 1
            else:
                print(f"  ✗ {link_path} exists but points to {real}", file=sys.stderr)
                errors += 1
            continue

        rel = relative_link(target_dir, skill_name)
        if check_only:
            print(f"  → would create {link_path} → {rel}")
            skipped += 1
        else:
            try:
                os.symlink(rel, link_path)
                print(f"  ✓ {link_path} → {rel}")
                created += 1
            except OSError as e:
                print(f"  ✗ {link_path}: {e}", file=sys.stderr)
                errors += 1

    return created, skipped, errors


def main():
    parser = argparse.ArgumentParser(description="Fan out user-level skills")
    parser.add_argument("skill_name", nargs="?", help="Skill to fan out")
    parser.add_argument("--check", action="store_true", help="Check without creating")
    parser.add_argument("--all", action="store_true", help="Fan out all skills")
    args = parser.parse_args()

    if args.all:
        skills = sorted(
            d for d in os.listdir(AGENTS_SKILLS)
            if os.path.isdir(os.path.join(AGENTS_SKILLS, d)) and not d.startswith(".")
        )
    elif args.skill_name:
        skills = [args.skill_name]
    else:
        parser.print_help()
        sys.exit(1)

    targets = discover_fanout_targets()
    print(f"Fan-out targets: {', '.join(targets) if targets else '(none found)'}\n")

    total_created, total_skipped, total_errors = 0, 0, 0
    for skill in skills:
        print(f"{skill}:")
        c, s, e = fanout_skill(skill, check_only=args.check)
        total_created += c
        total_skipped += s
        total_errors += e

    print(f"\nDone: {total_created} created, {total_skipped} skipped, {total_errors} errors")
    sys.exit(1 if total_errors else 0)


if __name__ == "__main__":
    main()
