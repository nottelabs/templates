# Scrape calendar events

Extract structured event names, dates, times, and links from public calendar pages with a browser-backed probe.

Template path: `notte-templates/ts/public-api-hybrid/public-calendar-event-extractor`
Runtime: TypeScript, entrypoint `main.ts`.

## Run the hybrid probe

```bash
cd notte-templates/ts/public-api-hybrid/public-calendar-event-extractor
cp .env.example .env
npm install --no-package-lock
npm start
```

Useful alternate invocations:

```bash
npm start -- --limit 5
npm --prefix ts/public-api-hybrid/public-calendar-event-extractor start -- --url https://www.loc.gov/events/ --limit 3
```

## API and browser path

- Defaults to `https://www.loc.gov/events/`, but accepts any `loc.gov` event listing URL.
- Uses a Notte browser session for traceability when `NOTTE_API_KEY` is set, then extracts from the LOC JSON listing endpoint.
- Parameterized by listing URL and result limit from the CLI or `.env`.

## Probe inputs

- `NOTTE_API_KEY`: optional; enables the Notte browser probe when set.
- `LOC_EVENTS_URL`: default event listing URL when `--url` is omitted.
- `LOC_EVENT_LIMIT`: default number of events when `--limit` is omitted.
- `USE_PROXY`: whether the Notte browser session uses proxies. Defaults to `true`.

## Alternate sources

The Python exploration notes and exported workflow are preserved in `exploration-notes.md` and `exported_workflow.py`.

## Reference

Notte documentation: https://docs.notte.cc/
