#!/usr/bin/env python3
"""Build and execute the launch command for opening a coding tool in a new terminal tab.

Usage:
    python3 launch.py --path <PATH> --tool <claude|opencode> [--model <MODEL>] [--handoff]

Builds the shell command and runs the AppleScript to open a new tab.
"""
import argparse
import os
import subprocess
import sys


def build_command(path: str, tool: str, model: str | None, handoff: bool) -> str:
    parts = [f"cd {path}"]

    cmd = tool
    if model:
        cmd += f" --model {model}"
    if handoff:
        # claude: positional arg is the prompt
        # opencode: positional arg is project path, use --prompt for initial message
        if tool == "opencode":
            cmd += ' --prompt "enter handoff no ask"'
        else:
            cmd += ' "enter handoff no ask"'

    parts.append(cmd)
    return " && ".join(parts)


def main():
    parser = argparse.ArgumentParser(description="Launch coding tool in new terminal tab")
    parser.add_argument("--path", required=True, help="Resolved workspace path")
    parser.add_argument("--tool", required=True, choices=["claude", "opencode"], help="CLI tool")
    parser.add_argument("--model", default=None, help="Model name")
    parser.add_argument("--handoff", action="store_true", help="Auto-enter handoff mode")
    args = parser.parse_args()

    shell_cmd = build_command(args.path, args.tool, args.model, args.handoff)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    applescript = os.path.join(script_dir, "open_tab.applescript")

    result = subprocess.run(
        ["osascript", applescript, shell_cmd],
        capture_output=True,
        text=True,
    )

    print(shell_cmd)
    if result.returncode != 0:
        print(f"error: {result.stderr.strip()}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
