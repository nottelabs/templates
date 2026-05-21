# Extract and download images

Give the template a page URL and download the images discovered during the Notte browser session.

Template path: `notte-templates/python/downloads-files/image-url-download`
Runtime: Python, entrypoint `main.py`.

## Download once

```bash
cd notte-templates/python/downloads-files/image-url-download
cp .env.example .env
uv run main.py
```

Run from the repository root when you do not want to change directories:

```bash
uv run notte-templates/python/downloads-files/image-url-download/main.py
```

## File workflow

- Browser-context downloads: `page.context.request.get()` inherits session cookies, proxy, and headers.
- Structured URL extraction: tries Notte `scrape()` first, then falls back to deterministic Playwright DOM extraction.
- Format-aware naming: uses the `Content-Type` response header to choose file extensions.
- Organized output: images are saved to `./images/<hostname>/`.
- Uses inline `uv` script metadata, so no template-specific `pyproject.toml` is required.
- Creates a Notte browser session.
- Connects Playwright through `session.page`.
- Navigates to the target URL and waits for rendering.
- Extracts image URLs with Notte `scrape()` or the DOM fallback.
- Deduplicates URLs and caps at `MAX_IMAGES`.
- Downloads each image through the browser context.
- Saves images to `./images/<hostname>/`.
- Closes the session cleanly.

## Download controls

- Scrape: Notte structured extraction from the current page.
- Browser context request: Playwright API request made from the active browser context.
- `MAX_IMAGES`: configurable cap on how many images to download per run.
- `OUTPUT_DIR`: configurable output directory, defaulting to `./images`.

## Other downloads

- Asset archiving from pages you own or have permission to scrape.
- Visual regression fixture collection.
- Authenticated media downloads after logging into a session.

## File handling notes

- Missing credentials: verify `.env` contains `NOTTE_API_KEY`.
- Zero images found: the page may lazy-load images; add scrolling before extraction if needed.
- Download failures: some image endpoints block direct asset requests even from the browser context.
- `MAX_IMAGES` cap: set `MAX_IMAGES=50` in `.env` if you need more than 10 images.
- Output location: set `OUTPUT_DIR=/tmp/images` or another path if you do not want files under `./images`.

## Reference

Notte documentation: https://docs.notte.cc/
