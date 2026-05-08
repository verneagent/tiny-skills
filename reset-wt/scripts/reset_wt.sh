#!/usr/bin/env bash
# reset-wt: discard ALL changes in a worktree's branch and align with origin/<default>.
# Usage: reset_wt.sh <summary|apply> [worktree-path]
#   If worktree-path is omitted, uses the current directory.
set -euo pipefail

MODE="${1:?Usage: reset_wt.sh <summary|apply> [worktree-path]}"
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
BRANCH=$(git -C "$WORKTREE_PATH" rev-parse --abbrev-ref HEAD 2>/dev/null)
if [ -z "$BRANCH" ] || [ "$BRANCH" = "HEAD" ]; then
  echo "ERROR: Worktree is in detached HEAD state." >&2
  exit 1
fi
if [ "$BRANCH" = "$DEFAULT_BRANCH" ]; then
  echo "ERROR: Refusing to reset the default branch '$DEFAULT_BRANCH'." >&2
  exit 1
fi

# --- Refresh remote refs ---
git -C "$WORKTREE_PATH" fetch origin "$DEFAULT_BRANCH" --quiet
# Fetch the branch's remote ref if it exists; ignore failure (branch may be local-only).
git -C "$WORKTREE_PATH" fetch origin "$BRANCH" --quiet 2>/dev/null || true

case "$MODE" in
  summary)
    echo "Worktree:       $WORKTREE_PATH"
    echo "Branch:         $BRANCH"
    echo "Default branch: $DEFAULT_BRANCH"
    echo ""

    # Uncommitted changes (includes untracked as '??')
    STATUS=$(git -C "$WORKTREE_PATH" status --porcelain)
    if [ -n "$STATUS" ]; then
      COUNT=$(printf '%s\n' "$STATUS" | wc -l | tr -d ' ')
      echo "Uncommitted + untracked files ($COUNT):"
      printf '%s\n' "$STATUS" | head -30 | sed 's/^/  /'
      [ "$COUNT" -gt 30 ] && echo "  ... and $((COUNT - 30)) more"
      echo ""
    else
      echo "Uncommitted + untracked: none"
      echo ""
    fi

    # Local commits ahead of origin/<default>
    LOCAL_AHEAD=$(git -C "$WORKTREE_PATH" log "origin/$DEFAULT_BRANCH..HEAD" --oneline)
    if [ -n "$LOCAL_AHEAD" ]; then
      COUNT=$(printf '%s\n' "$LOCAL_AHEAD" | wc -l | tr -d ' ')
      echo "Local commits ahead of origin/$DEFAULT_BRANCH ($COUNT):"
      printf '%s\n' "$LOCAL_AHEAD" | sed 's/^/  /'
      echo ""
    else
      echo "Local commits ahead: none"
      echo ""
    fi

    # Remote branch commits ahead of origin/<default>
    if git -C "$WORKTREE_PATH" rev-parse --verify --quiet "refs/remotes/origin/$BRANCH" >/dev/null; then
      REMOTE_AHEAD=$(git -C "$WORKTREE_PATH" log "origin/$DEFAULT_BRANCH..origin/$BRANCH" --oneline)
      if [ -n "$REMOTE_AHEAD" ]; then
        COUNT=$(printf '%s\n' "$REMOTE_AHEAD" | wc -l | tr -d ' ')
        echo "Remote commits on origin/$BRANCH ahead of origin/$DEFAULT_BRANCH ($COUNT):"
        printf '%s\n' "$REMOTE_AHEAD" | sed 's/^/  /'
        echo ""
      else
        echo "Remote commits ahead: none (origin/$BRANCH is at or behind origin/$DEFAULT_BRANCH)"
        echo ""
      fi
    else
      echo "Remote branch origin/$BRANCH: does not exist (nothing to force-push)"
      echo ""
    fi

    echo "Apply will:"
    echo "  1. git reset --hard origin/$DEFAULT_BRANCH"
    echo "  2. git clean -fd  (untracked files; keeps ignored like node_modules)"
    if git -C "$WORKTREE_PATH" rev-parse --verify --quiet "refs/remotes/origin/$BRANCH" >/dev/null; then
      echo "  3. git push --force-with-lease origin $BRANCH"
    else
      echo "  3. git push -u origin $BRANCH"
    fi
    ;;

  apply)
    echo "Resetting $BRANCH to origin/$DEFAULT_BRANCH..."
    git -C "$WORKTREE_PATH" reset --hard "origin/$DEFAULT_BRANCH" --quiet

    echo "Cleaning untracked files (keeping ignored)..."
    git -C "$WORKTREE_PATH" clean -fd --quiet

    if git -C "$WORKTREE_PATH" rev-parse --verify --quiet "refs/remotes/origin/$BRANCH" >/dev/null; then
      echo "Force-pushing $BRANCH to origin..."
      git -C "$WORKTREE_PATH" push --force-with-lease origin "$BRANCH"
    else
      echo "Pushing $BRANCH to origin (new branch)..."
      git -C "$WORKTREE_PATH" push -u origin "$BRANCH"
    fi

    SHORT_SHA=$(git -C "$WORKTREE_PATH" rev-parse --short HEAD)
    echo ""
    echo "Done! Worktree $WORKTREE_PATH:"
    echo "  Branch '$BRANCH' aligned with origin/$DEFAULT_BRANCH at $SHORT_SHA"
    ;;

  *)
    echo "ERROR: Unknown mode '$MODE'. Use 'summary' or 'apply'." >&2
    exit 1
    ;;
esac
