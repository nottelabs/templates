# Compare Amazon prices across countries

Use Notte sessions with regional proxy routing to compare product prices across country-specific Amazon pages.

Template path: `notte-templates/ts/proxies-geo/amazon-global-price-comparison`
Runtime: TypeScript, entrypoint `main.ts`.

## Run with routing

```bash
cd notte-templates/ts/proxies-geo/amazon-global-price-comparison
cp .env.example .env
npm install --no-package-lock
npm start
```

Useful alternate invocations:

```bash
npm run typecheck
SEARCH_QUERY="USB-C travel power adapter kit" RESULTS_COUNT=2 npm start
```

## Routing behavior

- Starts one Notte browser session per country with country proxy settings.
- Uses `session.scrape()` with Zod schemas for local price, stock, delivery, fulfillment, and deal notes.
- Creates Notte sessions for US, Canada, UK, Australia, and Japan.
- Searches Amazon for the configured query.
- Extracts offer title, local price, availability, delivery estimate, fulfillment context, deal note, and URL.
- Prints an availability comparison table and writes JSON results.

## Geo inputs

Set `NOTTE_API_KEY` in `.env` before running the template.

## Proxy notes

- Missing credentials: verify `.env` contains `NOTTE_API_KEY`.
- Amazon can block, redirect, or vary content by region.
- Proxy availability can vary by country.

## Reference

Notte documentation: https://docs.notte.cc/
