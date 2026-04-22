---
name: recycle-wt
description: Recycle a merged git worktree — reset branch to main, rename, and reuse for new work.
allowed-tools: Bash
---

Recycle an existing worktree whose branch has been merged, repurposing it for new work without the overhead of `rmwt` + `mkwt`.

## Usage

`/recycle-wt <new-name>` — Recycle the current (or specified) worktree with a new branch name.

`/recycle-wt <worktree> <new-name>` — Recycle a specific worktree (matched by name from `git worktree list`).

If `<new-name>` is not provided, ask the user.

## Workflow

### 1. Resolve the worktree

If inside a secondary worktree (not the main repo), use the current directory. Otherwise, run `git worktree list` and match `<worktree>` against paths (case-insensitive). If no match or multiple matches, list them and ask.

Record:
- `WORKTREE_PATH` — the absolute path
- `OLD_BRANCH` — from the brackets in `git worktree list` output
- `DEFAULT_BRANCH` — detect via: `git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@'`

### 2. Safety checks

a. **Uncommitted changes:**
   ```bash
   git -C $WORKTREE_PATH status --porcelain
   ```
   If non-empty → stop with error: "Worktree has uncommitted changes. Commit, stash, or discard them first."

b. **Branch content not in main:**
   ```bash
   git -C $WORKTREE_PATH fetch origin $DEFAULT_BRANCH
   git -C $WORKTREE_PATH diff origin/$DEFAULT_BRANCH..$OLD_BRANCH -- $(git -C $WORKTREE_PATH diff origin/$DEFAULT_BRANCH...$OLD_BRANCH --name-only) --stat
   ```
   If non-empty → stop with error: "Branch has changes not in main. Merge or discard them first."

   **Pitfall — three-dot vs two-dot diff after squash merge:**
   - `git log main..branch` — WRONG. After squash merge the original commits still exist (different SHAs), so this always shows them.
   - `git diff main...branch` (three dots) — ALSO WRONG. Three-dot diff compares branch against the merge-base (fork point), not against current main. After squash merge, the merge-base is still the old fork point, so the diff shows the branch's changes even though main already has them.
   - `git diff main..branch` (two dots) — CORRECT. Two-dot diff compares the actual trees at both tips. If main already contains the same content (via squash merge), the diff is empty for those files.

   The command above scopes the two-dot diff to only the files the branch touched (via `--name-only` from three-dot), so unrelated main changes don't cause false positives.

c. **New branch name already exists:**
   ```bash
   result=$(git branch --list <new-name>); if [ -n "$result" ]; then echo "EXISTS"; else echo "FREE"; fi
   ```
   Check **output**, not exit code (`git branch --list` always exits 0). If EXISTS → stop.

### 3. Delete old remote branch (tolerant)

```bash
git push origin --delete $OLD_BRANCH 2>/dev/null || true
```

PR auto-delete may have already removed it — ignore errors.

### 4. Rename local branch

```bash
git -C $WORKTREE_PATH branch -m $OLD_BRANCH <new-name>
```

### 5. Hard-reset to latest main

**Must use `--hard`.** A soft reset leaves the worktree out of sync (files stay at the old commit's version).

```bash
git -C $WORKTREE_PATH fetch origin $DEFAULT_BRANCH
git -C $WORKTREE_PATH reset --hard origin/$DEFAULT_BRANCH
```

### 6. Push new branch to remote

```bash
git -C $WORKTREE_PATH push -u origin <new-name>
```

This requires `dangerouslyDisableSandbox: true` since it writes to the network.

### 7. Print result

> Recycled worktree at `<WORKTREE_PATH>`:
> - Branch: `<OLD_BRANCH>` → `<new-name>`
> - Aligned with `origin/<DEFAULT_BRANCH>` at `<short-sha>`
> - Remote: pushed `<new-name>`
