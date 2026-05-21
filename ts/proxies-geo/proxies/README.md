# Route browser traffic through proxies

Start Notte browser sessions with proxy routing to inspect location-sensitive pages and network behavior.

Template path: `notte-templates/ts/proxies-geo/proxies`
Runtime: TypeScript, entrypoint `main.ts`.

## Run with routing

```bash
cd notte-templates/ts/proxies-geo/proxies
cp .env.example .env
npm install --no-package-lock
npm start
```

Useful alternate invocations:

```bash
npm run typecheck
```

## Routing behavior

- Tests default proxy routing and country-specific proxy routing.
- Extracts structured IP and geolocation data from the visual `browserleaks.com/ip` report.
- Uses the Node SDK and a Zod response schema.
- Tests built-in proxy routing.
- Tests United States country proxy routing.
- Displays IP information and geolocation data for each test.
- Shows how proxy configuration affects apparent network location.

## Geo inputs

Set `NOTTE_API_KEY` in `.env` before running the template.

## Proxy notes

- Missing credentials: verify `.env` contains `NOTTE_API_KEY`.
- Verify proxy access is enabled for your Notte account.
- Country routing does not guarantee city-level geolocation.

## Reference

Notte documentation: https://docs.notte.cc/
