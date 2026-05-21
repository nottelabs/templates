# Scrape Amazon products

Extract Amazon search result data including prices, delivery details, discounts, and product context as structured JSON.

Template path: `notte-templates/ts/ecommerce-price-monitoring/amazon-product-scraping`
Runtime: TypeScript, entrypoint `main.ts`.

## Run a price check

```bash
cd notte-templates/ts/ecommerce-price-monitoring/amazon-product-scraping
cp .env.example .env
npm install --no-package-lock
npm start
```

Useful alternate invocations:

```bash
npm run typecheck
SEARCH_QUERY="noise cancelling earbuds" npm start
```

## Price collection path

- Uses direct search URL navigation instead of prompt-driven typing.
- Uses the Node SDK, `session.scrape()`, and a Zod response schema.
- Enables Notte proxy routing and captcha solving for the session.
- Opens a Notte browser session with proxy routing.
- Navigates directly to an Amazon search results page.
- Extracts up to 5 non-sponsored monitoring candidates.
- Prints structured JSON with price, discount, delivery, and variant context.
- Closes the session cleanly.

## Product inputs

Set `NOTTE_API_KEY` in `.env` before running the template.

## Marketplace notes

- Missing credentials: verify `.env` contains `NOTTE_API_KEY`.
- Amazon may show bot checks or vary layout by region.
- Sponsored results and ads can appear before organic results; adjust scrape instructions if your category is noisy.

## Reference

Notte documentation: https://docs.notte.cc/
