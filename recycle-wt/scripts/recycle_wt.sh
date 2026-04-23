#!/usr/bin/env bash
# recycle-wt: recycle a merged git worktree for new work.
# Usage: recycle_wt.sh <new-name> [worktree-path]
#   If worktree-path is omitted, uses the current directory.
set -euo pipefail

NEW_NAME="${1:?Usage: recycle_wt.sh <new-name> [worktree-path]}"
WORKTREE_PATH="${2:-$(pwd)}"
WORKTREE_PATH="$(cd "$WORKTREE_PATH" && pwd)"

# --- Detect default branch ---
DEFAULT_BRANCH=$(git -C "$WORKTREE_PATH" symbolic-ref refs/remotes/origin/HEAD 2>/dev/null \
  | sed 's@^refs/remotes/origin/@@')
if [ -z "$DEFAULT_BRANCH" ]; then
  echo "ERROR: Cannot detect default branch. Run: git remote set-head origin --auto" >&2
  exit 1
fi

# --- Detect current branch ---
OLD_BRANCH=$(git -C "$WORKTREE_PATH" rev-parse --abbrev-ref HEAD 2>/dev/null)
if [ -z "$OLD_BRANCH" ] || [ "$OLD_BRANCH" = "HEAD" ]; then
  echo "ERROR: Worktree is in detached HEAD state." >&2
  exit 1
fi

echo "Worktree:       $WORKTREE_PATH"
echo "Old branch:     $OLD_BRANCH"
echo "New branch:     $NEW_NAME"
echo "Default branch: $DEFAULT_BRANCH"
echo ""

# --- Safety: uncommitted changes ---
if [ -n "$(git -C "$WORKTREE_PATH" status --porcelain)" ]; then
  echo "ERROR: Worktree has uncommitted changes. Commit, stash, or discard them first." >&2
  exit 1
fi

# --- Safety: branch content not in main ---
git -C "$WORKTREE_PATH" fetch origin "$DEFAULT_BRANCH" --quiet
TOUCHED_FILES=$(git -C "$WORKTREE_PATH" diff "origin/$DEFAULT_BRANCH...$OLD_BRANCH" --name-only)
if [ -n "$TOUCHED_FILES" ]; then
  DIFF_STAT=$(git -C "$WORKTREE_PATH" diff "origin/$DEFAULT_BRANCH..$OLD_BRANCH" -- $TOUCHED_FILES --stat)
  if [ -n "$DIFF_STAT" ]; then
    echo "ERROR: Branch has changes not in $DEFAULT_BRANCH:" >&2
    echo "$DIFF_STAT" >&2
    exit 1
  fi
fi

# --- Safety: new branch name already exists ---
if [ -n "$(git branch --list "$NEW_NAME")" ]; then
  echo "ERROR: Branch '$NEW_NAME' already exists." >&2
  exit 1
fi

# --- Delete old remote branch (tolerant) ---
echo "Deleting remote branch '$OLD_BRANCH'..."
git push origin --delete "$OLD_BRANCH" 2>/dev/null || true

# --- Rename local branch ---
echo "Renaming branch: $OLD_BRANCH -> $NEW_NAME"
git -C "$WORKTREE_PATH" branch -m "$OLD_BRANCH" "$NEW_NAME"

# --- Hard-reset to latest main ---
echo "Resetting to origin/$DEFAULT_BRANCH..."
git -C "$WORKTREE_PATH" reset --hard "origin/$DEFAULT_BRANCH" --quiet

# --- Push new branch to remote ---
echo "Pushing '$NEW_NAME' to remote..."
git -C "$WORKTREE_PATH" push -u origin "$NEW_NAME" --quiet

# --- Result ---
SHORT_SHA=$(git -C "$WORKTREE_PATH" rev-parse --short HEAD)
echo ""
echo "Done! Recycled worktree at $WORKTREE_PATH:"
echo "  Branch: $OLD_BRANCH -> $NEW_NAME"
echo "  Aligned with origin/$DEFAULT_BRANCH at $SHORT_SHA"
echo "  Remote: pushed $NEW_NAME"
