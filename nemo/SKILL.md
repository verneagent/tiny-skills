---
name: nemo
description: Start a Nemo (Lark-connected coding agent) daemon on a directory. Use when the user says "run nemo", "start nemo", "启动 nemo", or "在...运行 nemo".
allowed-tools: Bash
---

# nemo

Start a Nemo agent on a project directory and connect it to a Lark group.

Nemo runs in the **foreground** — this skill detaches it via `setsid nohup` so
it survives after the Bash tool call returns. Do **not** rely on nemo
self-daemonizing; it used to, but the env marker it set (`NEMO_FOREGROUND=1`)
leaked into subprocess env and made nested launches die silently.

## Usage

`/nemo [path]` — Start nemo on the given directory (default: `$PWD`).

## Workflow

1. **Resolve the target directory.**
   - If `<path>` is provided, expand `~` and use it.
   - Otherwise use `$PWD`.
   - Verify it exists. If not, tell the user and stop.

2. **Check if nemo is already running** for that directory:
   ```bash
   pgrep -f "nemo.*--project-dir $DIR" >/dev/null && echo RUNNING || echo FREE
   ```
   If `RUNNING`, tell the user (with the pid) and stop.

3. **Launch nemo detached** (the critical part — every piece matters):
   ```bash
   setsid nohup ~/.local/bin/nemo --project-dir "$DIR" --verbose \
     </dev/null >/dev/null 2>&1 &
   disown
   ```
   - `setsid` — new session so a pgroup kill at tool-end can't reach it.
   - `nohup` — ignore SIGHUP.
   - `</dev/null >/dev/null 2>&1` — fully detach the tty/pipe fds; otherwise
     a later write from nemo hits a closed pipe when the Bash tool exits.
   - `&` + `disown` — background and drop from the shell's job table.

   This command writes outside the project dir (PID file, DB, WebSocket),
   so the tool call needs `dangerouslyDisableSandbox: true`.

4. **Wait ~5 seconds** then verify by reading the log:
   ```bash
   sleep 5
   pid=$(pgrep -fn "nemo.*--project-dir $DIR")
   tail -30 ~/.nemo/logs/nemo-$pid.log
   ```
   Look for:
   - `Claimed group` / `Wrote PID file` — workspace assigned
   - `Start card sent` — Lark group greeted
   - `SDK client connected` — coding agent ready

5. **Report** to the user:
   - Directory
   - Chat id (from `Using chat:` / `Claimed group` log line)
   - PID
   - Whether startup looks healthy

## Options to pass through verbatim

| Flag | Purpose |
|------|---------|
| `--chat-name <name>` | Connect to an existing Lark group by name substring |
| `--chat-id <id>` | Connect to a specific Lark group by ID |
| `--profile <name>` | Config profile (default: `default`) |
| `--model <name>` | Override the model |

Do not pass `--foreground` — the flag was removed. Nemo always runs in
the foreground, and the `setsid nohup ... &` wrapper above is what
handles detachment.
