# Scrape quote author profiles

Crawl quote pages, follow author links, and extract structured author biographies and quote metadata.

Template path: `notte-templates/ts/structured-scraping/quotes-author-scraper`
Runtime: TypeScript, entrypoint `main.ts`.

## Run a scrape

```bash
cd notte-templates/ts/structured-scraping/quotes-author-scraper
cp .env.example .env
npm install --no-package-lock
npm start
```

## Query controls

- `BASE_URL`: target site, defaults to `https://quotes.toscrape.com/`.
- `MAX_PAGES`: quote listing pages to visit.
- `INCLUDE_AUTHOR_PROFILES`: `true` or `false`.
- `MAX_AUTHORS`: unique author profiles to visit.
- `NOTTE_API_KEY`: required Notte API key.

This TypeScript version uses Notte session navigation and Zod-backed structured scraping to collect quotes, pagination links, and author profile pages.

## Reference

Notte documentation: https://docs.notte.cc/
