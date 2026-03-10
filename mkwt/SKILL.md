---
name: mkwt
description: Create a new git worktree with a branch from the repo's default branch.
allowed-tools: Bash
---

Create a new git worktree and branch.

## Usage

`/mkwt <name>` — Create a worktree with a new branch `<name>` from the repo's default branch (e.g. `main`, `dev`).

The `<name>` argument is required. If not provided, ask the user for a name.

## Workflow

1. **Validate** the name argument is provided.

2. **Detect the worktree base directory** by inspecting existing worktrees:
   ```bash
   git worktree list
   ```
   - Look at paths of worktrees OTHER than the main worktree (the first entry, which is the repo itself).
   - If secondary worktrees exist, derive the base directory from their common parent. For example, if existing worktrees are at `/Users/foo/worktrees/meadow/branch_a` and `/Users/foo/worktrees/meadow/branch_b`, the base is `/Users/foo/worktrees/meadow/`.
   - If NO secondary worktrees exist (only the main repo), ask the user where to create the worktree.

3. **Check** the branch doesn't already exist:
   ```bash
   result=$(git branch --list <name>); if [ -n "$result" ]; then echo "EXISTS"; else echo "FREE"; fi
   ```
   **Important:** `git branch --list` always exits 0, even with no matches. You must check the **output** (non-empty = exists), not the exit code.
   If it exists, tell the user and stop.

4. **Check** the worktree path doesn't already exist:
   ```bash
   ls <BASE_DIR>/<name>
   ```
   If it exists, tell the user and stop.

5. **Confirm** with the user before creating:
   > Create worktree `<name>` at `<BASE_DIR>/<name>` (new branch from `<DEFAULT_BRANCH>`)?

6. **Create** the worktree:
   ```bash
   git worktree add <BASE_DIR>/<name> -b <name>
   ```
   **Important:** This command writes outside the project directory, so it requires `dangerouslyDisableSandbox: true`. If it fails due to sandbox restrictions, the branch may still be created (partial failure). Delete the branch with `git branch -d <name>` before retrying.

7. **Print** the result:
   > Created worktree `<name>` at `<BASE_DIR>/<name>`.
