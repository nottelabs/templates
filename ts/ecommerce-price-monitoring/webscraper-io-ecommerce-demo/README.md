# Scrape e-commerce product cards

Extract product names, prices, descriptions, ratings, and detail links from a demo e-commerce catalog.

Template path: `notte-templates/ts/ecommerce-price-monitoring/webscraper-io-ecommerce-demo`
Runtime: TypeScript, entrypoint `main.ts`.

## Run a price check

```bash
cd notte-templates/ts/ecommerce-price-monitoring/webscraper-io-ecommerce-demo
cp .env.example .env
npm install --no-package-lock
npm start
```

Useful alternate invocations:

```bash
npm run typecheck
WEBSCRAPER_RESULT_LIMIT=6 npm start
WEBSCRAPER_CATEGORY_URL="http://webscraper.io/test-sites/e-commerce/static/computers/tablets" npm start
```

## Price collection path

- Defaults to the laptops category, but accepts any category URL and result limit.
- Uses a Notte browser session with deterministic navigation and Zod structured extraction.
- Preserves the original CLI exploration artifacts in `exported_workflow.py` and `exploration-notes.md`.
- Opens a Notte browser session.
- Scrapes product cards across as many listing pages as needed to satisfy the limit.
- Prints requested category URL, browser category URL, category title, total item count text, and product records.
- Each product includes title, detail URL, price text, numeric price, description, review count, listing page, page position, and image URL.

## Product inputs

Set `NOTTE_API_KEY` in `.env` before running the template.

## Marketplace notes

- Missing credentials: verify `.env` contains `NOTTE_API_KEY`.
- Use a Webscraper.io static category URL.
- Keep `WEBSCRAPER_RESULT_LIMIT` small while testing.

## Reference

Notte documentation: https://docs.notte.cc/
