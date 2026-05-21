# Search Open Library books

Find books on Open Library and extract titles, authors, editions, and metadata from search results.

Template path: `notte-templates/python/structured-scraping/openlibrary-book-finder`
Runtime: Python, entrypoint `main.py`.

## Run a scrape

```bash
cd notte-templates/python/structured-scraping/openlibrary-book-finder
cp .env.example .env
uv run main.py
```

Run from the repository root when you do not want to change directories:

```bash
uv run notte-templates/python/structured-scraping/openlibrary-book-finder/main.py
```

Useful alternate invocations:

```bash
cp `.env.example` `.env` # Add your Notte API key to `.env
uv run `main.py
```

## Extraction path

- Uses a Notte-hosted Chrome browser session and the Open Library web search UI.
- Defaults to `the hobbit`, then returns title, authors, publication year, editions, ebook count, availability, ratings, and work URLs.
- Parameterized by command-line arguments or environment variables.
- Uses inline `uv` script metadata, so no template-specific `pyproject.toml` is required.
- Creates a Notte browser session and prints the session ID plus viewer link.
- Opens Open Library, submits the requested query, and waits for search results.
- Prints JSON containing the query, search URL, total hit count, returned count, and normalized book results.

## Query controls

- `OPENLIBRARY_QUERY`: search query. Default: `the hobbit`.
- `OPENLIBRARY_MAX_RESULTS`: number of visible results to extract. Default: `5`.
- `OPENLIBRARY_OUTPUT_PATH`: optional path for writing the JSON result.
- `NOTTE_API_KEY`: Notte API key. Loaded from the environment or local `.env`.

Command-line arguments override the query and max-result defaults:

```bash
uv run notte-templates/python/structured-scraping/openlibrary-book-finder/main.py "ursula le guin" 8
```

## Try another target

- Book discovery demos.
- Public-catalog search extraction.
- Examples of turning a Notte CLI workflow export into a parameterized Python workflow.

## Scrape reliability notes

- Missing credentials: verify `.env` contains `NOTTE_API_KEY`.
- Open Library may show an offline banner while search results still render correctly.
- Very broad queries can produce noisy results. Use a specific title or author for cleaner output.

## Reference

Notte documentation: https://docs.notte.cc/
