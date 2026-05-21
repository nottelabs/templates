# Scrape location-specific weather with proxies

Route a Notte browser session through a chosen region and extract the weather content shown for that location.

Template path: `notte-templates/python/proxies-geo/proxies-weather`
Runtime: Python, entrypoint `main.py`.

## Run with routing

```bash
cd notte-templates/python/proxies-geo/proxies-weather
cp .env.example .env
uv run main.py
```

Run from the repository root when you do not want to change directories:

```bash
uv run notte-templates/python/proxies-geo/proxies-weather/main.py
```

## Routing behavior

- Uses Notte sessions with country proxy codes such as `us`, `gb`, `jp`, and `br`.
- Navigates to `wttr.in`, which renders an ASCII weather report for the browser's inferred location.
- Extracts structured weather and nearest-location data with Notte `scrape()` and Pydantic validation.
- Uses inline `uv` script metadata, so no template-specific `pyproject.toml` is required.
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
- wttr.in infers location from the request IP when no city is specified.

## Reference

Notte documentation: https://docs.notte.cc/
