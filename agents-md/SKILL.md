---
name: agents-md
description: Consolidate repository agent instructions by making AGENTS.md the canonical source of truth and reducing CLAUDE.md to a redirect. Use when a user asks to integrate, sync, deduplicate, or adopt a redirect-based setup for CLAUDE.md and AGENTS.md.
---

# Agent Instructions

Use this skill when a user wants to standardize repository-level agent instructions, especially when they mention:

- integrating `CLAUDE.md` and `AGENTS.md`
- making one file the source of truth
- adopting a redirect-based pattern
- removing duplicated guidance across agent-specific instruction files

## Goal

Make `AGENTS.md` the shared instruction entrypoint for the repo.

In the common case:

1. Move or merge reusable repository guidance into `AGENTS.md`.
2. Reduce `CLAUDE.md` to a single `@AGENTS.md` redirect.
3. Keep agent-specific differences only if they are truly necessary.

## Workflow

1. Read the current `CLAUDE.md` and `AGENTS.md` if they exist.
2. Identify which content is shared repo guidance versus tool-specific behavior.
3. Put the shared, durable guidance in `AGENTS.md`.
4. Remove duplication so `CLAUDE.md` does not drift from `AGENTS.md`.
5. If the repo follows the redirect-based setup, replace `CLAUDE.md` with exactly `@AGENTS.md`.
6. Verify that no important instruction was dropped during consolidation.

## Rules

- Prefer one source of truth over mirrored copies.
- Preserve repository-specific rules; do not overwrite them with generic boilerplate.
- Keep `AGENTS.md` concise and repo-focused.
- Do not invent extra files unless the repo already uses a multi-level instruction layout.
- If a subdirectory already has its own `AGENTS.md`, keep the root file focused on root-level guidance and references to child scopes.

## Verification

After editing:

- diff `CLAUDE.md` and `AGENTS.md`
- confirm `CLAUDE.md` is only a redirect when using the redirect-based pattern
- check that any previously documented repo rules still exist in `AGENTS.md`
