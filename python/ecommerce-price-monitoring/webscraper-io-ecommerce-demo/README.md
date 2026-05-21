# Scrape e-commerce product cards

Extract product names, prices, descriptions, ratings, and detail links from a demo e-commerce catalog.

Template path: `notte-templates/python/ecommerce-price-monitoring/webscraper-io-ecommerce-demo`
Runtime: Python, entrypoint `main.py`.

## Run a price check

```bash
cd notte-templates/python/ecommerce-price-monitoring/webscraper-io-ecommerce-demo
cp .env.example .env
uv run main.py
```

Run from the repository root when you do not want to change directories:

```bash
uv run notte-templates/python/ecommerce-price-monitoring/webscraper-io-ecommerce-demo/main.py
```

Useful alternate invocations:

```bash
uv run main.py --limit 12
```

## Price collection path

- Defaults to the laptops category, but accepts any category URL and result limit.
- Uses a Notte browser session with deterministic DOM extraction and pagination.
- Uses inline `uv` script metadata, so no template-specific `pyproject.toml` is required.
- Requested category URL, browser category URL, category title, and total item count text.
- Product cards across as many listing pages as needed to satisfy the limit.
- For each product: title, detail URL, price text, numeric price, description, review count, listing page, page position, and image URL.

## Product inputs

- `NOTTE_API_KEY`: required by the Python SDK.
- `WEBSCRAPER_CATEGORY_URL`: default category URL when `--category-url` is omitted.
- `WEBSCRAPER_RESULT_LIMIT`: default maximum number of product cards to return.

## Commerce variants

```bash
uv run notte-templates/python/ecommerce-price-monitoring/webscraper-io-ecommerce-demo/main.py --limit 12
uv run notte-templates/python/ecommerce-price-monitoring/webscraper-io-ecommerce-demo/main.py --category-url "http://webscraper.io/test-sites/e-commerce/static/computers/tablets" --limit 10
WEBSCRAPER_RESULT_LIMIT=18 uv run notte-templates/python/ecommerce-price-monitoring/webscraper-io-ecommerce-demo/main.py
```

The Notte CLI exploration succeeded using the `http://` category URL. The raw exported workflow is kept in `exported_workflow.py`; notes from the exploration are in `exploration-notes.md`.

## Reference

Notte documentation: https://docs.notte.cc/
