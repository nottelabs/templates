# Find broken links on websites

Crawl a website, inspect discovered links, and report broken or suspicious URLs for QA monitoring.

Template path: `notte-templates/python/website-qa-monitoring/website-link-tester`
Runtime: Python, entrypoint `main.py`.

## Run the check

```bash
cd notte-templates/python/website-qa-monitoring/website-link-tester
cp .env.example .env
uv run main.py
```

Run from the repository root when you do not want to change directories:

```bash
uv run notte-templates/python/website-qa-monitoring/website-link-tester/main.py
```

## Monitor behavior

- Uses Playwright through `session.page` for deterministic link extraction and navigation.
- Uses Notte `scrape()` for content-match assessment on non-social links.
- Limits verification with `MAX_LINKS` to keep runs bounded.
- Uses inline `uv` script metadata, so no template-specific `pyproject.toml` is required.
- Creates a Notte browser session to collect rendered links.
- Deduplicates links by URL.
- Opens each destination in a Notte session.
- Skips detailed content checks for social domains.
- Uses Notte structured scraping to assess non-social destination content.
- Prints a JSON report.

## Check inputs

- `TARGET_URL`: homepage to inspect, default `https://www.notte.cc`.
- `MAX_LINKS`: maximum links to verify, default `10`.

## Monitoring variants

- Marketing site link QA.
- Content and SEO checks.
- Scheduled link monitoring.

## False-positive checks

- Missing credentials: verify `.env` contains `NOTTE_API_KEY`.
- Some links may be geo-restricted, slow, or require auth/consent.
- Increase `MAX_LINKS` carefully because each link opens a browser session.

## Reference

Notte documentation: https://docs.notte.cc/
