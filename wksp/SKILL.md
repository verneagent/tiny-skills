---
name: wksp
description: Open a new iTerm2 tab with Claude in a worktree or folder, optionally entering handoff mode.
allowed-tools: Bash, AskUserQuestion
---

Open a new terminal tab, cd to the given folder or worktree, and launch a coding tool (Claude Code or OpenCode) with a chosen model. Optionally auto-enter handoff mode.

**macOS only.** Uses AppleScript to open a new tab in iTerm2 (preferred) or Terminal.app (fallback).

## Usage

`/wksp <name-or-path> [with|using|as <model>]`

The `<name-or-path>` argument is required. If not provided, list worktrees and ask the user to pick one.

Natural language model specification:
- `/wksp spawn2 with haiku`
- `/wksp spawn2 using sonnet`
- `/wksp spawn2 as opus`

## Sandbox: CRITICAL

The `pretrust` step writes to `~/.claude.json` which requires `dangerouslyDisableSandbox: true`.

The `osascript` command MUST also run with `dangerouslyDisableSandbox: true`.

## Workflow

### Step 1: Parse natural language and resolve folder path

```bash
python3 -c "import sys; sys.path.insert(0, '~/.claude/skills/wksp'); from wksp_ops import parse_spawn_command; path, model = parse_spawn_command('<ARG>'); print(f'{path} {model or \"\"}'.strip())"
```

Then resolve path:
```bash
python3 ~/.claude/skills/wksp/wksp_ops.py resolve-spawn-path --arg '<PATH>'
```

If multiple matches are returned, ask user to choose. If none, stop.

### Step 1.5: Detect available tools and build model list

Before presenting options, check which tools are installed and gather models:
```bash
which claude && echo "claude:yes" || echo "claude:no"
which opencode && echo "opencode:yes" || echo "opencode:no"
```

If neither is installed, stop with an error.

**Claude Code models** (hardcoded): opus, sonnet, haiku

**OpenCode models** (dynamic — only fetch if OpenCode is installed):
```bash
opencode models
```
Parse the output — each line is a model ID (e.g. `openai/gpt-5.2`).

**Build the combined model list:**
- Start with Claude models as `["Opus (Claude)","claude:opus"], ["Sonnet (Claude)","claude:sonnet"], ["Haiku (Claude)","claude:haiku"]`
- Append OpenCode models as `["<model_id> (OpenCode)","opencode:<model_id>"]` for each model
- Default selection: `claude:opus`

The model value uses `tool:model` format so Claude can parse which tool to use from the selection.

### Step 2: Choose model and handoff

Present options using AskUserQuestion:

1. **Model**: Show numbered list of all available models (from Step 1.5) in `tool:model` format. If a model was already parsed from natural language in Step 1, pre-select it.
2. **Handoff**: Ask whether to auto-enter handoff mode (default: yes).

Parse `tool` and `model` from the selected value by splitting on `:` (first part = tool, rest = model).

### Step 4: Pre-trust workspace

```bash
python3 ~/.claude/skills/wksp/wksp_ops.py pretrust --path '<RESOLVED_PATH>'
```

This writes `~/.claude.json` and must run with `dangerouslyDisableSandbox: true`.

### Step 5: Open terminal tab and launch

Use `launch.py` to build the shell command and open a new terminal tab. The script auto-detects iTerm2 vs Terminal.app via the bundled AppleScript.

```bash
python3 ~/.claude/skills/wksp/launch.py --path '<RESOLVED_PATH>' --tool '<TOOL>' [--model '<MODEL>'] [--handoff]
```

Both tools accept `--model` for model selection. For the handoff prompt:
- **claude**: positional arg is the prompt — `claude --model <M> "enter handoff no ask"`
- **opencode**: positional arg is project path, use `--prompt` — `opencode --model <M> --prompt "enter handoff no ask"`

The script prints the generated shell command on stdout. Use this for the confirmation message.

### Step 6: Confirm

Print confirmation: which path was opened, which tool, which model, and whether handoff was enabled.
