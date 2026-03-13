---
name: inscribe
description: Capture rules, conventions, or code style guidelines into documentation files. Use when the user says "inscribe", "learn", "remember this rule", "add convention", or wants to persist coding guidelines.
allowed-tools: Read, Edit, Write, Glob, Grep
---

# inscribe

Capture coding conventions, rules, or best practices and persist them into the appropriate documentation files so they are remembered across sessions.

## Usage

`/inscribe [scope] [guideline]`

- **scope** (optional): `project` (default) or `global`
- **guideline** (optional): If omitted, conventions are extracted from recent conversation context.

### Scope

| Scope | Target | Description |
|-------|--------|-------------|
| `project` | Project documentation files | Conventions scoped to the current project. Auto-discovers target files. |
| `global` | User's global agent instructions | Conventions that apply across all projects for this user. |

When scope is `global`, discover the global instructions file heuristically instead of scanning project files. Search these locations in order and use the first that exists:

1. `~/.claude/AGENTS.md`
2. `~/.claude/CLAUDE.md`
3. `~/.config/opencode/AGENTS.md`
4. `~/.codex/AGENTS.md`

If none exist, check which agent tool directories are present (`~/.claude/`, `~/.config/opencode/`, `~/.codex/`) and create `AGENTS.md` in the first one found.

Steps 1–2 (project file discovery and selection) are skipped for global scope.

## Input Sources

- **Explicit parameter**: A guideline or rule passed directly (e.g., `/inscribe always use named exports`)
- **Conversation context**: Rules or patterns discussed earlier in the conversation
- **Both**: A guideline parameter that references or supplements conversation context

## Guardrails

- Always confirm with the user what exactly should be learned before writing.
- Never duplicate existing rules — check if the convention already exists in the target file.
- Append to the appropriate section, or create a new section if none fits.
- Preserve the existing format and style of each target file.
- Show the proposed addition and target file before writing.

## Workflow

### Step 0: Identify What to Learn

1. **If a guideline parameter is provided**: Use it as the primary input.
2. **If no parameter is provided**: Review the recent conversation for rules, conventions, or patterns that were discussed, corrected, or established. Summarize them.
3. **If both**: Combine the explicit guideline with conversation context.

Present the identified convention(s) to the user and ask to confirm or refine.

### Step 1: Discover Target Files (project scope only)

Skip this step if scope is `global`.

Scan the project to find existing documentation files where conventions might live. Search for:

```
**/AGENTS.md
**/CLAUDE.md
**/code-style*.md
**/coding-style*.md
**/conventions*.md
**/guidelines*.md
docs/**/*.md
.claude/skills/*/SKILL.md
.opencode/skills/*/SKILL.md
```

Build a target table from the discovered files. Classify each by scope (language, framework, platform, project-wide, skill) based on its path and content. For skill files (`SKILL.md`), use the skill name from the directory or frontmatter.

**Fallback priority** when no documentation files are found:
1. `AGENTS.md` in the project root (create if absent)
2. `CLAUDE.md` in the project root (create if absent)

### Step 2: Select Target File (project scope only)

Skip this step if scope is `global`.

Present the discovered files to the user with their inferred scope. Let the user:
- **Pick** from the list
- **Specify a new path** (the skill will create the file)
- **Accept the auto-suggestion** if the convention clearly matches one file's scope

Auto-suggestion rules:
- Language/framework-specific conventions → file whose path or content matches that language
- Skill-specific conventions → the relevant `SKILL.md` file
- Project-wide rules → `AGENTS.md` or the root-level conventions file
- AI behavior instructions → `AGENTS.md` or `CLAUDE.md`

### Step 3: Check for Duplicates

Read the target file and search for existing rules that cover the same topic. If a similar convention already exists, alert the user and ask: **Update existing**, **Add alongside**, or **Skip**.

### Step 4: Draft the Addition

Compose the new convention entry matching the target file's existing format:

- **code-style files**: Use the pattern of the existing sections — heading level, code examples with good/bad markers, explanations
- **AGENTS.md / CLAUDE.md**: Use the existing bullet/section style
- **New files**: Use a simple heading + bullet list format

Present the draft showing target file, section, and content. Ask to confirm: **Add**, **Edit first**, or **Cancel**.

### Step 5: Write and Confirm

1. Add the convention to the target file in the appropriate section.
2. Print confirmation with file path, section, and summary.
3. Ask whether to commit — **Do NOT commit without the user's explicit confirmation.** Use commit message `docs: inscribe <brief summary>`.

## Examples

```
/inscribe always use named exports in TypeScript
/inscribe global never use console.log in production code
/inscribe project use SnapKit for all layout constraints
/inscribe all API response types must use Zod schemas
/inscribe global 所有项目都要用 AGENTS.md 作为主指令文件
/inscribe
```
