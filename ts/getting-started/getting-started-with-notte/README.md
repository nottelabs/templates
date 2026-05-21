# Get started with Notte

Open a cloud browser session, navigate a real page, and extract structured data with Notte in one small script.

Template path: `notte-templates/ts/getting-started/getting-started-with-notte`
Runtime: TypeScript, entrypoint `main.ts`.

## Start here

```bash
cd notte-templates/ts/getting-started/getting-started-with-notte
cp .env.example .env
npm install --no-package-lock
npm start
```

Useful alternate invocations:

```bash
npm run typecheck
WIKIPEDIA_TOPIC_URL="https://en.wikipedia.org/wiki/Artificial_intelligence" npm start
```

## What happens

- Uses the Node SDK, `session.scrape()`, and a Zod response schema.
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
