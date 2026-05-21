# Extract trending keywords from Google Trends

Collect regional trending search terms from Google Trends and return structured keyword data for analysis.

Template path: `notte-templates/python/structured-scraping/google-trends`
Runtime: Python, entrypoint `main.py`.

## Run a scrape

```bash
cd notte-templates/python/structured-scraping/google-trends
cp .env.example .env
uv run main.py
```

Run from the repository root when you do not want to change directories:

```bash
uv run notte-templates/python/structured-scraping/google-trends/main.py
```

## Extraction path

- Configurable by country codes (US, GB, IN, DE, etc.), language preference, and stories per region.
- Uses Notte browser sessions and structured `scrape` with Pydantic validation.
- Uses inline `uv` script metadata, so no template-specific `pyproject.toml` is required.
- Creates a Notte browser session.
- Displays session details for monitoring.
- Navigates to Google Trends once per configured country/language.
- Dismisses a visible consent dialog when present.
- Extracts compact story clusters with visible volume, start time, related queries, and news headlines when available.
- Outputs structured JSON with country codes, language, timestamp, regional briefings, and shared topics.
- Closes the session cleanly.

## Query controls

- Session: a Notte-hosted browser used to load Google Trends.
- Scrape: Notte method for extracting structured data from a page with natural language instructions.
- Pydantic schema: validates the extracted trend story records.

## Try another target

- Market research and newsroom-style daily briefings across regions.
- Content strategy based on story clusters instead of raw keyword lists.
- Regional comparison for brand, policy, or social listening workflows.

- Parameterize country codes and story counts with CLI arguments.
- Store regional briefings with timestamps for trend history.
- Add semantic clustering for near-duplicate topics across regions.

## Scrape reliability notes

- Missing credentials: verify `.env` contains `NOTTE_API_KEY`.
- Invalid country code: ensure each country code is a valid 2-letter ISO code.
- Empty results: Google Trends may not have trending data for every country/language combination.
- Page changes: Google Trends UI changes may require adjusting the scrape instructions.

## Reference

Notte documentation: https://docs.notte.cc/
