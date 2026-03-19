---
name: codex-review
description: Multi-round code review loop between Claude and OpenAI Codex. Claude writes code, Codex reviews, Claude fixes, repeat. Use when the user says "codex review", "let codex review", "codex 看看", or wants a second-opinion review from GPT/Codex.
allowed-tools: Bash, Read, Glob, Grep, Edit, Write
---

# codex-review

Run a multi-round code review loop: Claude writes/edits code, Codex reviews it non-interactively, Claude incorporates feedback, repeat until Codex approves or max rounds reached.

## Prerequisites

- `codex` CLI installed and authenticated (`npm i -g @openai/codex` + `codex login`)
- Codex configured with a model in `~/.codex/config.toml`

## Trigger

Activate when the user mentions "codex review", "let codex review", "codex 看看", "second opinion", or wants Codex/GPT to review code.

## Usage

`/codex-review [scope] [focus]`

- **scope** (optional): what to review
  - `--uncommitted` (default) — staged + unstaged + untracked changes
  - `--commit HEAD` — last commit
  - `--base main` — current branch vs main
- **focus** (optional): custom review instructions, e.g. "focus on security" or "check error handling"

Examples:
```
/codex-review
/codex-review --base main focus on performance
/codex-review --commit HEAD 重点看安全问题
```

## Workflow

### Step 1: Initial Review

Run Codex review on the specified scope:

```bash
codex review <scope> "<focus instructions>"
```

Default scope is `--uncommitted`. If the user specified a focus, append it as the prompt.

Parse the output. Codex review outputs markdown with findings.

### Step 2: Evaluate Findings

Read the Codex review output. Categorize findings:
- **Critical** — bugs, security issues, data loss risks → must fix
- **Important** — performance, error handling, edge cases → should fix
- **Suggestions** — style, naming, documentation → nice to have

If Codex found no issues or only minor suggestions, report "Codex approved" and stop.

### Step 3: Fix Issues

For each Critical and Important finding:
1. Read the relevant code
2. Apply the fix
3. Brief note of what was changed

Do NOT fix mere style suggestions unless the user asked for it.

### Step 4: Re-review

Run `codex review --uncommitted` again to verify fixes and catch new issues.

Include context from the previous round in the prompt:
```bash
codex review --uncommitted "Previous round found: [summary of issues]. Verify these are fixed and check for any new issues."
```

### Step 5: Loop Control

- **Max rounds**: 3 (default). The user can override with e.g. `/codex-review 5 rounds`
- **Exit conditions**:
  - Codex reports no significant issues
  - Max rounds reached
  - User interrupts

### Step 6: Summary

After the loop ends, present a summary:
- Total rounds run
- Issues found and fixed per round
- Any remaining suggestions not addressed
- Final Codex verdict

## Notes

- Codex `review` is non-interactive and stateless — each call is fresh
- Context from previous rounds is passed via the prompt string
- The review runs against the working tree, so all Claude's edits are visible to Codex
- If `codex` is not installed or not authenticated, tell the user to run `codex login`
- Codex review respects the model configured in `~/.codex/config.toml`
- All `codex` commands MUST run with `dangerouslyDisableSandbox: true` (network access needed)
