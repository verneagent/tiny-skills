---
name: nemo
description: Start a Nemo (Lark-connected coding agent) daemon on a directory. Use when the user says "run nemo", "start nemo", "启动 nemo", or "在...运行 nemo".
allowed-tools: Bash
---

# nemo

Start a Nemo agent and connect it to a Lark group.

Nemo runs in the **foreground** — this skill detaches it via `nohup ... & disown`
so it survives after the Bash tool call returns. Do **not** rely on nemo
self-daemonizing; it used to, but the env marker it set (`NEMO_FOREGROUND=1`)
leaked into subprocess env and made nested launches die silently.

## Usage

`/nemo [args...]` — forward `args...` to `nemo`. With no args, nemo uses
the current working directory and auto-discovers / creates a Lark group.

## Workflow

1. **Launch nemo detached.** This is the entire launch command — every
   piece matters:
   ```bash
   nohup ~/.local/bin/nemo --verbose <USER_ARGS> \
     </dev/null >/dev/null 2>&1 &
   pid=$!
   disown
   ```
   - `nohup` — ignore SIGHUP so the child survives shell / tool teardown.
   - `</dev/null >/dev/null 2>&1` — fully detach the tty/pipe fds; otherwise
     a later write from nemo hits a closed pipe when the Bash tool exits.
   - `&` + `disown` — background, drop from the shell's job table, and let
     the shell exit cleanly so the child gets reparented to PID 1.
   - Capture `$!` immediately — do not `pgrep` for the pid afterwards,
     because multiple nemos may legitimately share the same `--project-dir`
     as long as they bind different Lark groups.

   Pass user args through **verbatim**. Do not pre-resolve the target
   directory, expand `~`, or check `[[ -d ]]` — nemo defaults
   `--project-dir` to the current working directory and validates the
   path itself. `cd` into the target dir first if the user specified
   one, or pass `--project-dir <path>` through.

   macOS does not ship `setsid`. The `nohup + disown` combo is enough.

   This command writes outside the project dir (PID file, DB, WebSocket),
   so the tool call needs `dangerouslyDisableSandbox: true`.

   **Launching on a remote host via ssh.** Wrap the same launch command in
   a single-quoted remote string, escape `$!` so the remote shell expands
   it, and pass `--project-dir` explicitly (the remote cwd isn't what the
   user means):
   ```bash
   ssh -i <key> <user>@<host> "nohup ~/.local/bin/nemo --verbose <USER_ARGS> \
     --project-dir <ABS_REMOTE_PATH> \
     </dev/null >/dev/null 2>&1 & disown; echo pid=\$!"
   ```
   Notes:
   - `</dev/null >/dev/null 2>&1` is **required** — without it ssh hangs
     waiting for the detached child's stdout/stderr to close.
   - `disown` goes after `&` on the same line (remote shell is
     non-interactive; semicolon form is safest).
   - Capture the PID from the `echo pid=…` line, then check the log
     with a second `ssh ... "tail ~/.nemo/logs/nemo-<pid>.log"` —
     don't chain `sleep && tail` into the same ssh call, it sometimes
     wedges. Run as two separate ssh calls.
   - Do **not** `cd` before the command; pass `--project-dir` instead.
     `cd` is relative to the remote user's home, which rarely matches
     intent and silently resolves to the wrong project.

2. **Wait ~5 seconds** then verify via the log:
   ```bash
   sleep 5
   tail -30 ~/.nemo/logs/nemo-$pid.log
   ```
   Look for:
   - `Claimed group` / `Wrote PID file` — workspace assigned
   - `Start card sent` — Lark group greeted
   - `SDK client connected` — coding agent ready

3. **Report** to the user:
   - Project directory (from `Looking for workspace tag:` log line)
   - Chat id (from `Using chat:` / `Claimed group` log line)
   - PID
   - Whether startup looks healthy

## Flags the user may want passed through

| Flag | Purpose |
|------|---------|
| `--project-dir <path>` | Project directory (default: cwd) |
| `--chat-name <name>` | Connect to an existing Lark group by name substring |
| `--chat-id <id>` | Connect to a specific Lark group by ID |
| `--profile <name>` | Config profile (default: `default`) |
| `--model <name>` | Override the model |

Do not pass `--foreground` — the flag was removed. Nemo always runs in
the foreground, and the `nohup ... & disown` wrapper above is what
handles detachment.
