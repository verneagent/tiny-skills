---
name: open-file
description: Open a local file or directory with a specified application on macOS. Use when the user asks to open, launch, or view a file in a specific app — e.g., "open this in Obsidian", "open in VS Code", "show me the PDF in Preview", "open the folder in Finder".
allowed-tools: Bash
---

# Open File

Open a local file or directory on macOS using `open`. Supports specifying an app, URL scheme deep linking, and error recovery.

## Usage

`/open-file <path> [app]`

- If no path is provided, infer from conversation context (e.g., a file just created or discussed).
- If an app is mentioned (e.g., "in Obsidian"), use `open -a` or the app's URL scheme.

## Workflow

1. **Resolve the path.** Make it absolute. If relative, resolve against cwd.

2. **Verify the target exists:**
   ```bash
   [ -e '<path>' ] && echo "EXISTS" || echo "NOT_FOUND"
   ```
   If not found, tell the user and stop.

3. **Open:**

   **With a specific app:**
   ```bash
   open -a '<App Name>' '<path>'
   ```

   **With the default app:**
   ```bash
   open '<path>'
   ```

4. **Handle `procNotFound` error.** If `open` fails because the app isn't running:
   ```bash
   open -a '<App Name>' && sleep 3 && open -a '<App Name>' '<path>'
   ```
   Launch the app first, wait for it to initialize, then retry.

5. **Confirm** to the user that the file was opened.

## URL Scheme Deep Linking

Use URL schemes when the user wants to jump to a specific item within an app, not just open a file.

| App | Command |
|-----|---------|
| Obsidian | `open -a "Obsidian" && sleep 3 && open 'obsidian://open?vault=<vault>&file=<url-encoded-path>'` |
| VS Code | `code '<path>'` or `open 'vscode://file/<absolute-path>'` |

URL-encode path components — especially emoji, CJK characters, and spaces.

## Notes

- Always single-quote paths to handle spaces and special characters
- `open '<directory>'` opens in Finder
- `open -a` both launches the app (if needed) and opens the file in one step — the two-step launch-then-open is only needed for URL scheme calls where the app must be running first
