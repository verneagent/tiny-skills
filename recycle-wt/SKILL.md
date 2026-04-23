---
name: recycle-wt
description: Recycle a merged git worktree — reset branch to main, rename, and reuse for new work.
allowed-tools: Bash
---

Recycle an existing worktree whose branch has been merged, repurposing it for new work without the overhead of `rmwt` + `mkwt`.

## Skill Path

```bash
RECYCLE_WT_SCRIPTS=$(python3 -c "import os; p='.claude/skills/recycle-wt/scripts'; print(os.path.abspath(p) if os.path.isdir(p) else os.path.expanduser('~/.agents/skills/recycle-wt/scripts'))")
```

## Usage

`/recycle-wt <new-name>` — Recycle the current (or specified) worktree with a new branch name.

`/recycle-wt <worktree> <new-name>` — Recycle a specific worktree (matched by name from `git worktree list`).

If `<new-name>` is not provided, ask the user.

## Workflow

### 1. Resolve arguments

- If two args: first is worktree identifier, second is new name.
  - Run `git worktree list` and match the first arg against paths (case-insensitive basename match). If no match or multiple matches, list them and ask.
  - Use the matched worktree path.
- If one arg: use current directory as worktree path, arg is new name.
- If no args: ask the user.

### 2. Run the script

```bash
bash $RECYCLE_WT_SCRIPTS/recycle_wt.sh <new-name> <worktree-path>
```

This requires `dangerouslyDisableSandbox: true` since it pushes to remote.

The script handles all safety checks, branch operations, and prints the result. If it exits non-zero, report the error to the user.
