#!/usr/bin/env python3
"""Image generation supporting OpenAI-compatible APIs and Google Gemini."""

import argparse
import base64
import json
import urllib.request
import urllib.error
from pathlib import Path


def encode_image(path: str) -> str:
    data = Path(path).read_bytes()
    b64 = base64.b64encode(data).decode()
    suffix = Path(path).suffix.lower().lstrip(".")
    mime = {"jpg": "jpeg", "jpeg": "jpeg", "png": "png", "webp": "webp"}.get(suffix, "png")
    return f"data:image/{mime};base64,{b64}"


def generate_gemini(provider: dict, prompt: str, output: str, image_path: str | None = None):
    """Generate image using Google Gemini API."""
    api_key = provider["api_key"]
    model = provider.get("model", "gemini-2.5-flash-image")
    base_url = provider.get("base_url", "https://generativelanguage.googleapis.com")

    url = f"{base_url}/v1beta/models/{model}:generateContent?key={api_key}"

    parts = []
    if image_path:
        img_data = Path(image_path).read_bytes()
        b64 = base64.b64encode(img_data).decode()
        suffix = Path(image_path).suffix.lower().lstrip(".")
        mime = {"jpg": "jpeg", "jpeg": "jpeg", "png": "png", "webp": "webp"}.get(suffix, "png")
        parts.append({"inlineData": {"mimeType": f"image/{mime}", "data": b64}})
    parts.append({"text": prompt})

    body = json.dumps({
        "contents": [{"parts": parts}],
        "generationConfig": {"responseModalities": ["TEXT", "IMAGE"]},
    }).encode()

    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        error_body = json.loads(e.read())
        msg = error_body.get("error", {}).get("message", str(e))
        raise SystemExit(f"Gemini API error ({e.code}): {msg}")

    candidates = data.get("candidates", [{}])
    parts = candidates[0].get("content", {}).get("parts", [])

    for part in parts:
        if "inlineData" in part:
            img_bytes = base64.b64decode(part["inlineData"]["data"])
            Path(output).write_bytes(img_bytes)
            print(f"Saved to {output}")
            return

    text_parts = [p["text"] for p in parts if "text" in p]
    raise SystemExit(f"No image in response. Text: {' '.join(text_parts)}")


def generate_openai(provider: dict, prompt: str, output: str, image_path: str | None = None, size: str | None = None):
    """Generate image using OpenAI-compatible API."""
    from openai import OpenAI

    client = OpenAI(base_url=provider["base_url"], api_key=provider["api_key"])
    size = size or provider.get("default_size", "2048x2048")
    extra_body = {}

    if image_path:
        extra_body["image"] = [encode_image(image_path)]
        if not size:
            size = "auto"

    resp = client.images.generate(
        model=provider["model"],
        prompt=prompt,
        size=size,
        response_format="url",
        extra_body=extra_body if extra_body else None,
    )

    url = resp.data[0].url
    urllib.request.urlretrieve(url, output)
    print(f"Saved to {output}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", help="Provider name from config.json")
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--image", help="Input image for img2img")
    parser.add_argument("--output", required=True)
    parser.add_argument("--size", help="Override default size")
    args = parser.parse_args()

    config_path = Path.home() / ".genimg" / "config.json"
    if not config_path.exists():
        print("Error: Config not found at ~/.genimg/config.json")
        print("Run '/genimg init' to set up a provider, or create the file manually.")
        print()
        print("Expected format:")
        print(json.dumps({
            "providers": {
                "gemini": {
                    "type": "gemini",
                    "api_key": "AIza...",
                    "model": "gemini-2.5-flash-image"
                },
                "volcengine": {
                    "base_url": "https://ark.cn-beijing.volces.com/api/v3",
                    "api_key": "sk-...",
                    "model": "doubao-seedream-3-0-t2i-250415",
                    "default_size": "2048x2048"
                }
            },
            "default_provider": "gemini"
        }, indent=2))
        raise SystemExit(1)
    config = json.loads(config_path.read_text())

    provider_name = args.provider or config["default_provider"]
    provider = config["providers"][provider_name]

    if provider.get("type") == "gemini":
        generate_gemini(provider, args.prompt, args.output, args.image)
    else:
        generate_openai(provider, args.prompt, args.output, args.image, args.size)


if __name__ == "__main__":
    main()
