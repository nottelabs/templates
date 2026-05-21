# Scrape location-specific weather with proxies

Route a Notte browser session through a chosen region and extract the weather content shown for that location.

Template path: `notte-templates/ts/proxies-geo/proxies-weather`
Runtime: TypeScript, entrypoint `main.ts`.

## Run with routing

```bash
cd notte-templates/ts/proxies-geo/proxies-weather
cp .env.example .env
npm install --no-package-lock
npm start
```

Useful alternate invocations:

```bash
npm run typecheck
```

## Routing behavior

- Uses Notte sessions with country proxy codes such as `us`, `gb`, `jp`, and `br`.
- Navigates to `wttr.in`, which renders a weather report for the browser's inferred location.
- Extracts structured weather and nearest-location data with Notte `scrape()` and Zod validation.
- Creates a Notte session for each country proxy.
- Navigates to wttr.in's browser-friendly weather page.
- Extracts the nearest area, region, country, temperature, condition, and humidity.
- Prints a summary for each country.
- Closes each session cleanly.

## Geo inputs

Set `NOTTE_API_KEY` in `.env` before running the template.

## Proxy notes

- Missing credentials: verify `.env` contains `NOTTE_API_KEY`.
- Proxy access may need to be enabled for your Notte account.
- Country proxy routing does not guarantee city-level geolocation.

## Reference

Notte documentation: https://docs.notte.cc/
