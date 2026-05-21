# Compare Amazon prices across countries

Use Notte sessions with regional proxy routing to compare product prices across country-specific Amazon pages.

Template path: `notte-templates/python/proxies-geo/amazon-global-price-comparison`
Runtime: Python, entrypoint `main.py`.

## Run with routing

```bash
cd notte-templates/python/proxies-geo/amazon-global-price-comparison
cp .env.example .env
uv run main.py
```

Run from the repository root when you do not want to change directories:

```bash
uv run notte-templates/python/proxies-geo/amazon-global-price-comparison/main.py
```

Useful alternate invocations:

```bash
SEARCH_QUERY="USB-C travel power adapter kit" RESULTS_COUNT=2 uv run main.py
```

## Routing behavior

- Browser: starts one Notte browser session per country with geolocation proxies.
- Extraction: uses `session.scrape()` with Pydantic models for local price, stock, delivery, fulfillment, and deal notes.
- Creates Notte sessions for US, Canada, UK, Australia, and Japan.
- Searches Amazon for the configured travel-accessory query.
- Extracts offer title, local price, availability, delivery estimate, fulfillment context, deal note, and URL.
- Prints an availability-focused comparison table and writes JSON results.

## Geo inputs

Set `NOTTE_API_KEY` in `.env` before running the template.

## Routing variants

- Add currency conversion or landed-cost estimates.
- Persist offer snapshots to CSV or a database.
- Tune countries, query, and offer count for your workflow.

## Proxy notes

- Missing credentials: verify `.env` contains `NOTTE_API_KEY`.
- Amazon can block, redirect, or vary content by region.
- Proxy availability can vary by country.

## Reference

Notte documentation: https://docs.notte.cc/
