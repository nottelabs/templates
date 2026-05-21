# Scrape calendar events

Extract structured event names, dates, times, and links from public calendar pages with a browser-backed probe.

Template path: `notte-templates/python/public-api-hybrid/public-calendar-event-extractor`
Runtime: Python, entrypoint `main.py`.

## Run the hybrid probe

```bash
cd notte-templates/python/public-api-hybrid/public-calendar-event-extractor
cp .env.example .env
uv run main.py
```

Run from the repository root when you do not want to change directories:

```bash
uv run notte-templates/python/public-api-hybrid/public-calendar-event-extractor/main.py
```

Useful alternate invocations:

```bash
uv run main.py --limit 5
```

## API and browser path

- Defaults to `https://www.loc.gov/events/`, but accepts any `loc.gov` event listing URL.
- Uses a Notte browser session for traceability when `NOTTE_API_KEY` is set, then extracts from the LOC JSON listing endpoint.
- Parameterized by listing URL and result limit from the CLI or `.env`.
- Original listing URL and derived LOC JSON URL.
- Browser probe status and result count.
- Events with title, detail URL, date, local start/end timestamps, venue, attendance condition, status, categories, and description.

## Probe inputs

- `NOTTE_API_KEY`: optional; enables the Notte browser probe when set.
- `LOC_EVENTS_URL`: default event listing URL when `--url` is omitted.
- `LOC_EVENT_LIMIT`: default number of events when `--limit` is omitted.
- `USE_PROXY`: whether the Notte browser session uses proxies. Defaults to `true`.

## Alternate sources

```bash
uv run notte-templates/python/public-api-hybrid/public-calendar-event-extractor/main.py --limit 5
uv run notte-templates/python/public-api-hybrid/public-calendar-event-extractor/main.py --url "https://www.loc.gov/events/?fa=location:online-only" --limit 10
LOC_EVENTS_URL=https://www.loc.gov/events/ LOC_EVENT_LIMIT=2 uv run notte-templates/python/public-api-hybrid/public-calendar-event-extractor/main.py
```

Notte CLI exploration partially succeeded: sessions started and the workflow was exported, but top-level navigation to `https://www.loc.gov/events/` closed the remote browser context during exploration. The raw exported workflow is kept in `exported_workflow.py`; notes from the exploration are in `exploration-notes.md`.

## Reference

Notte documentation: https://docs.notte.cc/
