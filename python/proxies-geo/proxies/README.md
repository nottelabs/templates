# Route browser traffic through proxies

Start Notte browser sessions with proxy routing to inspect location-sensitive pages and network behavior.

Template path: `notte-templates/python/proxies-geo/proxies`
Runtime: Python, entrypoint `main.py`.

## Run with routing

```bash
cd notte-templates/python/proxies-geo/proxies
cp .env.example .env
uv run main.py
```

Run from the repository root when you do not want to change directories:

```bash
uv run notte-templates/python/proxies-geo/proxies/main.py
```

## Routing behavior

- Tests default proxy routing and country-specific proxy routing.
- Extracts structured IP and geolocation data from the visual `browserleaks.com/ip` report.
- Uses inline `uv` script metadata, so no template-specific `pyproject.toml` is required.
- Tests built-in proxy routing.
- Tests United States country proxy routing.
- Displays IP information and geolocation data for each test.
- Shows how proxy configuration affects apparent network location.

## Geo inputs

- Proxies: Notte session option for routing browser traffic through proxy infrastructure.
- Country proxy: a two-letter country code such as `us` or `gb` passed as the session `proxies` value.
- Scrape: Notte structured extraction from the current page.

## Routing variants

- Geo-testing location-specific content.
- Checking proxy routing before a larger scraping workflow.
- Comparing responses across network locations.
- Verifying the apparent city, state, country, and coordinates from a proxy-routed browser.

- Add more country codes.
- Write results to JSON for comparison.
- Add retries for transient proxy failures.

## Proxy notes

- Missing credentials: verify `.env` contains `NOTTE_API_KEY`.
- Proxy availability: verify proxy access is enabled for your Notte account.
- Geo expectations: country routing is supported; city/state-level routing may require different proxy configuration.

## Reference

Notte documentation: https://docs.notte.cc/
