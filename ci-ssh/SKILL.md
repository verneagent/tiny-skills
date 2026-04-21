---
name: ci-ssh
description: SSH connection details and utilities for CI machines (NeoJenkins). Use when the user needs to SSH into CI, connect to the build server, run commands on the Jenkins machine, or sync Claude credentials between SSH and local config dirs on CI (after `claude login` over SSH). Subcommands — cpcred (sync fresh credentials from ~/.claude-remote to ~/.claude and restore the symlink so nemo/SDK daemons don't 401).
---

# ci-ssh

SSH connection info for CI machines is maintained in the Obsidian note:

**`~/Library/Mobile Documents/iCloud~md~obsidian/Documents/MarkNote/🚧 Projects/FiveD/NeoJenkins SSH.md`**

Read that file for up-to-date connection details (IP, username, key path, GitHub SSH alias, etc.).

## Subcommands

### `cpcred` — sync credentials after SSH `claude login`

**Problem.** `~/.zshrc` on CI sets `CLAUDE_CONFIG_DIR=~/.claude-remote` for SSH sessions to keep them out of the local daemons' state. But:

- SDK-based daemons (nemo, bug pipeline) default to `~/.claude/.credentials.json`
- `claude login` over SSH writes to `~/.claude-remote/.credentials.json`
- A fresh login **invalidates the old refresh token** in `~/.claude/.credentials.json` → daemons 401 on next refresh

**Steady state.** `~/.claude-remote/.credentials.json` is a **symlink** to `~/.claude/.credentials.json` so daemons and SSH sessions share one token file. Daemon-side token refreshes then propagate to the SSH side automatically.

**Why you still need this command.** `claude login` doesn't follow symlinks — it `unlink`s the target and writes a new real file. After every SSH `claude login`, the symlink is gone and the two files diverge again.

**After any SSH `claude login`, run:**

```bash
ssh neojenkins-relay 'cp -p ~/.claude-remote/.credentials.json ~/.claude/.credentials.json \
  && rm ~/.claude-remote/.credentials.json \
  && ln -s ~/.claude/.credentials.json ~/.claude-remote/.credentials.json \
  && ls -la ~/.claude/.credentials.json ~/.claude-remote/.credentials.json'
```

Steps:
1. Copy the freshly-logged-in creds from `~/.claude-remote/` to `~/.claude/` (preserves 0600 + mtime)
2. Delete the now-stale real file at `~/.claude-remote/.credentials.json`
3. Recreate the symlink `~/.claude-remote/.credentials.json → ~/.claude/.credentials.json`
4. Verify: `ls -la` should show the remote path as `lrwxr-xr-x` pointing to the real file

Daemons don't need to restart — they pick up the new token on the next refresh.
