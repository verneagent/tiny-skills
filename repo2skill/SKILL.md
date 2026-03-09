---
name: repo2skill
description: Install a skill from a local git repo into ~/.agents/skills/ and fan out symlinks. The opposite of refine-skill. Use when the user says "install skill", "deploy skill", "repo2skill", or wants to push a skill from a repo to the agent skill directories.
allowed-tools: Bash, Read, Glob, Grep, Edit, Write
---

# repo2skill

Install a skill from a local git repo (or any directory containing a `SKILL.md`) into `~/.agents/skills/` and fan out symlinks to all agent-facing directories.

This is the inverse of `refine-skill`: instead of syncing changes from the installed skill back to the repo, it syncs from the repo to the installed location.

## Usage

```
/repo2skill [skill-name] [source-path]
```

- If `skill-name` is given, look for it in the current directory or use the source repo mapping.
- If `source-path` is given, use that directory directly.
- If neither is given, scan the current directory for subdirectories containing `SKILL.md` and list them.

## Workflow

### Step 1: Locate the source

Find the skill source. Check in order:

1. Explicit `source-path` argument
2. `./<skill-name>/` in the current directory (if it contains `SKILL.md`)
3. Source folder mapping in `~/.refine-skill/folder-map.json` (shared with refine-skill, reversed)
4. Ask the user

### Step 2: Validate

Confirm the source directory contains a `SKILL.md`. Read it to extract the skill name from the frontmatter `name:` field.

If the frontmatter name differs from the directory name, use the frontmatter name as the canonical skill name (this is what agents look up).

### Step 3: Preview changes

If the skill is already installed at `~/.agents/skills/<name>/`, diff the source against the installed version:

```bash
diff -rq <source> ~/.agents/skills/<name>/
```

Show a summary of new, changed, and deleted files. Ask for confirmation before proceeding.

If not installed yet, note this is a fresh install.

### Step 4: Install

Copy the skill to `~/.agents/skills/<name>/`:

```bash
rm -rf ~/.agents/skills/<name>/
cp -r <source> ~/.agents/skills/<name>/
```

### Step 5: Fan out symlinks

Run the fan-out script to create symlinks in all agent-facing directories:

```bash
python3 ~/.agents/skills/adhoc-skill/scripts/fanout.py <name>
```

### Step 6: Update folder mapping

If the source path is not already in `~/.refine-skill/folder-map.json`, add it so `refine-skill` can sync changes back later.

### Step 7: Report

Print a summary: what was installed, where it was linked, and whether the folder mapping was updated.

## Notes

- Never modify the source repo. This skill only reads from it.
- Always record the skill's own source folder (the directory containing `SKILL.md`) in the mapping, not a parent directory.
- Exclude `.git/`, `__pycache__/`, `.DS_Store`, and other common artifacts when copying.
