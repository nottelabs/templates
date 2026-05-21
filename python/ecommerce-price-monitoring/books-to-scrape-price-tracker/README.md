# Track e-commerce book prices

Scrape book listings, prices, stock status, and detail pages from an e-commerce demo site for price monitoring.

Template path: `notte-templates/python/ecommerce-price-monitoring/books-to-scrape-price-tracker`
Runtime: Python, entrypoint `main.py`.

## Run a price check

```bash
cd notte-templates/python/ecommerce-price-monitoring/books-to-scrape-price-tracker
cp .env.example .env
uv run main.py
```

Run from the repository root when you do not want to change directories:

```bash
uv run notte-templates/python/ecommerce-price-monitoring/books-to-scrape-price-tracker/main.py
```

## Price collection path

- Uses a Notte-hosted browser session with Playwright selectors discovered through the Notte CLI.
- Defaults to the public demo site at `http://books.toscrape.com/`.
- Visits listing pages, optionally opens product detail pages, and prints a JSON price snapshot.
- Uses inline `uv` script metadata, so no template-specific `pyproject.toml` is required.
- Creates a Notte browser session and prints the session ID plus viewer link.
- Navigates through one or more catalog pages.
- Extracts title, price, stock text, rating, detail URL, and image URL from each listing card.
- When details are enabled, opens each product page for UPC, full availability count, category path, and description.
- Prints JSON with all books, the five cheapest books, price alerts, and low-stock alerts.

## Product inputs

- `BOOKS_START_URL`: catalog or category URL to start from. Default: `http://books.toscrape.com/`.
- `BOOKS_MAX_PAGES`: number of listing pages to scan. Default: `2`.
- `BOOKS_MAX_BOOKS`: maximum books to collect. Default: `40`.
- `BOOKS_PRICE_ALERT_BELOW`: alert threshold in GBP. Default: `20.00`.
- `BOOKS_LOW_STOCK_THRESHOLD`: alert when available count is at or below this number. Default: `5`.
- `BOOKS_INCLUDE_DETAILS`: visit each detail page for UPC, exact availability count, category, and description. Default: `true`.
- `BOOKS_OUTPUT_PATH`: optional path for writing the JSON snapshot.

## Commerce variants

- Price monitoring demos.
- Structured catalog scraping.
- Pagination and detail-page enrichment examples.
- Building alerting jobs from a browser-collected snapshot.

## Marketplace notes

- Missing credentials: verify `.env` contains `NOTTE_API_KEY`.
- The site worked reliably over `http://books.toscrape.com/` during exploration; HTTPS failed in one Notte session.
- Detail-page enrichment opens one page per book. Set `BOOKS_INCLUDE_DETAILS=false` for faster catalog-only runs.

## Reference

Notte documentation: https://docs.notte.cc/
