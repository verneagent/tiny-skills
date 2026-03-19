---
name: claude-review
description: Multi-round code review loop using Claude Code as reviewer. Codex writes code, Claude reviews via CLI, Codex fixes, repeat. Use when the user says "claude review", "let claude review", "claude 看看", or wants Claude's opinion on code written by Codex.
allowed-tools: Bash, Read, Glob, Grep, Edit, Write
---

# claude-review

Run a multi-round code review loop where Claude Code reviews code non-interactively. Designed for use inside Codex — Codex writes code, Claude reviews it, Codex incorporates feedback, repeat.

## Prerequisites

- `claude` CLI installed and authenticated (Claude Code)
- Current directory must be a code project

## Trigger

Activate when the user mentions "claude review", "let claude review", "claude 看看", or wants Claude to review code.

## Usage

`/claude-review [scope] [focus]`

- **scope** (optional): what to review
  - `uncommitted` (default) — review working tree changes
  - `commit` — review the last commit
  - `branch` — review current branch vs main
- **focus** (optional): custom review instructions

Examples:
```
/claude-review
/claude-review branch focus on error handling
/claude-review commit check for security issues
```

## Workflow

### Step 1: Initial Review

Build the review command based on scope:

```bash
# For uncommitted changes (default)
git diff --no-color HEAD | claude -p "Review this diff. Focus on: bugs, security, error handling, edge cases. Be specific about file and line. Output findings as a numbered list. ${FOCUS}"

# For last commit
git show --no-color HEAD | claude -p "Review this commit. ${FOCUS}"

# For branch vs main
git diff --no-color main...HEAD | claude -p "Review these branch changes. ${FOCUS}"
```

If there's no diff, check for untracked files:
```bash
git diff --no-color && git diff --no-color --cached && git ls-files --others --exclude-standard
```

Parse Claude's output — it returns a markdown review with findings.

### Step 2: Evaluate Findings

Read Claude's review output. Categorize:
- **Critical** — bugs, security, data loss → must fix
- **Important** — performance, error handling → should fix
- **Suggestions** — style, naming → nice to have

If no significant issues found, report "Claude approved" and stop.

### Step 3: Fix Issues

Apply fixes for Critical and Important findings. Skip style-only suggestions unless the user asked.

### Step 4: Re-review

Run the review again with context from previous round:

```bash
git diff --no-color HEAD | claude -p "Previous review found these issues: [summary]. Verify they are fixed and check for new issues. ${FOCUS}"
```

### Step 5: Loop Control

- **Max rounds**: 3 (default)
- **Exit conditions**:
  - Claude reports no significant issues
  - Max rounds reached
  - User interrupts

### Step 6: Summary

Present:
- Total rounds
- Issues found/fixed per round
- Remaining suggestions
- Final verdict

## Notes

- `claude -p` runs non-interactively (print mode) — outputs review and exits
- Each call is stateless; pass previous context via the prompt
- The review sees the current working tree, so all Codex edits are visible
- If `claude` is not installed, tell the user to install Claude Code
- Works in both Codex and any other agent that can run shell commands
