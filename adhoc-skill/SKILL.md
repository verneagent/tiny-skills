---
name: adhoc-skill
description: Create, refine, or sync user-level skills. Works in the skill's source repo first, then syncs to ~/.agents/skills and fans out symlinks. Use when the user says "create skill", "refine skill", "install skill", "sync skill", "deploy skill", "improve skill", "fix skill", "edit skill", "simplify skill", "改进 skill", "创建 skill", "编辑 skill", or "简化 skill".
allowed-tools: Bash, Read, Glob, Grep, Edit, Write, Agent
---

# adhoc-skill

Manage user-level skills: create new ones, refine existing ones, or sync from repo to the installed location. All edits happen in the source repo first, then sync one-way to `~/.agents/skills/` and fan out.

## Config

`~/.adhoc-skill/config.json`:

```json
{
  "skill_roots": [
    "~/code/verneagent/tiny-skills",
    "~/code/verneagent"
  ]
}
```

`skill_roots` — directories to search for skill source repos. Each root is scanned for subdirectories containing `SKILL.md`.

If the config file doesn't exist, ask the user for their skill root directories and create it.

## Finding a skill

Search `skill_roots` in order. For each root, look for `<skill-name>/SKILL.md` as a direct child. Match by directory name or by the `name:` field in the SKILL.md frontmatter. First match wins.

## Operations

### Create (`/adhoc-skill create <name>`)

1. Ask the user: create as an **independent repo** (new git repo under a skill root) or as a **subdirectory** of an existing repo (e.g., `tiny-skills/<name>/`)? If only one root exists or the user specifies, skip asking.
2. Use `skill-creator` to write the skill content under the chosen location.
3. If independent repo: `git init` the new directory.
4. Sync to `~/.agents/skills/<name>/` (see Sync below).
5. Fan out symlinks.

### Refine (`/adhoc-skill refine <name> <what to change>`)

Also triggered implicitly when the user says "improve", "fix", or "refine" a skill.

1. Find the skill source repo using the search logic above.
2. Read and understand the current implementation.
3. Make the requested changes **in the source repo**.
4. Show a diff summary and confirm.
5. Sync to `~/.agents/skills/<name>/`.
6. Fan out symlinks.

### Sync (`/adhoc-skill sync <name>`)

Also triggered when the user says "install", "deploy", or "repo2skill".

1. Find the skill source repo.
2. If already installed at `~/.agents/skills/<name>/`, diff source vs installed and show changes.
3. Copy source to `~/.agents/skills/<name>/` (excluding `.git/`, `__pycache__/`, `.DS_Store`, `node_modules/`).
4. Fan out symlinks:
   ```bash
   python3 ~/.agents/skills/adhoc-skill/scripts/fanout.py <name>
   ```

### Sync All (`/adhoc-skill sync --all`)

Scan all skill roots, find every skill, and sync + fan out each one.

## Sync procedure

```bash
rsync -a --delete \
  --exclude='.git/' --exclude='__pycache__/' --exclude='.DS_Store' --exclude='node_modules/' \
  <source>/ ~/.agents/skills/<name>/
```

Then fan out:

```bash
python3 ~/.agents/skills/adhoc-skill/scripts/fanout.py <name>
```

## No args (`/adhoc-skill`)

If invoked with no arguments, list all known skills (scan skill_roots) with their status (installed/not installed, in sync/out of sync).

## Notes

- **One-way only**: repo → `~/.agents/skills/`. Never modify `~/.agents/skills/` directly.
- **Never auto-commit** to the source repo. Just edit the files and let the user commit.
- Always read `SKILL.md` before making changes to understand the skill's architecture.
- The fan-out script discovers targets automatically by checking which agent-facing directories already symlink into `~/.agents/skills/`.
