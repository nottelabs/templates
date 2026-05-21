# Search Open Library books

Find books on Open Library and extract titles, authors, editions, and metadata from search results.

Template path: `notte-templates/ts/structured-scraping/openlibrary-book-finder`
Runtime: TypeScript, entrypoint `main.ts`.

## Run a scrape

```bash
cd notte-templates/ts/structured-scraping/openlibrary-book-finder
cp .env.example .env
npm install --no-package-lock
npm start
```

Useful alternate invocations:

```bash
npm start -- "the hobbit" 5
```

## Query controls

- `OPENLIBRARY_QUERY`: default search query.
- `OPENLIBRARY_MAX_RESULTS`: number of visible results to extract.
- `OPENLIBRARY_OUTPUT_PATH`: optional JSON output path.
- `NOTTE_API_KEY`: Notte API key.

The script opens Open Library search results, uses a Zod schema with Notte structured scraping, normalizes relative work URLs, and prints a compact book-discovery report.

## Reference

Notte documentation: https://docs.notte.cc/
