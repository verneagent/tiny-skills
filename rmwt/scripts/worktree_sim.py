#!/usr/bin/env python3
"""Resolve the dedicated iOS simulator a worktree owns, for cleanup by rmwt.

A worktree's per-worktree sim is named by the project convention
    vf-<worktree-basename>-<6-char SHA1 of the worktree path>
(see the project's scripts/sim-id.sh). rmwt deletes that sim when it removes the
worktree so dedicated sims don't pile up.

Usage:
  worktree_sim.py <worktree-path>            # print the exact sim name + matching udids
  worktree_sim.py --name <worktree-path>     # print only the exact sim name (pure, testable)

The default mode shells out to `xcrun simctl` and must run with the sandbox
disabled. `--name` is pure (no simctl) so it can be unit-tested.
"""

import hashlib
import json
import os
import subprocess
import sys


def sim_name(worktree_path: str) -> str:
    """Exact sim name for a worktree path — mirrors scripts/sim-id.sh."""
    p = worktree_path.rstrip("/")
    digest = hashlib.sha1(p.encode()).hexdigest()[:6]
    return f"vf-{os.path.basename(p)}-{digest}"


def matching_udids(name: str) -> list[str]:
    """udids of every booted/shutdown sim with exactly this name (clones can dupe)."""
    out = subprocess.run(
        ["xcrun", "simctl", "list", "devices", "-j"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    devices = json.loads(out)["devices"]
    return [d["udid"] for runtime in devices.values() for d in runtime if d.get("name") == name]


def main(argv: list[str]) -> int:
    if "--name" in argv:
        argv = [a for a in argv if a != "--name"]
        if len(argv) != 1:
            print("usage: worktree_sim.py --name <worktree-path>", file=sys.stderr)
            return 2
        print(sim_name(argv[0]))
        return 0

    if len(argv) != 1:
        print("usage: worktree_sim.py <worktree-path>", file=sys.stderr)
        return 2
    name = sim_name(argv[0])
    udids = matching_udids(name)
    print(json.dumps({"name": name, "udids": udids}))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
