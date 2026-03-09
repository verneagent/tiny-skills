#!/usr/bin/env python3
"""OpenAI-compatible image generation. Supports text-to-image and image-to-image."""

import argparse
import base64
import json
import urllib.request
from pathlib import Path

from openai import OpenAI


def encode_image(path: str) -> str:
    data = Path(path).read_bytes()
    b64 = base64.b64encode(data).decode()
    suffix = Path(path).suffix.lower().lstrip(".")
    mime = {"jpg": "jpeg", "jpeg": "jpeg", "png": "png", "webp": "webp"}.get(suffix, "png")
    return f"data:image/{mime};base64,{b64}"


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
                "my-provider": {
                    "base_url": "https://api.example.com/v1",
                    "api_key": "sk-...",
                    "model": "model-name",
                    "default_size": "2048x2048"
                }
            },
            "default_provider": "my-provider"
        }, indent=2))
        raise SystemExit(1)
    config = json.loads(config_path.read_text())

    provider_name = args.provider or config["default_provider"]
    provider = config["providers"][provider_name]

    client = OpenAI(base_url=provider["base_url"], api_key=provider["api_key"])

    size = args.size or provider.get("default_size", "2048x2048")
    extra_body = {}

    if args.image:
        extra_body["image"] = [encode_image(args.image)]
        if not args.size:
            size = "auto"

    resp = client.images.generate(
        model=provider["model"],
        prompt=args.prompt,
        size=size,
        response_format="url",
        extra_body=extra_body if extra_body else None,
    )

    url = resp.data[0].url
    urllib.request.urlretrieve(url, args.output)
    print(f"Saved to {args.output}")


if __name__ == "__main__":
    main()
