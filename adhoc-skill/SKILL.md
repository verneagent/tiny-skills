---
name: adhoc-skill
description: Add a new user-level skill quickly. Use when a just-learned workflow should become a reusable skill installed from ~/.agents/skills into the current machine's shared skill fan-out.
---

# Ad Hoc Skill

Use this skill when a user wants to turn a just-learned workflow into a reusable `user-level` skill.

Before writing the skill itself, use `skill-creator` and follow its rules.

This skill adds only the extra local installation rule for shared `user-level` skills.

## Scope

This applies only to `user-level` skills whose canonical source lives under:

- `~/.agents/skills/<skill-name>/`

It does not apply to `project-level` skills that should remain inside a project.

## Local Installation Rule

Do not hardcode target agents from memory.

Instead, reverse-check the current machine's symlink graph and discover which agent-facing skill directories already consume shared skills from `~/.agents/skills/`.

Install the new skill by mirroring that existing fan-out pattern.

## Workflow

1. Use `skill-creator` to create the skill content.
2. Put the canonical source under `~/.agents/skills/<skill-name>/`.
3. Run the fan-out script to create symlinks in all agent-facing directories:
   ```bash
   python3 ~/.agents/skills/adhoc-skill/scripts/fanout.py <skill-name>
   ```
4. Verify the output shows all targets succeeded.

## Reverse Check

Use the current machine state as the source of truth.

A practical way is to inspect likely agent skill roots and keep only symlinks whose real target resolves under `~/.agents/skills/`.

Examples of agent-facing roots on this machine may include:

- `~/.codex/skills/`
- `~/.claude/skills/`
- `~/.config/opencode/skills/`

But the rule is to mirror the discovered shared-skill fan-out, not to blindly assume those paths always apply.

## Preferred Outcome

The skill is written once under `~/.agents/skills/` and exposed everywhere on the current machine that already consumes shared `user-level` skills.
