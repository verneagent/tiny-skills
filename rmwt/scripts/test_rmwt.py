#!/usr/bin/env python3
"""Test suite for rmwt scripts.

Run these tests to verify the scripts work correctly.
"""

import os
import subprocess
import sys

# Resolve scripts directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def test_get_workspace_id():
    """Test get_workspace_id.py computes correct workspace ID."""
    result = subprocess.run(
        [
            sys.executable,
            os.path.join(SCRIPT_DIR, "get_workspace_id.py"),
            "/Users/dinghaozeng/worktrees/meadow/andsim",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Script failed: {result.stderr}"
    assert "Users-dinghaozeng-worktrees-meadow-andsim" in result.stdout
    print("  get_workspace_id.py - andsim worktree OK")

    result = subprocess.run(
        [
            sys.executable,
            os.path.join(SCRIPT_DIR, "get_workspace_id.py"),
            "/Users/dinghaozeng/clover/meadow",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Script failed: {result.stderr}"
    assert "Users-dinghaozeng-clover-meadow" in result.stdout
    print("  get_workspace_id.py - main worktree OK")


def test_list_workspace_groups():
    """Test list_workspace_groups.py returns valid JSON."""
    import json

    result = subprocess.run(
        [
            sys.executable,
            os.path.join(SCRIPT_DIR, "list_workspace_groups.py"),
            "/Users/dinghaozeng/worktrees/meadow/andsim",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Script failed: {result.stderr}"

    data = json.loads(result.stdout)
    assert "workspace_id" in data
    assert "groups" in data
    assert "Users-dinghaozeng-worktrees-meadow-andsim" in data["workspace_id"]
    print("  list_workspace_groups.py - returns valid JSON OK")


def test_workspace_id_isolation():
    """Critical test: Ensure workspace IDs are different for different paths."""
    paths = [
        "/Users/dinghaozeng/worktrees/meadow/andsim",
        "/Users/dinghaozeng/clover/meadow",
        "/Users/dinghaozeng/worktrees/meadow/andprod",
    ]

    ids = []
    for path in paths:
        result = subprocess.run(
            [sys.executable, os.path.join(SCRIPT_DIR, "get_workspace_id.py"), path],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        ids.append(result.stdout.strip())

    # All IDs should be unique
    assert len(set(ids)) == len(ids), f"Duplicate workspace IDs detected: {ids}"
    print(f"  Workspace ID isolation - {len(ids)} unique IDs OK")


def run_all_tests():
    """Run all tests."""
    print("Running rmwt script tests...\n")

    tests = [
        test_get_workspace_id,
        test_list_workspace_groups,
        test_workspace_id_isolation,
    ]

    passed = 0
    failed = 0

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
    success = run_all_tests()
    sys.exit(0 if success else 1)
