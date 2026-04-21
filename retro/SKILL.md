---
name: retro
description: Retrospective on mistakes or new conventions — analyze patterns, find root causes, and propose deterministic prevention (static checks > lint > tests > runtime > review > docs). Use when the user says "retro", "反省", "复盘", "怎么防", "how to prevent", or wants to enforce a new convention.
allowed-tools: Bash, Read, Glob, Grep, Edit, Write, Agent, WebSearch, WebFetch
---

# retro

Analyze mistakes or new conventions, find patterns, and propose **deterministic prevention** — prioritizing machine-enforced guardrails over human discipline.

## Trigger Scenarios

1. **Post-incident retro** — something went wrong, analyze what happened and prevent recurrence
2. **Convention enforcement** — new infra/tool/rule that others must follow, how to make violation impossible

## Usage

```
/retro <description of what happened or what rule to enforce>
/retro                  # ask user for context
```

## Workflow

### Step 1: Understand

Gather context. Read relevant code, git history, CI logs, error messages. If the user provides a description, start from there. If not, ask.

Key questions to answer:
- **What went wrong?** (or: what rule needs enforcing?)
- **Why did it happen?** (root cause, not symptoms)
- **Is this a pattern?** Search for similar past occurrences (`git log`, `grep`)

### Step 2: Analyze

Identify the **failure pattern** — classify it:

| Pattern | Example |
|---------|---------|
| Wrong API usage | Called deprecated method, wrong parameter order |
| Missing validation | Nil check, bounds check, type assertion |
| Convention violation | Wrong file location, naming, import order |
| Config drift | Env mismatch, stale defaults |
| Integration gap | Works locally, breaks in CI/prod |
| Knowledge gap | Didn't know about existing util/constraint |

Look for **similar code** in the codebase that might have the same latent bug. Report how widespread the issue is.

### Step 3: Propose Prevention

Propose fixes in **strict priority order** — always prefer higher levels:

#### Priority 1: Make it impossible (compile/type-level)
- API design that makes wrong usage unrepresentable
- Type system enforcement (stronger types, generics, enums)
- Remove the footgun entirely (delete deprecated API, make breaking change)

#### Priority 2: Static analysis
- Custom lint rule (ESLint, golangci-lint, clippy, etc.)
- Compiler flags / strict mode
- `go vet`, `staticcheck` custom analyzers
- Pre-commit hooks

#### Priority 3: Automated tests
- Unit test that reproduces the exact failure
- Property-based / fuzz test for the category of failure
- Integration test at the boundary
- CI gate (test must pass to merge)

#### Priority 4: Runtime guards
- Assertion / panic early at the entry point
- Validation middleware
- Feature flag with safe default

#### Priority 5: Process / review
- PR template checklist item
- CODEOWNERS for sensitive paths
- Required reviewer for specific file patterns

#### Priority 6: Documentation (last resort)
- AGENTS.md / CLAUDE.md rule (for AI agents)
- README warning
- Code comment at the dangerous call site

### Step 4: Implement

For each proposed prevention:
1. **Show the concrete implementation** — not just "add a lint rule", but the actual rule code
2. **Estimate blast radius** — what existing code would be affected?
3. **Ask before applying** — present the plan, get confirmation

If the user confirms, implement the highest-priority prevention that's feasible. Create the lint rule, write the test, modify the API — don't just document.

### Step 5: Record

After implementing, save a brief entry for future reference:

```
<incident-or-rule>
Pattern: <pattern type>
Root cause: <why>
Prevention: <what was implemented>
Level: <which priority level>
```

Consider whether this should become:
- A **memory** (if it's a recurring pattern worth remembering across conversations)
- An **AGENTS.md rule** (if it should guide AI behavior in this repo)
- A **lint rule / test** (already implemented in Step 4)

## Style

- Be direct. "This broke because X. Here's how to make it impossible."
- Show code, not prose. The fix should be copy-pasteable.
- If a higher-priority prevention isn't feasible, explicitly state why before falling to a lower level.
- Language: match the user's language (zh/en).

## Examples

```
/retro 昨天有人把 staging 的配置提交到 prod 了
/retro we keep forgetting to update the changelog
/retro 新写了一个 cache layer，怎么确保大家都走 cache 不直接查 DB
/retro CI 又挂了因为有人引入了新依赖没更新 lock file
```
