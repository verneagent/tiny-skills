---
name: genimg
description: Generate or edit images using OpenAI-compatible image generation APIs. Supports text-to-image (文生图) and image-to-image (图生图). Trigger when the user says /genimg, or mentions 文生图, 图生图, AI生图, 画图, generate image, image generation, or wants to create/transform images via API. Works with any provider (火山引擎, OpenAI, etc.) that exposes the standard images/generations endpoint.
---

# genimg — Image Generation

Text-to-image and image-to-image via any OpenAI-compatible image API.

## Usage

```
/genimg <prompt>                     # text-to-image
/genimg <image_path> <prompt>        # image-to-image
/genimg init                         # interactive setup wizard
```

## Setup

If `~/.genimg/config.json` doesn't exist, the script will print a friendly error with the expected format and suggest running `/genimg init`.

### `/genimg init` — Interactive Setup

When the user runs `/genimg init`, walk them through creating or updating `~/.genimg/config.json`:

1. **Ask for provider name** (e.g. "volcengine", "openai", "together")
2. **Ask for base URL** (the OpenAI-compatible API endpoint, e.g. `https://ark.cn-beijing.volces.com/api/v3`)
3. **Ask for API key**
4. **Ask for model name** (e.g. `doubao-seedream-3-0-t2i-250415`, `dall-e-3`)
5. **Ask for default size** (e.g. `2048x2048`, `1024x1024`)
6. **Write config** to `~/.genimg/config.json`, setting this as `default_provider`

If a config already exists, show current providers and offer to add a new one or update an existing one.

## Config

Provider settings live in `~/.genimg/config.json`. Structure:

```json
{
  "providers": {
    "<name>": {
      "base_url": "...",
      "api_key": "...",
      "model": "...",
      "default_size": "2048x2048"
    }
  },
  "default_provider": "<name>"
}
```

`default_size` must be valid for the configured provider and model. Do not assume `1024x1024` is universally accepted. For the current `volcengine` configuration, use `2048x2048`.

To add a new provider, just add an entry to `providers`. To switch default, change `default_provider`.

## Running

```bash
python3 <skill-path>/scripts/generate.py \
  --prompt "<prompt>" \
  --output "<output_path>" \
  [--provider "<provider_name>"] \
  [--image "<input_image_path>"] \
  [--size "2048x2048"]
```

- `--provider`: optional, defaults to `default_provider` in config
- `--image`: enables img2img mode, size defaults to `auto`
- `--size`: override the provider's default size

## Workflow

1. Run `scripts/generate.py` with prompt and output path
2. Pick a short descriptive filename (English, kebab-case)
3. Show the result to the user with the Read tool
