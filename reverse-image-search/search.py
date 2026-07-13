#!/usr/bin/env python3
"""Reverse image search using Yandex Images via Playwright."""

import sys
import os
import time
from pathlib import Path


def search(image_path: str) -> dict:
    from playwright.sync_api import sync_playwright

    abs_path = os.path.abspath(image_path)
    if not os.path.exists(abs_path):
        raise FileNotFoundError(f"Image not found: {abs_path}")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox"]
        )
        context = browser.new_context(
            viewport={"width": 1440, "height": 900},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        )
        page = context.new_page()

        # Navigate to Yandex Images
        page.goto("https://yandex.com/images/", wait_until="domcontentloaded")
        time.sleep(2)

        # Click the camera button (search by image)
        camera_btn = page.locator('button[aria-label="search by image"], button[title*="image"], button:has(svg)').first
        if camera_btn.count() == 0:
            # Fallback: look for any element containing "image" near the search bar
            camera_btn = page.locator('button').filter(has_text="").first

        try:
            camera_btn.click(timeout=5000)
        except Exception:
            # Try direct URL: yandex.com/images/search?source=collections
            pass

        time.sleep(1)

        # Look for file input (may appear after clicking camera, or use drag-drop zone)
        file_input = page.locator('input[type="file"]')
        if file_input.count() == 0:
            # Some layouts have the file input hidden in the page
            # Re-navigate with direct upload parameter
            page.goto("https://yandex.com/images/", wait_until="domcontentloaded")
            time.sleep(2)

        # Set up file chooser listener + click upload area
        upload_trigger = page.locator('input[type="file"], .upload-button, .cbir-button, button')
        chooser_promise = None
        try:
            chooser_promise = page.wait_for_event("filechooser", timeout=3000)
        except Exception:
            pass

        # Try clicking various upload triggers
        for selector in ['button[aria-label*="image"]', 'button[title*="image"]', '.cbir-button', '.upload-button']:
            try:
                el = page.locator(selector).first
                if el.count() > 0:
                    el.click(timeout=2000)
                    break
            except Exception:
                continue

        # If no chooser was triggered yet, try the file input directly
        if chooser_promise is None:
            try:
                chooser_promise = page.wait_for_event("filechooser", timeout=3000)
            except Exception:
                pass
        else:
            # Cancel and retry
            pass

        # Actually — use a more robust approach: dispatch file input directly
        # Inject a visible file input and use it
        try:
            # Try to find or create filechooser
            # Easiest approach: use the input[type=file] that exists
            file_inputs = page.locator('input[type="file"]')
            if chooser_promise:
                file_chooser = chooser_promise
                file_chooser.set_files(abs_path)
            else:
                # Fallback: use JS to trigger upload
                page.evaluate("""
                    () => {
                        const input = document.querySelector('input[type="file"]');
                        if (!input) {
                            const el = document.createElement('input');
                            el.type = 'file';
                            el.style.display = 'block';
                            el.style.position = 'fixed';
                            el.style.top = '0';
                            el.style.left = '0';
                            el.style.zIndex = '999999';
                            document.body.appendChild(el);
                            return 'created';
                        }
                        return 'found';
                    }
                """)
                time.sleep(0.5)
                file_input = page.locator('input[type="file"]').first
                file_input.set_input_files(abs_path)
        except Exception as e:
            print(f"Upload attempt 1 failed: {e}")

        # Wait for results
        time.sleep(5)
        page.wait_for_load_state("networkidle", timeout=15000)

        # If still on search page, we might need a different approach
        current_url = page.url
        if "search" not in current_url:
            # Redirect to the direct upload search URL
            page.goto("https://yandex.com/images/touch/search?rpt=imageview", wait_until="domcontentloaded")
            time.sleep(2)
            # Try to find and click upload area on this page
            try:
                file_input = page.locator('input[type="file"]').first
                file_input.set_input_files(abs_path)
                time.sleep(5)
                page.wait_for_load_state("networkidle", timeout=15000)
            except Exception as e:
                print(f"Touch upload failed: {e}")

        # Take screenshot
        screenshot_path = "/tmp/reverse-image-search-result.png"
        page.screenshot(path=screenshot_path, full_page=False)

        # Extract result text
        result_text = page.evaluate("""
            () => {
                const labels = document.querySelectorAll(
                    '.CbirSites-ItemDomain, .CbirSites-ItemTitle, ' +
                    '.cbir-search__sites-item-domain, .cbir-search__sites-item-title, ' +
                    '.Tags-Item, .cbir-item__tag, ' +
                    'a[href*="http"]'
                );
                const texts = [];
                labels.forEach(el => {
                    const t = el.textContent?.trim();
                    const href = el.href || '';
                    if (t && t.length > 1) texts.push(href ? `${t} | ${href}` : t);
                });
                return texts.slice(0, 30);
            }
        """)

        # Try to get the "similar images" count
        similar_count = page.evaluate("""
            () => {
                const el = document.querySelector('[class*="similar"], [class*="count"], [class*="result"]');
                return el ? el.textContent?.trim() : null;
            }
        """)

        browser.close()

        return {
            "screenshot": screenshot_path,
            "texts": result_text,
            "similar_count": similar_count,
            "final_url": page.url
        }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 search.py <image_path>")
        sys.exit(1)

    image_path = sys.argv[1]
    print(f"Searching for: {image_path}")
    results = search(image_path)

    print(f"\nFinal URL: {results['final_url']}")
    print(f"Similar count: {results['similar_count']}")
    print(f"\nExtracted results ({len(results['texts'])} items):")
    for t in results['texts']:
        print(f"  - {t}")

    print(f"\nScreenshot saved to: {results['screenshot']}")
