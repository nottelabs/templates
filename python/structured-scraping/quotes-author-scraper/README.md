# Scrape quote author profiles

Crawl quote pages, follow author links, and extract structured author biographies and quote metadata.

Template path: `notte-templates/python/structured-scraping/quotes-author-scraper`
Runtime: Python, entrypoint `main.py`.

## Run a scrape

```bash
cd notte-templates/python/structured-scraping/quotes-author-scraper
cp .env.example .env
uv run main.py
```

Run from the repository root when you do not want to change directories:

```bash
uv run notte-templates/python/structured-scraping/quotes-author-scraper/main.py
```

## Extraction path

- Uses a Notte-hosted browser session controlled through Playwright.
- No AI required at runtime: selectors extract quotes, pagination, and author profiles.
- Uses inline `uv` script metadata, so no template-specific `pyproject.toml` is required.
- `quotes`: quote text, author, author URL, tags, and source page.
- `authors`: author name, birth date, birth location, profile URL, and description.
- `pages_scraped`, `quote_count`, and `author_count` summary fields.

## Query controls

Environment variables:

- `NOTTE_API_KEY`: required Notte API key.
- `BASE_URL`: target site, defaults to `https://quotes.toscrape.com/`.
- `MAX_PAGES`: quote listing pages to visit, defaults to `2`.
- `INCLUDE_AUTHOR_PROFILES`: `true` or `false`, defaults to `true`.
- `MAX_AUTHORS`: unique author profiles to visit, defaults to `10`.

Example:

```bash
MAX_PAGES=1 MAX_AUTHORS=5 uv run notte-templates/python/structured-scraping/quotes-author-scraper/main.py
```

## Scrape reliability notes

- Missing credentials: verify `.env` contains `NOTTE_API_KEY`.
- Selector changes: this template expects the Quotes to Scrape HTML structure.
- Large runs: increase `MAX_PAGES` and `MAX_AUTHORS` gradually when testing.

## Reference

Notte documentation: https://docs.notte.cc/
