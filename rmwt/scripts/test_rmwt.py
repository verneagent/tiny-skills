#!/usr/bin/env python3
"""Test suite for rmwt scripts."""

import os
import subprocess
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def _name(path: str) -> str:
    result = subprocess.run(
        [sys.executable, os.path.join(SCRIPT_DIR, "worktree_sim.py"), "--name", path],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Script failed: {result.stderr}"
    return result.stdout.strip()


def test_sim_name_convention():
    """worktree_sim.py --name matches scripts/sim-id.sh's vf-<basename>-<hash>."""
    name = _name("/Users/dinghaozeng/code/voicefeed")
    assert name == "vf-voicefeed-e42ccb", name
    print("  sim_name - matches sim-id.sh convention OK")


def test_sim_name_trailing_slash():
    """A trailing slash must not change the name (sim-id.sh strips it)."""
    assert _name("/Users/dinghaozeng/code/voicefeed/") == _name("/Users/dinghaozeng/code/voicefeed")
    print("  sim_name - trailing slash normalised OK")


def test_sim_name_isolation():
    """Critical: sim names are unique per path (prevents deleting the wrong sim)."""
    paths = [
        "/Users/dinghaozeng/worktrees/meadow/andsim",
        "/Users/dinghaozeng/clover/meadow",
        "/Users/dinghaozeng/worktrees/meadow/andprod",
    ]
    names = [_name(p) for p in paths]
    assert len(set(names)) == len(names), f"Duplicate sim names: {names}"
    print(f"  sim_name isolation - {len(names)} unique names OK")


def run_all_tests():
    print("Running rmwt script tests...\n")
    tests = [test_sim_name_convention, test_sim_name_trailing_slash, test_sim_name_isolation]
    passed = failed = 0
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"  {test.__name__} failed: {e}")
            failed += 1
        except Exception as e:
            print(f"  {test.__name__} error: {e}")
            failed += 1
    print(f"\n{'=' * 50}")
    print(f"Results: {passed} passed, {failed} failed")
    return failed == 0


if __name__ == "__main__":
    sys.exit(0 if run_all_tests() else 1)
