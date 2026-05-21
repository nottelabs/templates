# Get started with Notte

Open a cloud browser session, navigate a real page, and extract structured data with Notte in one small script.

Template path: `notte-templates/python/getting-started/getting-started-with-notte`
Runtime: Python, entrypoint `main.py`.

## Start here

```bash
cd notte-templates/python/getting-started/getting-started-with-notte
cp .env.example .env
uv run main.py
```

Run from the repository root when you do not want to change directories:

```bash
uv run notte-templates/python/getting-started/getting-started-with-notte/main.py
```

Useful alternate invocations:

```bash
WIKIPEDIA_TOPIC_URL="https://en.wikipedia.org/wiki/Artificial_intelligence" uv run notte-templates/python/getting-started/getting-started-with-notte/main.py
```

## What happens

- Uses the Python SDK, `session.scrape()`, and a Pydantic response model.
- Uses inline `uv` script metadata, so no template-specific `pyproject.toml` is required.
- Opens a Notte browser session.
- Navigates to a Wikipedia article.
- Scrapes the right-hand infobox into structured JSON.
- Closes the browser session cleanly.

## Small changes

Set `NOTTE_API_KEY` in `.env` before running the template.

## Setup notes

- Missing credentials: verify `.env` contains `NOTTE_API_KEY`.
- No infobox: some Wikipedia articles do not have a right-hand infobox to extract.

## Reference

Notte documentation: https://docs.notte.cc/
