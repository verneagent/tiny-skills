---
name: claude-review
description: Multi-round code review with optional Review Army (parallel specialist subagents). Use when the user says "claude review", "let claude review", "claude 看看", or wants Claude's opinion on code.
allowed-tools: Bash, Read, Glob, Grep, Edit, Write, Agent
---

# claude-review

Code review with two modes: **Standard** (single-pass, fast) and **Army** (parallel specialist subagents, thorough). Supports multi-round fix loops in both modes.

## Prerequisites

- `claude` CLI installed and authenticated (Claude Code)
- Current directory must be a code project

## Trigger

Activate when the user mentions "claude review", "let claude review", "claude 看看", or wants Claude to review code.

## Usage

`/claude-review [--army] [scope] [focus]`

- **--army** (optional): enable Review Army mode (parallel specialists). Auto-enabled for `branch` scope.
- **scope** (optional): what to review
  - `uncommitted` (default) — review working tree changes
  - `commit` — review the last commit
  - `branch` — review current branch vs main (auto-enables army)
- **focus** (optional): custom review instructions

Examples:
```
/claude-review
/claude-review --army
/claude-review branch focus on error handling
/claude-review commit check for security issues
```

## Mode Selection

| Condition | Mode |
|---|---|
| `--army` flag | Army |
| scope is `branch` | Army |
| diff > 500 lines | Army |
| otherwise | Standard |

---

## Standard Mode

For small, focused changes. Single reviewer, fast feedback.

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

### Step 2–6: Evaluate → Fix → Re-review → Loop → Summary

(Same as Army mode steps 3–7 below.)

---

## Army Mode

Dispatches parallel specialist subagents, each reviewing from a different angle. Merges and deduplicates findings.

### Step 1: Gather Diff

```bash
# Capture the diff based on scope
DIFF=$(git diff --no-color HEAD)          # uncommitted
DIFF=$(git show --no-color HEAD)          # commit
DIFF=$(git diff --no-color main...HEAD)   # branch
```

Also gather context: list of changed files, languages involved, whether there are migration files, API route changes, test files, config changes, etc. This context determines which specialists to dispatch.

### Step 2: Dispatch Review Army

Launch specialist subagents **in parallel** using the Agent tool. Each agent receives the diff and a focused checklist. Only dispatch specialists relevant to the changes (skip others).

**Specialists:**

1. **Security** — injection flaws, auth/authz gaps, secrets in code, input validation, OWASP Top 10
2. **Performance** — O(n²) loops, N+1 queries, missing indexes, unnecessary allocations, blocking calls in hot paths
3. **Correctness** — logic errors, off-by-one, nil/null handling, race conditions, error swallowing, edge cases
4. **Testing** — untested critical paths, missing edge case tests, test quality, mocking correctness
5. **API Contract** — breaking changes, missing validation, inconsistent naming, missing error responses, versioning
6. **Data & Migration** — schema safety, backward compatibility, data loss risk, rollback plan
7. **Red Team** — runs LAST, receives other specialists' findings, explicitly tries to find what they missed

**Agent prompt template** (adapt per specialist):

```
You are a {SPECIALIST} code reviewer. Review this diff and report findings.

Context:
- Changed files: {FILE_LIST}
- Languages: {LANGUAGES}
- Focus: {USER_FOCUS}

Diff:
{DIFF}

Checklist:
{SPECIALIST_CHECKLIST}

Output format — JSON array:
[
  {
    "severity": "critical|important|suggestion",
    "category": "{specialist_name}",
    "file": "path/to/file",
    "line": 42,
    "finding": "description of the issue",
    "suggestion": "how to fix it"
  }
]

Only report real issues. If nothing found, return [].
```

**Dispatch rules:**
- Security, Correctness: always dispatch
- Performance: dispatch if diff > 100 lines or touches hot paths
- Testing: dispatch if test files exist or should exist
- API Contract: dispatch if route/handler/API files changed
- Data & Migration: dispatch if migration/schema files changed
- Red Team: always dispatch, but AFTER others complete — receives their findings as context

### Step 3: Merge & Deduplicate

Collect all specialist outputs. Merge into one list:
1. Parse each agent's JSON output
2. Deduplicate: same file + similar line range + similar finding → keep the more detailed one
3. Sort by severity: critical → important → suggestion
4. Present the merged findings as a numbered list with specialist attribution

### Step 4: Evaluate Findings

Categorize the merged findings:
- **Critical** — bugs, security, data loss → must fix
- **Important** — performance, error handling → should fix
- **Suggestions** — style, naming → nice to have

If no significant issues found, report "Review Army: all clear" and stop.

### Step 5: Fix Issues

Apply fixes for Critical and Important findings. Skip style-only suggestions unless the user asked.

### Step 6: Re-review

Run a **standard** single-pass re-review (not full army) to verify fixes:

```bash
git diff --no-color HEAD | claude -p "Previous review found these issues: [summary]. Verify they are fixed and check for new issues. ${FOCUS}"
```

### Step 7: Loop Control

- **Max rounds**: 3 (default). Army dispatch only on round 1; subsequent rounds use standard re-review.
- **Exit conditions**:
  - No significant issues remain
  - Max rounds reached
  - User interrupts

### Step 8: Summary

Present:
- Mode used (Standard / Army)
- Specialists dispatched and their finding counts
- Total issues: critical / important / suggestion
- Issues fixed per round
- Remaining suggestions
- Final verdict

## Notes

- `claude -p` runs non-interactively (print mode) — outputs review and exits
- Each CLI call is stateless; pass previous context via the prompt
- Army subagents are Claude Code Agent tool calls, not CLI — they run in-process
- Red Team agent receives other specialists' findings to avoid duplicating and to find gaps
- The review sees the current working tree, so all edits are visible
- If `claude` is not installed, tell the user to install Claude Code
- Works in both Codex and any other agent that can run shell commands
