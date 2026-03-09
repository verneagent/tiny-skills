---
name: multi-gh
description: Fix and standardize GitHub multi-account workflows with gh account switching, SSH host aliases, and safe remote setup. Use when creating repos, pushing code, or diagnosing GitHub auth mismatches across multiple identities.
---

# GitHub Multi-Account SSH

Use this skill when the user works with multiple GitHub identities and any of these happen:

- `gh repo create` targets the wrong owner
- `git push` fails with `Permission denied (publickey)`
- the repository remote uses `github.com` but the machine is configured with SSH host aliases like `dinghao.github.com`
- `gh` is authenticated as one account while `git` or SSH is effectively using another

## Goal

Make GitHub ownership, CLI auth, git author identity, and SSH transport line up cleanly.

## Quick Workflow

1. Check current GitHub CLI identity.
2. Check current git remote.
3. Check current SSH auth path.
4. Decide whether to use `github.com` or a configured host alias.
5. Fix local repo config only, not global config, unless the user explicitly asks.

## Step 1: Check CLI Identity

Run:

```bash
gh auth status
gh api user
```

If the active `gh` identity is wrong for the target owner, switch it:

```bash
gh auth switch -u <username>
```

Do this before `gh repo create`, `gh repo view`, or any owner-specific GitHub action.

## Step 2: Check Git Remote

Run:

```bash
git remote -v
```

Look for one of these patterns:

- Standard host:
  - `git@github.com:<owner>/<repo>.git`
  - `https://github.com/<owner>/<repo>.git`
- Alias host:
  - `git@dinghao.github.com:<owner>/<repo>.git`

If the machine is already configured with SSH aliases, prefer the alias host instead of generic `github.com`.

## Step 3: Check SSH Setup

Run:

```bash
ls -la ~/.ssh
ssh-add -l
sed -n '1,220p' ~/.ssh/config
```

Interpretation:

- If `ssh-add -l` says `The agent has no identities`, agent-based auth is not active.
- If `~/.ssh/config` defines `Host alice.github.com` with `IdentityFile ~/.ssh/alice`, then remotes for that identity should use `git@alice.github.com:<owner>/<repo>.git`.
- If there is no `Host github.com` entry, generic `git@github.com` may fail even when alias-based SSH works.

## Step 4: Test The Correct Host

Never assume the failing host and the working host are the same.

Test exactly what the remote should use:

```bash
ssh -T git@github.com
ssh -T git@alice.github.com
```

Expected success output:

```text
Hi <username>! You've successfully authenticated, but GitHub does not provide shell access.
```

## Step 5: Fix The Remote

If the user already has an alias host configured, set the remote to match it:

```bash
git remote set-url origin git@dinghao.github.com:<owner>/<repo>.git
```

If alias SSH is unavailable but `gh` works, HTTPS is a valid temporary fallback:

```bash
git remote set-url origin https://github.com/<owner>/<repo>.git
```

After any temporary HTTPS fallback used only for bootstrapping, switch back to the intended SSH remote if the user prefers SSH.

## Step 6: Fix Commit Identity Safely

Check current git author identity:

```bash
git config --get user.name
git config --get user.email
```

If it does not match the intended owner, set repo-local config only:

```bash
git config user.name <username>
git config user.email <noreply-or-approved-email>
```

Do not change global git identity unless explicitly requested.

## Common Failure Patterns

### `gh repo create` says the active account cannot create a repo for the owner

Cause:

- `gh` is authenticated as the wrong account

Fix:

```bash
gh auth switch -u <owner>
```

### `git push` over SSH fails but `gh repo view` works

Cause:

- GitHub CLI auth is fine, but SSH host/key selection is wrong

Fix:

- inspect `~/.ssh/config`
- switch remote to the correct alias host
- test with `ssh -T` against that exact alias

### First push works only over HTTPS

Cause:

- SSH path is misconfigured or unavailable in the current environment

Fix:

- use HTTPS only as a bootstrap fallback
- then restore the SSH remote once the correct alias host is verified

## Preferred Outcome

For each repo, the following should be true:

- `gh` active account matches the intended GitHub owner
- repo-local git author identity matches the intended owner
- `origin` uses the correct SSH alias host for that owner
- `ssh -T` succeeds for that exact alias host

## Example

If `~/.ssh/config` contains:

```sshconfig
Host alice.github.com
    Hostname ssh.github.com
    Port 443
    User git
    IdentitiesOnly yes
    IdentityFile ~/.ssh/alice
```

Then the correct remote form is:

```bash
git remote set-url origin git@alice.github.com:alice/<repo>.git
```

And the correct auth test is:

```bash
ssh -T git@alice.github.com
```
