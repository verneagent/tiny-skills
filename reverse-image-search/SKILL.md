---
name: reverse-image-search
description: Reverse image search using Yandex Images via Playwright. Upload a local image and find where it appears online. Use when the user wants to find the source/origin of an image, check if an image is stock/demo vs authentic, or identify people/places/objects in a photo.
allowed-tools: Bash, Read
---

# Reverse Image Search

Upload a local image to Yandex Images reverse search and extract results.

## Usage

```
python3 <skill_dir>/search.py <image_path>
```

or via the `search-image` helper:

```
search-image <image_path>
```

Arguments:
- `<image_path>` — absolute path to the local image file (PNG, JPG, GIF, etc.)

## How it works

1. Launches Chromium via Playwright
2. Navigates to yandex.com/images
3. Clicks the camera icon to open "search by image"
4. Uploads the local file
5. Waits for results to load
6. Takes a screenshot and extracts text labels from the results page
7. Outputs: screenshot path + extracted text (URLs, descriptions, similar image counts)

## Output

- A screenshot saved to `/tmp/reverse-image-search-result.png`
- Extracted text from result labels printed to stdout (URLs, counts, descriptions)

## Dependencies

- `playwright` (pip)
- Chromium browser installed via `playwright install chromium`

## Notes

- Yandex is used because it supports true reverse image search (content-based), unlike Google which now requires Lens API
- Network access to yandex.com is required (no proxy needed from China)
- Results page uses infinite scroll — the script captures what's immediately visible
