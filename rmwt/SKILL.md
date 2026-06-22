---
name: rmwt
description: Remove a git worktree, its branch, and its dedicated iOS simulator.
allowed-tools: Bash, Read, Glob
---

Remove a git worktree and clean up all associated resources.

## Skill Path

Resolve the scripts directory once:

```bash
RMWT_SCRIPTS=$(python3 -c "import os; p='.claude/skills/rmwt/scripts'; print(os.path.abspath(p) if os.path.isdir(p) else os.path.expanduser('~/.agents/skills/rmwt/scripts'))")
```

## Usage

`/rmwt <name>` — Remove the worktree, its branch, and its dedicated per-worktree
iOS simulator.

The `<name>` argument is required. If not provided, list worktrees and ask the user to pick one.

## Workflow

1. **Resolve** the worktree. Run `git worktree list` and find a worktree whose path contains `<name>` (case-insensitive). If no match, tell the user. If multiple matches, list them and ask the user to pick.

2. **Gather** what will be cleaned up:

   a. **Worktree path** — from `git worktree list` output.

   b. **Branch name** — from `git worktree list` output (shown in brackets).

   c. **Dedicated simulator** — the per-worktree sim a project's `scripts/sim-id.sh`
      creates (named `vf-<basename>-<hash>`). Resolve it (runs `xcrun simctl`, so
      use `dangerouslyDisableSandbox: true`):
      ```bash
      python3 $RMWT_SCRIPTS/worktree_sim.py '<WORKTREE_PATH>'
      ```
      It prints `{"name": ..., "udids": [...]}`. An empty `udids` means none exists
      (the worktree never created one) — skip this part of the cleanup.

3. **Safety checks** — before showing the summary, check for uncommitted work:

   a. **Uncommitted changes** — check if the worktree has any local changes:
      ```bash
      git -C <WORKTREE_PATH> status --porcelain
      ```
      If output is non-empty, warn the user: "This worktree has uncommitted changes."

   b. **Branch ahead of default branch** — detect the default branch, then check if the branch has commits not merged:
      ```bash
      DEFAULT_BRANCH=$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@')
      git log ${DEFAULT_BRANCH}..<BRANCH_NAME> --oneline
      ```
      If output is non-empty, warn the user: "This branch has N commit(s) not merged into <default_branch>."

    Include warnings in the summary (step 4) only when they are material to the user's decision. Use `🚨` only when there is real code-loss risk (for example unmerged commits or uncommitted work). If there is no code-loss risk, do not show warning signs; use a green check (for example `✅`) for safe status.

4. **Show summary** and confirm with the user before proceeding:
   > Removing worktree `<name>`:
   > - Worktree: `<path>`
   > - Branch: `<branch>`
   > - Simulator: `<sim-name>` (`<N>` udid(s)) (or "none found")
   >
   > Proceed?

5. **Execute** cleanup in order:

   a. **Delete the dedicated simulator** (for each udid found in step 2c):
      ```bash
      xcrun simctl delete <UDID>
      ```
      Runs `xcrun simctl`, so use `dangerouslyDisableSandbox: true`. `simctl delete`
      shuts the sim down first if it is booted.

   b. **Remove worktree**:
      ```bash
      git worktree remove <WORKTREE_PATH>
      ```

   c. **Delete branch**:
      ```bash
      git branch -d <BRANCH_NAME>
      ```
      If `-d` fails (unmerged), tell the user and suggest `-D` if they want to force-delete. Do NOT force-delete without explicit confirmation.

6. **Print** summary of what was cleaned up.

## Testing

Run the test suite to verify scripts work correctly:

```bash
python3 $RMWT_SCRIPTS/test_rmwt.py
```

The test suite verifies:
- The sim name matches the `scripts/sim-id.sh` convention (`vf-<basename>-<hash>`)
- A trailing slash on the path does not change the name
- **Critical**: sim names are unique for different paths (prevents accidental deletion of the wrong sim)
