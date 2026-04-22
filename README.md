# tiny-skills

A collection of user-level skills for AI coding agents (Claude Code, OpenCode, Codex CLI).

## Skills

| Skill | Description |
|-------|-------------|
| **adhoc-skill** | Create, refine, or sync user-level skills. All edits in repo first, then sync to `~/.agents/skills/` and fan out. |
| **agents-md** | Consolidate `AGENTS.md` as canonical source of truth, reduce `CLAUDE.md` to a redirect. |
| **genimg** | Generate or edit images via OpenAI-compatible APIs. Text-to-image and image-to-image. |
| **lark-share** | Send knowledge-sharing cards to a Lark group via webhook. |
| **mkwt** | Create a new git worktree with a branch from the repo's default branch. |
| **multi-gh** | Fix GitHub multi-account workflows — SSH host aliases, `gh` account switching, safe remotes. |
| **open-file** | Open a local file or directory with a specified app on macOS. |
| **recycle-wt** | Recycle a merged git worktree — reset branch to main, rename, and reuse for new work. |
| **rmwt** | Remove a git worktree, its branch, and associated handoff resources. |
| **inscribe** | Capture coding conventions and rules into documentation files. Supports `project` (default) and `global` scope. |
| **wksp** | Open a new iTerm2 tab with Claude in a worktree or folder. |

## Install (global)

Install all skills at once:

```bash
npx skills add -g verneagent/tiny-skills
```

Or install a single skill by name:

```bash
npx skills add -g verneagent/tiny-skills/adhoc-skill
```

This clones the repo, copies skills to `~/.agents/skills/`, and fans out symlinks to all agent directories (`~/.claude/skills/`, `~/.config/opencode/skills/`, `~/.codex/skills/`).

## Managing skills

Once `adhoc-skill` is installed, use it to manage all skills:

```
/adhoc-skill sync --all     # Sync all skills from repo to ~/.agents/skills/
/adhoc-skill sync <name>    # Sync a single skill
/adhoc-skill refine <name>  # Edit a skill in its source repo, then sync
/adhoc-skill create <name>  # Create a new skill
```

## Config

Some skills require per-machine config:

| Config file | Used by |
|-------------|---------|
| `~/.adhoc-skill/config.json` | adhoc-skill — skill root directories |
| `~/.lark-share/config.json` | lark-share — Lark webhook token |
| `~/.genimg/config.json` | genimg — image generation API keys |
