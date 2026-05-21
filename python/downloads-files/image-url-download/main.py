# Notte: Image URL Download - See README.md for full documentation
#
# Uses Notte scrape() to find image URLs on a page, then downloads each image
# through Playwright's browser context so requests inherit the session cookies,
# proxy, and headers.
#
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "notte-sdk[playwright]",
#     "pydantic",
#     "python-dotenv",
# ]
# ///

import os
import re
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

from dotenv import load_dotenv
from notte_sdk import NotteClient
from pydantic import BaseModel, Field

load_dotenv(Path(__file__).with_name(".env"))

MAX_IMAGES = int(os.environ.get("MAX_IMAGES", "10"))
OUTPUT_DIR = os.environ.get("OUTPUT_DIR", "./images")
DEFAULT_URL = "https://yandex.com/images/search?text=flowers"

MIME_TO_EXT = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
    "image/gif": "gif",
    "image/svg+xml": "svg",
    "image/avif": "avif",
    "image/bmp": "bmp",
    "image/tiff": "tiff",
}


class ImageUrls(BaseModel):
    urls: list[str] = Field(description="List of absolute image URLs found on the page")


def is_valid_url(url: str) -> bool:
    """Return True only for absolute http/https URLs."""
    try:
        parsed = urlparse(url)
        return parsed.scheme in ("http", "https") and bool(parsed.netloc)
    except Exception:
        return False


def image_filename(url: str, mime_type: str, index: int) -> str:
    """Derive a safe filename from an image URL and detected MIME type."""
    ext = MIME_TO_EXT.get(mime_type, "bin")
    try:
        path = urlparse(url).path
        segments = [part for part in path.split("/") if part]
        segment = segments[-1] if segments else ""
        base = re.sub(r"\.[^.]+$", "", segment) or f"image-{index}"
        safe = re.sub(r"[^a-zA-Z0-9_-]", "_", base)[:80]
        return f"{safe}-{int(time.time() * 1000)}.{ext}"
    except Exception:
        return f"image-{index}-{int(time.time() * 1000)}.{ext}"


def print_viewer_url(session) -> None:
    viewer_url = getattr(session, "viewer_url", None)
    if not viewer_url:
        viewer_url = getattr(session.status(), "viewer_url", None)
    if viewer_url:
        print(f"Live View Link: {viewer_url}")


def extract_image_urls_from_dom(page) -> list[str]:
    """Collect image URLs directly from the rendered DOM."""
    return page.evaluate(
        """
        () => {
          const urls = new Set();
          for (const img of document.querySelectorAll("img")) {
            if (img.currentSrc) urls.add(img.currentSrc);
            if (img.src) urls.add(img.src);
          }
          for (const el of document.querySelectorAll("*")) {
            const bg = getComputedStyle(el).backgroundImage;
            for (const match of bg.matchAll(/url\\(["']?([^"')]+)["']?\\)/g)) {
              urls.add(new URL(match[1], document.baseURI).href);
            }
          }
          return Array.from(urls);
        }
        """
    )


def main() -> None:
    api_key = os.environ.get("NOTTE_API_KEY")
    if not api_key:
        raise RuntimeError("Missing NOTTE_API_KEY. Set it in your environment or .env file.")

    target_url = sys.argv[1] if len(sys.argv) >= 2 else DEFAULT_URL
    print(f"Image URL Download - target: {target_url}")
    print(f"Max images: {MAX_IMAGES} | Output: {OUTPUT_DIR}/<hostname>/\n")

    client = NotteClient(api_key=api_key)

    with client.Session(open_viewer=True, idle_timeout_minutes=2) as session:
        print("Notte session initialized successfully")
        print(f"Session ID: {session.session_id}")
        print_viewer_url(session)

        page = session.page

        print(f"\nNavigating to {target_url}...")
        page.goto(target_url, wait_until="networkidle", timeout=60000)
        session.execute(type="scroll_down")
        session.execute(type="scroll_down")

        print("Extracting image URLs from page...")
        extracted = session.scrape(
            instructions=(
                "Extract all image URLs on this page, including src attributes "
                "from img tags and any CSS background image URLs. Return absolute URLs only."
            ),
            response_format=ImageUrls,
        )
        all_urls = extracted.urls
        if not all_urls:
            print("Structured scrape returned no URLs; falling back to DOM extraction...")
            all_urls = extract_image_urls_from_dom(page)

        seen: set[str] = set()
        unique_urls = []
        for url in all_urls:
            if url and url not in seen and is_valid_url(url):
                seen.add(url)
                unique_urls.append(url)

        print(f"Found {len(unique_urls)} unique image URL(s)")

        urls = unique_urls[:MAX_IMAGES]
        if len(unique_urls) > MAX_IMAGES:
            print(f"Capping at {MAX_IMAGES} (adjust MAX_IMAGES to change this)")

        if not urls:
            print("No image URLs found on the page.")
            return

        hostname = urlparse(target_url).hostname or "unknown"
        output_dir = Path(OUTPUT_DIR) / hostname
        output_dir.mkdir(parents=True, exist_ok=True)

        saved = 0
        failed = 0

        print(f"\nDownloading {len(urls)} image(s) via browser context...\n")

        for i, url in enumerate(urls):
            print(f"[{i + 1}/{len(urls)}] {url} -> ", end="", flush=True)

            try:
                response = page.context.request.get(url)
                if not response.ok:
                    print(f"FAILED (HTTP {response.status}, skipping)")
                    failed += 1
                    continue
                image_bytes = response.body()
                mime_type = response.headers.get("content-type", "").split(";")[0].strip()
            except Exception as error:
                print(f"FAILED ({error}, skipping)")
                failed += 1
                continue

            try:
                filename = image_filename(url, mime_type, i)
                filepath = output_dir / filename
                filepath.write_bytes(image_bytes)
            except Exception as error:
                print(f"FAILED (write error: {error}, skipping)")
                failed += 1
                continue

            print(f"saved as {filename} ({len(image_bytes)} bytes)")
            saved += 1

        print(f"\nDone! {saved} saved, {failed} failed -> {output_dir}/")

    print("Session closed successfully")


if __name__ == "__main__":
    try:
        main()
    except Exception as err:
        print(f"Error: {err}")
        print("Common issues:")
        print("  - Check .env has NOTTE_API_KEY")
        print("  - Verify the target URL is accessible")
        print("Docs: https://docs.notte.cc/")
        sys.exit(1)
