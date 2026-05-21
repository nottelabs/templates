# Scrape prediction market data

Use a Notte Agent to research a prediction market and extract odds, prices, volume, and market context.

Template path: `notte-templates/python/agentic-research/kalshi-research`
Runtime: Python, entrypoint `main.py`.

## Run the research task

```bash
cd notte-templates/python/agentic-research/kalshi-research
cp .env.example .env
uv run main.py
```

Run from the repository root when you do not want to change directories:

```bash
uv run notte-templates/python/agentic-research/kalshi-research/main.py
```

## Research loop

- Uses a Notte Agent because the search and result-selection flow is open-ended and UI-dependent.
- Returns structured data with a Pydantic response model.
- Uses inline `uv` script metadata, so no template-specific `pyproject.toml` is required.
- Creates a Notte browser session.
- Starts a Notte Agent at Kalshi.
- Searches for `SEARCH_QUERY`.
- Opens the most relevant market.
- Extracts market title, odds, yes/no prices, volume, and price change when visible.
- Prints structured JSON.
- Closes the session cleanly.

## Research inputs

Set `NOTTE_API_KEY` in `.env` before running the template.

## Use it for

- Market research.
- Trading analysis.
- Prediction-market data enrichment.

## Research caveats

- Missing credentials: verify `.env` contains `NOTTE_API_KEY`.
- Agent runs can take longer and cost more than deterministic scripts.
- Search queries may not map to active or visible markets.
- Kalshi may vary UI or gate content by region.

## Reference

Notte documentation: https://docs.notte.cc/
