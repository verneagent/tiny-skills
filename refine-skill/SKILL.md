---
name: refine-skill
description: Refine or improve an existing skill's code. Automatically syncs changes to the skill's local source folder when it's a user-level skill not tracked by the current project's git. Use when the user says "refine", "improve", or "fix" a skill.
allowed-tools: Bash, Read, Glob, Grep, Edit, Write, Agent
---

# refine-skill

Refine, improve, or fix an existing skill. When the skill lives outside the current project's git (e.g., under `~/.agents/skills/` or `~/.claude/skills/`), automatically sync changes back to its canonical source folder.

## Usage

```
/refine-skill <skill-name> <what to change>
```

Or invoked implicitly when the user asks to improve/fix a skill.

## Workflow

### Step 1: Locate the skill

Find the skill files. Check in order:
1. `.claude/skills/<name>/` in the current project
2. `~/.claude/skills/<name>/`
3. `~/.agents/skills/<name>/`

### Step 2: Determine git tracking

Check if the skill's files are tracked by the current project's git:

```bash
git ls-files --error-unmatch <skill-path> 2>/dev/null
```

- **Tracked**: Changes will be committed with the project. No extra sync needed.
- **Not tracked**: This is a user-level skill. After making changes, sync to the local source folder (Step 4).

### Step 3: Make the changes

Read the relevant files, understand the current implementation, and apply the requested improvement.

### Step 4: Sync to local source folder (user-level skills only)

If the skill is not git-tracked, look up its **source folder** from the mapping below and copy the changed files there.

#### Source Folder Mapping

Read `~/.refine-skill/folder-map.json` — a JSON object mapping skill names to their source folder paths:

```json
{
  "handoff": "~/code/verneagent/handoff",
  "repo2skill": "~/code/verneagent/tiny-skills"
}
```

Values point to the folder containing the skill (which may be a repo root or a parent directory with multiple skills as subdirectories).

If the file doesn't exist or the skill isn't in it, ask the user where the source folder is. When they provide one, save it to the map for future use.

#### Sync procedure

1. Identify which files were changed
2. For each changed file, find the corresponding path in the local repo
3. Show a diff summary and confirm before copying
4. Copy the files
5. Report what was synced

### Step 5: Verify

- If the skill has tests, run them
- Confirm the changes work as expected

## Notes

- Always read the skill's SKILL.md before making changes to understand its architecture
- When syncing to a source folder, file structure may differ between installed copy and source — match by filename, not path
- Never auto-commit to the source folder. Just copy the files and let the user commit
