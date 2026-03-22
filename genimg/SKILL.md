---
name: genimg
description: Generate or edit images using OpenAI-compatible image generation APIs or Google Gemini. Supports text-to-image (文生图) and image-to-image (图生图). Trigger when the user says /genimg, or mentions 文生图, 图生图, AI生图, 画图, generate image, image generation, or wants to create/transform images via API. Works with any provider (火山引擎, OpenAI, Google Gemini, etc.).
---

# genimg — Image Generation

Text-to-image and image-to-image via OpenAI-compatible APIs or Google Gemini.

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

1. **Ask for provider type** — `gemini` or `openai` (OpenAI-compatible)
2. **For Gemini:**
   - Ask for API key (starts with `AIza`)
   - Ask for model (default: `gemini-2.5-flash-image`)
3. **For OpenAI-compatible:**
   - Ask for provider name (e.g. "volcengine", "openai", "together")
   - Ask for base URL
   - Ask for API key
   - Ask for model name
   - Ask for default size (e.g. `2048x2048`, `1024x1024`)
4. **Write config** to `~/.genimg/config.json`, setting this as `default_provider`

If a config already exists, show current providers and offer to add a new one or update an existing one.

## Config

Provider settings live in `~/.genimg/config.json`. Structure:

```json
{
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
}
```

### Gemini provider fields

- `type`: must be `"gemini"` — this is how the script distinguishes Gemini from OpenAI-compatible
- `api_key`: Google AI API key (starts with `AIza`)
- `model`: Gemini model with image generation support. Available models:
  - `gemini-2.5-flash-image` (recommended)
  - `gemini-3-pro-image-preview`
  - `gemini-3.1-flash-image-preview`
- `base_url`: optional, defaults to `https://generativelanguage.googleapis.com`

### OpenAI-compatible provider fields

- `base_url`: API endpoint
- `api_key`: API key
- `model`: model name
- `default_size`: image size (must be valid for the provider/model)

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
- `--image`: enables img2img mode (both Gemini and OpenAI-compatible)
- `--size`: override the provider's default size (OpenAI-compatible only; ignored for Gemini)

## Workflow

1. Run `scripts/generate.py` with prompt and output path
2. Pick a short descriptive filename (English, kebab-case)
3. Show the result to the user with the Read tool
