# Find contact emails on a website

Scan a website and its likely contact pages for public email addresses. The template discovers relevant same-site links, falls back to common contact paths, and can return each address with the pages where it was found.

Template path: `python/structured-scraping/website-email-finder`
Runtime: Python, entrypoint `main.py`.

## Run the template

```bash
cd python/structured-scraping/website-email-finder
cp .env.example .env
uv run main.py https://example.com
```

Add `NOTTE_API_KEY` to `.env` before running. A scheme is optional, so `example.com` also works.

## Output options

Print only unique email addresses:

```bash
uv run main.py https://example.com
```

Return JSON mapping each address to its source pages:

```bash
uv run main.py https://example.com --json
```

Show fetched pages and non-fatal errors:

```bash
uv run main.py https://example.com --verbose
```

## How it works

- Opens the target in a Notte browser session, so JavaScript-rendered content is included.
- Decodes HTML entities and percent-encoded content before matching email addresses.
- Follows same-site links whose URL or label suggests a contact or support page.
- Falls back to `/contact`, `/contact-us`, `/get-in-touch`, and `/support` when no relevant link is exposed.
- Skips obvious media and document URLs.
- Deduplicates email addresses while retaining their source pages for JSON output.

## Inputs

- `url`: required positional website URL.
- `--json`: optional machine-readable output.
- `--verbose` / `-v`: optional fetch diagnostics.
- `NOTTE_API_KEY`: required Notte API key, loaded from `.env` or the process environment.

## Notes

- The template only inspects the starting page and likely contact pages; it is not a broad crawler.
- Email addresses rendered as images or heavily obfuscated by custom JavaScript may not be detected.
- Only collect and use public contact information in accordance with applicable laws and website terms.
