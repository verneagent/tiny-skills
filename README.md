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
| **rmwt** | Remove a git worktree, its branch, and associated handoff resources. |
| **wksp** | Open a new iTerm2 tab with Claude in a worktree or folder. |

## Install (global)

Clone the repo and run the fan-out script to symlink all skills into your agent directories:

```bash
git clone https://github.com/verneagent/tiny-skills.git ~/code/verneagent/tiny-skills

# Install all skills
rsync -a --delete \
  --exclude='.git/' --exclude='__pycache__/' --exclude='.DS_Store' --exclude='node_modules/' \
  ~/code/verneagent/tiny-skills/<skill-name>/ ~/.agents/skills/<skill-name>/

# Fan out symlinks to all agent directories
python3 ~/.agents/skills/adhoc-skill/scripts/fanout.py --all
```

Or install a single skill:

```bash
rsync -a --delete \
  --exclude='.git/' --exclude='__pycache__/' --exclude='.DS_Store' \
  ~/code/verneagent/tiny-skills/<skill-name>/ ~/.agents/skills/<skill-name>/
python3 ~/.agents/skills/adhoc-skill/scripts/fanout.py <skill-name>
```

The fan-out script auto-discovers which agent directories already participate in the `~/.agents/skills/` symlink pattern (e.g., `~/.claude/skills/`, `~/.config/opencode/skills/`, `~/.codex/skills/`).

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
