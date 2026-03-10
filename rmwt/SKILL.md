---
name: rmwt
description: Remove a git worktree, its branch, and associated handoff resources.
allowed-tools: Bash, Read, Glob
---

Remove a git worktree and clean up all associated resources.

## Skill Path

Resolve the scripts directory once:

```bash
RMWT_SCRIPTS=$(python3 -c "import os; p='.claude/skills/rmwt/scripts'; print(os.path.abspath(p) if os.path.isdir(p) else os.path.expanduser('~/.agents/skills/rmwt/scripts'))")
```

## Usage

`/rmwt <name>` — Remove worktree, branch, all handoff chat groups for that workspace, and all handoff database buckets for that project.

The `<name>` argument is required. If not provided, list worktrees and ask the user to pick one.

## Workflow

1. **Resolve** the worktree. Run `git worktree list` and find a worktree whose path contains `<name>` (case-insensitive). If no match, tell the user. If multiple matches, list them and ask the user to pick.

2. **Gather** what will be cleaned up:

   a. **Worktree path** — from `git worktree list` output.

   b. **Branch name** — from `git worktree list` output (shown in brackets).

   c. **Handoff chat groups (all for workspace)** — list all bot-owned groups tagged with the workspace (computed from worktree path):
      ```bash
      python3 $RMWT_SCRIPTS/list_workspace_groups.py '<WORKTREE_PATH>'
      ```
      This MUST run with `dangerouslyDisableSandbox: true` in Claude Code since it calls the Lark API. If handoff is not installed, this step is skipped.

   d. **Handoff database directory** — check if it exists:
      ```bash
      python3 -c "
      import os
      project = '<WORKTREE_PATH>'.replace('/', '-')
      print(os.path.join(os.path.expanduser('~/.handoff/projects'), project))
      "
      ```
      Then check whether that directory exists. If it exists, it may contain multiple bucket DBs (`default`, named profiles, `path-*`).

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

   c. **Active handoff sessions in target project DBs** — if `<PROJECT_HANDOFF_DIR>` exists, inspect every `handoff-data.db` file under it and sum `sessions` row counts. If non-zero, warn the user that the target workspace still has active handoff sessions and removing it will disconnect them.

    Include warnings in the summary (step 4) only when they are material to the user's decision. Use `🚨` only when there is real code-loss risk (for example unmerged commits or uncommitted work). If there is no code-loss risk, do not show warning signs; use a green check (for example `✅`) for safe status.

4. **Show summary** and confirm with the user before proceeding:
   > Removing worktree `<name>`:
   > - Worktree: `<path>`
   > - Branch: `<branch>`
   > - Chat groups: `<N>` found for workspace (or "none found" / "skipped — handoff not installed")
   > - Handoff DB dir: `<project_handoff_dir>` (or "none found")
   >
   > Proceed?

5. **Execute** cleanup in order:

   a. **Dissolve chat groups** (if any found):
      ```bash
      python3 $RMWT_SCRIPTS/dissolve_groups.py '<GROUPS_JSON>'
      ```
      This MUST run with `dangerouslyDisableSandbox: true` in Claude Code since it calls the Lark API.

   b. **Delete handoff project DB directory** (if found):
      ```bash
      rm -rf <PROJECT_HANDOFF_DIR>
      ```

   c. **Remove worktree**:
      ```bash
      git worktree remove <WORKTREE_PATH>
      ```

   d. **Delete branch**:
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
- Workspace ID calculation for different worktrees
- JSON output format from `list_workspace_groups.py`
- **Critical**: Workspace IDs are unique for different paths (prevents accidental deletion of wrong groups)
