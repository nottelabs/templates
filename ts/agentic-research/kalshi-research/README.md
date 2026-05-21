# Scrape prediction market data

Use a Notte Agent to research a prediction market and extract odds, prices, volume, and market context.

Template path: `notte-templates/ts/agentic-research/kalshi-research`
Runtime: TypeScript, entrypoint `main.ts`.

## Run the research task

```bash
cd notte-templates/ts/agentic-research/kalshi-research
cp .env.example .env
npm install --no-package-lock
npm start
```

## Research loop

- Running an agent in a Notte browser session.
- Navigating an open-ended search and result-selection flow.
- Returning structured market data with a Zod schema.
- Using proxies and captcha solving for a public market site.

## Research inputs

Set `NOTTE_API_KEY` in `.env` before running the template.

## Reference

Notte documentation: https://docs.notte.cc/
