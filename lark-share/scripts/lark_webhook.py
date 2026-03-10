#!/usr/bin/env python3
"""Send a message to a Lark group chat via custom bot webhook.

Reads webhook token from ~/.lark-share/config.json.
Supports optional HMAC signing and image upload (requires handoff skill).
"""

import argparse
import base64
import hashlib
import hmac
import json
import os
import re
import sys
import time
import urllib.request
import urllib.error

WEBHOOK_BASE = "https://open.larksuite.com/open-apis/bot/v2/hook/"
CONFIG_PATH = os.path.expanduser("~/.lark-share/config.json")

# --- Config ---


def load_config():
    """Load config from ~/.lark-share/config.json."""
    if not os.path.exists(CONFIG_PATH):
        print(f"Error: Config not found at {CONFIG_PATH}", file=sys.stderr)
        print("Run /lark-share to set up.", file=sys.stderr)
        sys.exit(1)
    with open(CONFIG_PATH) as f:
        return json.load(f)


# --- Markdown helpers ---

_MARKDOWN_ESCAPE_SUBREGEX = "|".join(
    r"\{0}(?=([\s\S]*((?<!\{0})\{0})))".format(c) for c in ("*", "`", "_", "~", "|")
)
_MARKDOWN_ESCAPE_COMMON = r"^>(?:>>)?\s|\[.+\]\(.+\)"
_MARKDOWN_ESCAPE_REGEX = re.compile(
    r"(?P<markdown>%s|%s)" % (_MARKDOWN_ESCAPE_SUBREGEX, _MARKDOWN_ESCAPE_COMMON)
)


def escape_markdown(text, *, as_needed=False, ignore_links=True):
    if not as_needed:
        url_regex = r"(?P<url><[^: >]+:\/[^ >]+>|(?:https?|steam):\/\/[^\s<]+[^<.,:;\"\'\]\s])"

        def replacement(match):
            groupdict = match.groupdict()
            is_url = groupdict.get("url")
            if is_url:
                return is_url
            return "\\" + groupdict["markdown"]

        regex = r"(?P<markdown>[_\\~|\*`]|%s)" % _MARKDOWN_ESCAPE_COMMON
        if ignore_links:
            regex = "(?:%s|%s)" % (url_regex, regex)
        return re.sub(regex, replacement, text)
    else:
        text = re.sub(r"\\", r"\\\\", text)
        return _MARKDOWN_ESCAPE_REGEX.sub(r"\\\1", text)


def md_element(content):
    return {
        "tag": "div",
        "text": {
            "content": content,
            "tag": "lark_md",
        },
    }


def img_element(image_key, alt="image"):
    return {
        "tag": "img",
        "img_key": image_key,
        "alt": {"tag": "plain_text", "content": alt},
    }


def upload_images(image_paths):
    """Upload images via handoff's lark_im. Returns image_keys or empty list on failure."""
    try:
        handoff_dir = None
        candidates = [
            os.path.join(os.getcwd(), ".claude/skills/handoff/scripts"),
            os.path.expanduser("~/.agents/skills/handoff/scripts"),
        ]
        for p in candidates:
            if os.path.isdir(p):
                handoff_dir = p
                break
        if not handoff_dir:
            print(
                "Warning: handoff skill not found, skipping image upload",
                file=sys.stderr,
            )
            return []

        sys.path.insert(0, handoff_dir)
        from handoff_config import load_credentials
        from lark_im import get_tenant_token, upload_image

        creds = load_credentials()
        token = get_tenant_token(creds["app_id"], creds["app_secret"])
        keys = []
        for path in image_paths:
            key = upload_image(token, path)
            keys.append(key)
        return keys
    except Exception as e:
        print(f"Warning: image upload failed: {e}", file=sys.stderr)
        return []


# --- Signing ---


def compute_sign(timestamp, secret):
    string_to_sign = f"{timestamp}\n{secret}"
    hmac_code = hmac.new(
        string_to_sign.encode("utf-8"), digestmod=hashlib.sha256
    ).digest()
    return base64.b64encode(hmac_code).decode("utf-8")


# --- Send ---


def send_to_lark(color, title, elements, webhook_token, signing_secret=None):
    secret = signing_secret or webhook_token
    timestamp = str(int(time.time()))
    sign = compute_sign(timestamp, secret)

    payload = {
        "timestamp": timestamp,
        "sign": sign,
        "msg_type": "interactive",
        "card": {
            "config": {
                "wide_screen_mode": True,
                "enable_forward": True,
            },
            "elements": elements,
            "header": {
                "title": {
                    "content": title,
                    "tag": "lark_md",
                },
                "template": color,
            },
        },
    }

    req = urllib.request.Request(
        WEBHOOK_BASE + webhook_token,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )

    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        return json.loads(e.read().decode())


def main():
    parser = argparse.ArgumentParser(description="Send a message to Lark via webhook")
    parser.add_argument("message", help="Message content (supports lark_md)")
    parser.add_argument("--title", default="Notification", help="Card title")
    parser.add_argument(
        "--color",
        default="blue",
        choices=["blue", "red", "orange", "green", "purple", "indigo", "grey"],
        help="Card header color (default: blue)",
    )
    parser.add_argument(
        "--image",
        action="append",
        dest="images",
        help="Image file path to attach (can be specified multiple times)",
    )
    args = parser.parse_args()

    config = load_config()
    webhook_token = config["webhook_token"]
    signing_secret = config.get("signing_secret") or None

    message = args.message.replace("\\n", "\n")
    elements = [md_element(message)]

    if args.images:
        image_keys = upload_images(args.images)
        for i, key in enumerate(image_keys):
            elements.append(img_element(key, alt=f"image {i + 1}"))

    result = send_to_lark(args.color, args.title, elements, webhook_token, signing_secret)

    if result.get("code") == 0:
        print("Message sent successfully.")
    else:
        print(f"Failed to send message: {result}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
