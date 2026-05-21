# Scrape Amazon products

Extract Amazon search result data including prices, delivery details, discounts, and product context as structured JSON.

Template path: `notte-templates/python/ecommerce-price-monitoring/amazon-product-scraping`
Runtime: Python, entrypoint `main.py`.

## Run a price check

```bash
cd notte-templates/python/ecommerce-price-monitoring/amazon-product-scraping
cp .env.example .env
uv run main.py
```

Run from the repository root when you do not want to change directories:

```bash
uv run notte-templates/python/ecommerce-price-monitoring/amazon-product-scraping/main.py
```

## Price collection path

- Uses direct search URL navigation instead of prompt-driven typing.
- Uses Notte `scrape()` with a Pydantic schema for price, list-price, deal, delivery, and purchase-context fields.
- Enables proxy routing for the session.
- Uses inline `uv` script metadata, so no template-specific `pyproject.toml` is required.
- Creates a Notte browser session.
- Navigates directly to the Amazon search results page for `SEARCH_QUERY`.
- Extracts up to 5 non-sponsored monitoring candidates.
- Outputs structured JSON with price, discount, delivery, and variant context.
- Closes the session cleanly.

## Product inputs

Set `NOTTE_API_KEY` in `.env` before running the template.

## Commerce variants

- Deal and coupon monitoring.
- Assortment checks for product families.
- Delivery-promise tracking for recurring purchases.

## Marketplace notes

- Missing credentials: verify `.env` contains `NOTTE_API_KEY`.
- Amazon may show bot checks or vary layout by region.
- Sponsored results and ads can appear before organic results; adjust scrape instructions if your category is noisy.

## Reference

Notte documentation: https://docs.notte.cc/
