# Find broken links on websites

Crawl a website, inspect discovered links, and report broken or suspicious URLs for QA monitoring.

Template path: `notte-templates/ts/website-qa-monitoring/website-link-tester`
Runtime: TypeScript, entrypoint `main.ts`.

## Run the check

```bash
cd notte-templates/ts/website-qa-monitoring/website-link-tester
cp .env.example .env
npm install --no-package-lock
npm start
```

## Check inputs

- `TARGET_URL`: homepage to inspect, default `https://www.notte.cc`.
- `MAX_LINKS`: maximum links to verify.
- `NOTTE_API_KEY`: required Notte API key.

The script collects visible homepage links with Notte structured scraping, deduplicates them, opens each destination, and uses a Zod-backed scrape to assess whether non-social destinations match their link text.

## Reference

Notte documentation: https://docs.notte.cc/
