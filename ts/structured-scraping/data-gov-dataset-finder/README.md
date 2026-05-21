# Find datasets on Data.gov

Search Data.gov, visit dataset detail pages, and return ranked metadata for public datasets.

Template path: `notte-templates/ts/structured-scraping/data-gov-dataset-finder`
Runtime: TypeScript, entrypoint `main.ts`.

## Run a scrape

```bash
cd notte-templates/ts/structured-scraping/data-gov-dataset-finder
cp .env.example .env
npm install --no-package-lock
npm start
```

Useful alternate invocations:

```bash
npm start -- --query climate --limit 5
```

## Query controls

- `NOTTE_API_KEY`: required Notte API key.
- `DATA_GOV_QUERY`: default search query.
- `DATA_GOV_RESULT_LIMIT`: default number of ranked results to enrich.

Command-line flags override the environment defaults:

```bash
npm start -- --query "water quality" --limit 3
```

The script opens Data.gov search results, uses Notte structured scraping with Zod schemas, visits the selected dataset detail pages, and prints a JSON report with result-card and resource metadata.

## Reference

Notte documentation: https://docs.notte.cc/
