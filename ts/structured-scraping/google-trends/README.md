# Extract trending keywords from Google Trends

Collect regional trending search terms from Google Trends and return structured keyword data for analysis.

Template path: `notte-templates/ts/structured-scraping/google-trends`
Runtime: TypeScript, entrypoint `main.ts`.

## Run a scrape

```bash
cd notte-templates/ts/structured-scraping/google-trends
cp .env.example .env
npm install --no-package-lock
npm start
```

## Query controls

Edit `countryCodes`, `storiesPerRegion`, and `language` in `main.ts` to change regions and language. The default compares `US` and `GB`.

The script opens Google Trends once per configured region, dismisses a visible consent dialog when present, uses Notte structured scraping with Zod schemas, and prints regional story clusters plus shared topics.

## Reference

Notte documentation: https://docs.notte.cc/
