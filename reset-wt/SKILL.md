---
name: reset-wt
description: Discard ALL changes in the current git worktree (uncommitted, untracked, local commits, remote commits) and align the branch with origin/main. Always shows a summary and asks the user to confirm before doing anything destructive.
allowed-tools: Bash
---

Reset a worktree's branch hard to `origin/<default-branch>`, throwing away everything on the branch — uncommitted changes, untracked files, local commits, and remote commits. Used when the user wants to abandon a branch's work entirely and start fresh from main without recreating the worktree.

This is destructive and unrecoverable. The skill MUST show a summary and get explicit confirmation before applying.

## Skill Path

```bash
RESET_WT_SCRIPTS=$(python3 -c "import os; p='.claude/skills/reset-wt/scripts'; print(os.path.abspath(p) if os.path.isdir(p) else os.path.expanduser('~/.agents/skills/reset-wt/scripts'))")
```

## Usage

`/reset-wt` — Reset the current worktree's branch.

`/reset-wt <worktree>` — Reset a specific worktree (matched by name from `git worktree list`).

## Workflow

### 1. Resolve worktree path

- If an arg is given: run `git worktree list` and match the arg against paths (case-insensitive basename match). On no/multiple matches, list them and ask.
- Otherwise: use the current working directory.

### 2. Show the summary

```bash
bash $RESET_WT_SCRIPTS/reset_wt.sh summary <worktree-path>
```

Print the script's output verbatim to the user. The summary lists:

- Current branch and default branch
- Uncommitted + untracked files
- Local commits ahead of `origin/<default>`
- Remote commits on `origin/<branch>` ahead of `origin/<default>`

If the script exits non-zero (e.g. detached HEAD, or branch is the default branch), stop and report the error.

### 3. Ask the user to confirm

Show the summary, then ask explicitly, in the user's language, something like:

> 以上改动会全部被丢弃（本地未提交 / 未跟踪 / 本地 commit / 远端 commit），不可恢复。确认 reset 吗？

Wait for an explicit affirmative ("是" / "确认" / "yes" / "do it" / etc.). If the user hesitates, asks a follow-up, or does not clearly confirm, abort and do nothing.

### 4. Apply

```bash
bash $RESET_WT_SCRIPTS/reset_wt.sh apply <worktree-path>
```

Requires `dangerouslyDisableSandbox: true` (the script force-pushes to the remote).

The script:
1. `git reset --hard origin/<default-branch>`
2. `git clean -fd` (untracked files; keeps ignored files like `node_modules`)
3. `git push --force-with-lease origin <branch>` (or plain `-u` if the remote branch doesn't exist)

If the script exits non-zero, report the error and stop.
