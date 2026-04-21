#!/usr/bin/env python3
"""Send a Card v2 message to a Lark group chat via custom bot webhook.

Reads webhook token from ~/.lark-share/config.json.
Supports optional HMAC signing and image upload (via lark-suite credentials).
"""

import argparse
import base64
import hashlib
import hmac
import json
import os
import sys
import time
import urllib.request
import urllib.error

WEBHOOK_BASE = "https://open.larksuite.com/open-apis/bot/v2/hook/"
CONFIG_PATH = os.path.expanduser("~/.lark-share/config.json")
LARK_SUITE_CONFIG = os.path.expanduser("~/.lark-suite/config.json")


# --- Config ---


def load_config():
    """Load config from ~/.lark-share/config.json."""
    if not os.path.exists(CONFIG_PATH):
        print(f"Error: Config not found at {CONFIG_PATH}", file=sys.stderr)
        print("Run /lark-share to set up.", file=sys.stderr)
        sys.exit(1)
    with open(CONFIG_PATH) as f:
        return json.load(f)


# --- Image upload ---


def get_tenant_token(app_id, app_secret):
    """Get tenant access token from Lark API."""
    url = "https://open.larksuite.com/open-apis/auth/v3/tenant_access_token/internal"
    data = json.dumps({"app_id": app_id, "app_secret": app_secret}).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as resp:
        result = json.loads(resp.read().decode())
    if result.get("code") != 0:
        raise RuntimeError(f"Failed to get token: {result}")
    return result["tenant_access_token"]


def upload_image(token, image_path):
    """Upload an image to Lark and return the image_key."""
    url = "https://open.larksuite.com/open-apis/im/v1/images"
    boundary = f"----WebKitFormBoundary{int(time.time() * 1000)}"

    with open(image_path, "rb") as f:
        image_data = f.read()

    filename = os.path.basename(image_path)
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="image_type"\r\n\r\n'
        f"message\r\n"
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="image"; filename="{filename}"\r\n'
        f"Content-Type: application/octet-stream\r\n\r\n"
    ).encode() + image_data + f"\r\n--{boundary}--\r\n".encode()

    req = urllib.request.Request(url, data=body, headers={
        "Content-Type": f"multipart/form-data; boundary={boundary}",
        "Authorization": f"Bearer {token}",
    })
    with urllib.request.urlopen(req) as resp:
        result = json.loads(resp.read().decode())
    if result.get("code") != 0:
        raise RuntimeError(f"Image upload failed: {result}")
    return result["data"]["image_key"]


def upload_images(image_paths):
    """Upload images via lark-suite credentials. Returns image_keys."""
    if not os.path.exists(LARK_SUITE_CONFIG):
        print("Warning: ~/.lark-suite/config.json not found, skipping image upload", file=sys.stderr)
        return []
    try:
        with open(LARK_SUITE_CONFIG) as f:
            creds = json.load(f)
        token = get_tenant_token(creds["app_id"], creds["app_secret"])
        keys = []
        for path in image_paths:
            key = upload_image(token, path)
            keys.append(key)
            print(f"Uploaded {os.path.basename(path)} -> {key}", file=sys.stderr)
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


# --- Card v2 builder ---


def build_card_v2(color, title, markdown_content, image_keys=None):
    """Build a Card v2 payload with markdown body and optional images.

    If image_after is set, the markdown is split at '---IMG---' markers and
    images are inserted at the specified split point. Otherwise images go at
    the end.
    """
    IMG_SPLIT = "---IMG---"
    parts = markdown_content.split(IMG_SPLIT) if IMG_SPLIT in markdown_content else [markdown_content]

    elements = []
    img_idx = 0
    for i, part in enumerate(parts):
        part = part.strip()
        if part:
            elements.append({
                "tag": "markdown",
                "content": part,
                "text_align": "left",
                "text_size": "normal",
            })
        # Insert images after this part if we have any and this is the split point
        if image_keys and i < len(parts) - 1:
            while img_idx < len(image_keys):
                elements.append({
                    "tag": "img",
                    "img_key": image_keys[img_idx],
                    "alt": {"tag": "plain_text", "content": "image"},
                    "mode": "fit_horizontal",
                    "preview": True,
                })
                img_idx += 1

    # Remaining images go at the end
    if image_keys:
        while img_idx < len(image_keys):
            elements.append({
                "tag": "img",
                "img_key": image_keys[img_idx],
                "alt": {"tag": "plain_text", "content": "image"},
                "mode": "fit_horizontal",
                "preview": True,
            })
            img_idx += 1

    return {
        "schema": "2.0",
        "config": {
            "update_multi": True,
            "enable_forward": True,
            "width_mode": "default",
        },
        "header": {
            "title": {
                "content": title,
                "tag": "plain_text",
            },
            "template": color,
        },
        "body": {
            "direction": "vertical",
            "elements": elements,
        },
    }


# --- Send ---


def send_to_lark(card, webhook_token, signing_secret=None):
    secret = signing_secret or webhook_token
    timestamp = str(int(time.time()))
    sign = compute_sign(timestamp, secret)

    payload = {
        "timestamp": timestamp,
        "sign": sign,
        "msg_type": "interactive",
        "card": card,
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
    parser = argparse.ArgumentParser(description="Send a Card v2 message to Lark via webhook")
    parser.add_argument("message", help="Message content (CommonMark markdown)")
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

    image_keys = []
    if args.images:
        image_keys = upload_images(args.images)

    card = build_card_v2(args.color, args.title, message, image_keys)
    result = send_to_lark(card, webhook_token, signing_secret)

    if result.get("code") == 0:
        print("Message sent successfully.")
    else:
        print(f"Failed to send message: {result}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
