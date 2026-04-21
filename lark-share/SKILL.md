---
name: lark-share
description: Share a knowledge insight or message with a team via Lark group chat webhook. Use when the user says "share", "lark-share", or wants to send a formatted message to a Lark group.
allowed-tools: Bash, Read, Write, Agent
---

# lark-share

Send a formatted knowledge-sharing card to a Lark group chat via custom bot webhook.

## Skill Path

```bash
LARK_SHARE_SCRIPTS=$(python3 -c "import os; p='.claude/skills/lark-share/scripts'; print(os.path.abspath(p) if os.path.isdir(p) else os.path.expanduser('~/.agents/skills/lark-share/scripts'))")
```

## Config

`~/.lark-share/config.json`:

```json
{
  "webhook_token": "354e0595-...",
  "language": "zh",
  "signing_secret": ""
}
```

- `webhook_token` — The Lark custom bot webhook token (the path segment after `/hook/`)
- `language` — Content language: `zh` (Chinese) or `en` (English). Default `zh`.
- `signing_secret` — Optional HMAC signing secret. If empty, uses the webhook_token for signing (Lark's default behavior).

If the config file doesn't exist, run the init flow.

## Init

If `~/.lark-share/config.json` doesn't exist:

1. Ask the user for their Lark webhook URL or token.
   - If they paste a full URL like `https://open.larksuite.com/open-apis/bot/v2/hook/xxx`, extract the token.
   - If they paste just the token, use it directly.
2. Ask for content language preference (`zh` or `en`, default `zh`).
3. Ask for signing secret (optional, press Enter to skip — will use webhook_token).
4. Create the config file.

## Usage

`/lark-share [subject]`

- If a subject is provided, use it as the topic.
- If no subject is provided, ask the user what topic they want to share.

## Workflow

### Step 1: Research and Draft

1. Research the subject — use web search, codebase context, or your own knowledge as appropriate.
2. Draft a CommonMark markdown message (Card v2). Structure it as:
   - A brief intro (1–2 sentences on why this matters)
   - Key points or tips (use bold, bullet lists, code snippets as needed)
   - A practical example or takeaway

**Style rules:**
- Keep the message concise but informative — aim for 5–15 lines of markdown.
- Focus on practical, actionable insights the team can use immediately.
- Use Card v2 markdown syntax (CommonMark with Lark extensions).
- **Title style**: Don't use boring titles like "详解" or "Guide". Use attention-grabbing titles — pose a question, highlight a benefit or pain point. Add emoji to make titles pop. Examples: "🤔 你想减少 84% 的权限弹窗吗？", "😤 Git push 老报错？可能是 sandbox 的锅", "⚡ 一个配置让 Claude 自动执行命令".
- **Body must not repeat title**: The card header already shows the title. Start the body directly with the intro.
- **Language**: Follow the `language` config. If `zh`, all content must be in Chinese (even if the user describes the topic in English). If `en`, use English.

**Card v2 markdown syntax (CommonMark + Lark extensions):**
- Bold: `**text**`
- Italic: `*text*`
- Strikethrough: `~~text~~`
- Headings: `# H1` through `###### H6`
- Ordered list: `1. item` (4 spaces for nesting)
- Unordered list: `- item` (4 spaces for nesting)
- Code block: ` ```language\ncode\n``` ` (supports 60+ languages)
- Inline code: `` `code` ``
- Links: `[text](url)`
- Blockquote: `> quoted text`
- Horizontal rule: `---`
- Table: standard markdown table syntax (max 5 data rows per page)
- Colored text: `<font color='red'>text</font>` (supports color names and RGBA)
- Mentions: `<at id=all>everyone</at>`
- Line breaks: `\n`

### Step 2: Preview and Confirm

**NEVER skip the preview step, even if the user's intent seems clear.** Always present the draft and wait for explicit confirmation before sending.

Present the drafted message to the user:

```
=== Message Preview ===
Title: <title>
Color: <color>

<the formatted content>
```

**Preview formatting rule:** The preview MUST display actual rendered line breaks (real markdown), NOT literal `\n` escape sequences. The `\n` sequences are only used in the final bash command argument to the send script.

Ask the user: **Send**, **Edit** (user provides corrections), **Cancel**

- If **Edit**: apply the user's changes and preview again.
- If **Cancel**: stop without sending.

### Step 3: Send

```bash
python3 $LARK_SHARE_SCRIPTS/lark_webhook.py "<message>" --title "<title>" --color blue
```

The script reads the webhook token from config automatically.

Optional flags:
- `--image <path>` — Attach an image (can be used multiple times). Uses `~/.lark-suite/config.json` credentials for upload.

To control where images appear in the card, insert `---IMG---` as a marker in the message text. The image will be placed at that position as a standalone `img` element between two markdown sections. If no marker is present, images are appended at the end.

Report the result to the user.

## Examples

```
/lark-share prompt engineering best practices
/lark-share how to use Claude Code effectively
/lark-share cursor vs claude code
/lark-share
```
