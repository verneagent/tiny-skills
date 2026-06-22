---
name: nemo-restart
description: Restart a running Nemo daemon while preserving the coding-agent session context (codex thread / Claude SDK session). Use when the user says "restart nemo", "重启 nemo", "nemo 重启", "reload nemo", "resume nemo", or wants to pick up a Lark chat conversation after a code change / crash.
allowed-tools: Bash, Read
---

# nemo-restart

Restart an in-process Nemo daemon **without losing the coding agent's thread/session**.

As of the `deactivate` no-delete refactor, the DB `sessions` row survives clean shutdown, SIGKILL, and crash alike — the boot path's resume logic picks it up automatically. This skill just handles the one remaining edge: the **relay heartbeat TTL** after a SIGKILL can block workspace rediscovery for ~60s.

## Background

- `sdk_session_id` lives in `~/.nemo/projects/<hash>/nemo.db`, one row per chat.
- `db.deactivate` no longer deletes the row, so both SIGTERM and SIGKILL leave resume state intact.
- On boot, `agent.py` reads the row via `get_chat_owner` → `get_sdk_session_id` → `agent.start(resume=…)`. Logs confirm with `Cleaning stale session <uuid> (sdk=<prefix>)` and `Resuming SDK session <prefix>`.
- Liveness is NOT read from DB — it's the relay heartbeat + PID file + local process scan (`evict_existing` in `nemo/workspace.py`).

## The recipe

### 1. Identify target

```bash
CHAT_ID=oc_...                                        # from user or pid dir
PID=$(cat ~/.nemo/pids/$CHAT_ID.pid)
PROJECT_DIR=$(lsof -p $PID 2>/dev/null | awk '$4=="cwd"{print $NF}')
# `-ww` prevents argv truncation. `-o args=` truncates to terminal width
# and drops trailing flags like `--model deepseek-v4-pro[1m]`.
ORIGINAL_ARGS=$(ps -ww -p $PID -o command= | sed 's/.*nemo //')
```

If the user only says "restart nemo" without naming a chat, list `~/.nemo/pids/*.pid` and ask which one — don't guess.

**Sanity-check the args before reusing them.** A daemon launched on an old captain-nemo may have flags the current install dropped (e.g., `--base-url` / `--api-key-env` were folded into `--model <preset>` in 0.3.84). If a daemon you're restarting is older than the installed version, dry-run argparse first:

```bash
/Users/.../local/bin/nemo $ORIGINAL_ARGS --version 2>&1 | tail -3
```

`unrecognized arguments` → you must rewrite `$ORIGINAL_ARGS` before relaunching. Common migration: `--base-url <X> --api-key-env <Y> --model <remote_id>` → `--model <preset_name>`. **Beware**: in `ps`, the visible `--model` value of an old `--base-url`-style daemon is the *remote model id* (e.g., `deepseek-v4-pro[1m]`), NOT a preset name. Don't pass it to the new scheme verbatim — see step 6's preset-resolution check.

### 1.5. Pre-flight: is the daemon running stale code?

`pip install -e .` **is not a hot-reload** — it just puts the repo on `sys.path`. A running daemon holds in-memory bytecode from the files as they existed the moment it did `import nemo.*`. Source edits since then don't reach that process; only a restart will. There are also two separate staleness modes to check, because they decouple:

- **Source staleness** — the `.py` files on disk have been edited since the daemon started. The daemon is running *older* code than the source tree. Restart loads the new bytecode.
- **Metadata staleness** — `site-packages/captain_nemo-*.dist-info` was created by an earlier `pip install -e .` and never refreshed after version bumps. `importlib.metadata.version("captain-nemo")` returns the stale version number, so the start card / `--version` lies. The daemon's *code* can be correct (because the `.pth` injects the repo into `sys.path`) while the *label* is wrong.

Run this combined check (works on macOS and Linux — parses `ps lstart` via Python instead of shell-math tricks that break with `ps -o etime=`):

```bash
/opt/homebrew/opt/python@3.14/bin/python3.14 <<'PY'
from datetime import datetime
from importlib.metadata import version, PackageNotFoundError
import pathlib, subprocess, tomllib

pid = "$PID"  # substitute before running, or pass via env

# --- Source staleness ---
lstart = subprocess.check_output(
    ["ps", "-p", pid, "-o", "lstart="], text=True
).strip()
start = datetime.strptime(lstart, "%a %b %d %H:%M:%S %Y").timestamp()
import nemo
src = pathlib.Path(nemo.__file__).parent
newer = [p for p in src.rglob("*.py") if p.stat().st_mtime > start]
age = int(datetime.now().timestamp() - start)

print(f"daemon pid={pid} age={age}s")
if newer:
    print(f"  ⚠ SOURCE STALE — {len(newer)} files modified since start:")
    for p in newer[:5]:
        print(f"    - {p.relative_to(src)}")
else:
    print("  ✓ source up to date")

# --- Metadata staleness ---
# Compare installed dist-info version vs pyproject.toml in the editable repo.
repo = src.parent
pyproject = repo / "pyproject.toml"
if pyproject.is_file():
    with pyproject.open("rb") as f:
        pyproject_version = tomllib.load(f)["project"]["version"]
    try:
        installed_version = version("captain-nemo")
    except PackageNotFoundError:
        installed_version = "(not installed)"
    if installed_version != pyproject_version:
        print(f"  ⚠ METADATA STALE — site-packages says {installed_version}, "
              f"pyproject says {pyproject_version}")
        print(f"    fix: {repo}/; pip install -e . --break-system-packages")
    else:
        print(f"  ✓ metadata matches pyproject: {installed_version}")
PY
```

Interpretation:

| Source | Metadata | Action |
|---|---|---|
| Fresh | Fresh | Nothing to do from a code standpoint — restart only if runtime state is wedged. |
| Stale | Fresh | Restart. New daemon picks up new `.py`. |
| Fresh | Stale | No restart needed for behavior, but **reinstall metadata** (`pip install -e . --break-system-packages`) so the next start card shows the right version. Active daemon's in-memory `__version__` remains stale until its own restart. |
| Stale | Stale | Reinstall metadata first, **then** restart — otherwise the new daemon will also import the stale dist-info and keep lying about its version. |

#### Sub-gotcha: legacy editable artifacts shadow the new install

After running `pip install -e . --break-system-packages`, the new daemon may still die at startup with:

```
ImportError: cannot import name '__version__' from 'nemo' (unknown location)
```

The "(unknown location)" hint means Python found `nemo` as a **namespace package** — a directory with no `__init__.py` — instead of the editable install. Trigger:

- captain-nemo used to be packaged as `nemo` (pre-rename). An old `pip install -e .` from that era wrote `__editable__.nemo-0.1.0.pth` and a real `site-packages/nemo/codex_sidecar/` subdir
- `pip uninstall captain-nemo` doesn't touch that legacy install (different package name)
- When the daemon's cwd ≠ source repo, the `site-packages/nemo/` directory wins resolution as a namespace package; the editable `.pth` finder is shadowed

Reproduction:

```bash
cd <some_dir_that_isnt_the_nemo_source_repo>
python3 -c "import nemo; print(nemo.__file__)"
# If this prints `None` (namespace package), you have the bug
```

Fix:

```bash
rm -rf /opt/homebrew/lib/python3.14/site-packages/nemo
rm -f  /opt/homebrew/lib/python3.14/site-packages/__editable__.nemo-0.1.0.pth
rm -f  /opt/homebrew/lib/python3.14/site-packages/__editable___nemo_0_1_0_finder.py
```

Then re-verify import resolves to the source `__init__.py`. Only relevant on machines that had captain-nemo installed before the rename — newer hosts won't have these files.

After the restart succeeds (step 6), sanity-check that the new PID actually has the new code. A fresh import is sufficient evidence since the new daemon is reached through the same `sys.path`:

```bash
/opt/homebrew/opt/python@3.14/bin/python3.14 -c "
import inspect
from nemo import codex_agent
for line in inspect.getsource(codex_agent.CodexCodingAgent.run_turn).splitlines():
    if 'limit=' in line:
        print(line.strip())
"
```

Swap the grep pattern to whatever signature line is specific to the fix you just shipped.

### 2. Stop the daemon

```bash
kill $PID          # SIGTERM — clean shutdown, row preserved (fixed daemon only)
# or
kill -9 $PID       # SIGKILL — always safe; the pre-flight-stale path must use this
```

Rule of thumb based on step 1.5:

- **Pre-flight says "up to date"** → prefer `kill` (SIGTERM). The `deactivate` no-delete fix (≥ 0.3.70) preserves the resume row and graceful shutdown also releases the relay heartbeat / workspace claim.
- **Pre-flight says "stale"** → use `kill -9` (SIGKILL). A pre-0.3.70 daemon still DELETEs the sessions row on clean shutdown, which wipes `sdk_session_id`. SIGKILL skips `deactivate` entirely and the row survives.

### 3. If SIGKILL was used, release the relay heartbeat

SIGTERM runs `channel.release_workspace()` which also clears the relay heartbeat. SIGKILL skips it, so the chat looks "occupied" for ~60s and `nemo`'s workspace discovery will create a new orphan group instead of reusing this one:

```bash
/opt/homebrew/opt/python@3.14/bin/python3.14 -c "
from nemo import relay
relay.release_heartbeat('$CHAT_ID')
print('is_alive:', relay.is_alive('$CHAT_ID'))
"
```

Expect `is_alive: False`. Skip this whole step if you used plain `kill`.

### 4. Clean the stale PID file (only after SIGKILL)

```bash
rm -f ~/.nemo/pids/$CHAT_ID.pid
```

### 5. Relaunch, pinned to the same chat

Always pass `--chat-id` to skip workspace discovery and guarantee the daemon lands on the intended chat. Reuse `$ORIGINAL_ARGS` so provider / model / effort match. Detach with `nohup ... & disown` like the `nemo` skill:

```bash
cd "$PROJECT_DIR" && nohup /opt/homebrew/bin/nemo \
  --chat-id "$CHAT_ID" \
  $ORIGINAL_ARGS \
  </dev/null >/tmp/nemo-restart.out 2>&1 &
disown
NEW_PID=$!
```

### 6. Verify resume + preset + WS

```bash
sleep 3
tail -30 ~/.nemo/logs/nemo-$NEW_PID.log
```

Required lines (resume case — sessions row had a prior id):

- `Cleaning stale session <uuid> (sdk[<provider>]=<prefix>)` — old row found
- `Resuming SDK session <prefix>` — resume id handed to the agent

If either is missing, resume did NOT happen. Do not declare success.

Required line **when `--model <preset>` was passed**:

- `Resolved preset <name> → endpoint=<url> model=<remote_id>`

**Missing this line is silent corruption**: the SDK is sending the literal string you passed (e.g., `deepseek-v4-pro[1m]`) to the default Anthropic endpoint as a model id. Turns complete with `cost=0.0000`, the chat looks alive, but every reply is `There's an issue with the selected model (...). It may not exist or you may not have access to it.` `--model` accepts the **preset name** (e.g., `deepseek-v4-pro`), not the remote id (e.g., `deepseek-v4-pro[1m]`). Inspect available presets: `python -c "from nemo.presets import load_presets; print(list(load_presets()))"`.

Required line for relay-mode daemons (most deployments):

- `WS connected to relay`

If the log loops `WS error, reconnecting in 3s: did not receive a valid HTTP response from proxy` instead, the host has `HTTP_PROXY` / `HTTPS_PROXY` / `ALL_PROXY` set (e.g., ClashX) and the daemon is on captain-nemo `<= 0.3.98`. Upgrade to `>= 0.3.99` (which passes `proxy=None` to `websockets.connect`).

## Orphan cleanup

If a prior failed restart created a new group, its PID file is still in `~/.nemo/pids/` and its relay heartbeat may still be live:

```bash
rm -f ~/.nemo/pids/<orphan_chat_id>.pid
/opt/homebrew/opt/python@3.14/bin/python3.14 -c "
from nemo import relay; relay.release_heartbeat('<orphan_chat_id>')"
```

Dissolving the orphan Lark group itself is a manual step — it requires bot permissions and is usually not worth automating.

## Bulk restart (rolling out a new version)

When deploying a fix that affects every daemon (e.g. the 0.3.99 WS proxy fix), do it in one batch instead of one-by-one:

1. **Snapshot every PID file's args** to `/tmp/nemo-restart-snap/before.txt`, one line per chat: `chat|pid|cwd|args`. Use `ps -ww -p $pid -o command=` (not `-o args=`).
2. **SIGTERM all**, sleep 8s, then `kill -9` stragglers. SIGKILL is safe — `deactivate`-no-delete (≥ 0.3.70) preserves session rows. Most daemons in the middle of a turn will need SIGKILL; that's fine.
3. **Loop over the snapshot to relaunch.** Always re-add `--chat-id $chat` even if the original args didn't have it — without it, the new daemon does workspace discovery and may land on the wrong chat (or claim a fresh one).
4. **Verify each new daemon** against step 6: alive, PID file matches, `WS connected`, and `Resolved preset` if a preset was passed. **WS-connected without preset-resolved looks alive but every reply is a "model not found" error** — easy to miss without checking the preset line.
5. **If some daemons fail to start** with no log file written, suspect args incompatibility. Run `nemo $ORIGINAL_ARGS --version` from the snapshot to see which flags the new captain-nemo no longer accepts, rewrite, retry just those.

## Reporting back

Tell the user:
- Old PID → New PID
- `sdk_session_id` prefix that was resumed (from the log line)
- Chat ID
- Whether the "Resuming SDK session" log line was observed
- Whether `Resolved preset` appeared (when `--model <preset>` was passed)
- Whether `WS connected to relay` appeared

Do **not** report "restarted" without confirming step 6.
