# Search business registries for KYC

Look up a company in public business records and extract registration details for KYC-style checks.

Template path: `notte-templates/ts/deterministic-workflows/business-lookup`
Runtime: TypeScript, entrypoint `main.ts`.

## Run the workflow

```bash
cd notte-templates/ts/deterministic-workflows/business-lookup
cp .env.example .env
npm install --no-package-lock
npm start
```

Useful alternate invocations:

```bash
npm run typecheck
```

## Deterministic path

- Uses the Node SDK with deterministic page actions instead of an agent.
- Resolves a company name, ticker, or CIK against SEC's public company ticker dataset.
- Opens the SEC EDGAR company page, scrapes the visible company profile, then reads SEC submissions JSON for normalized company fields.
- Defaults to `AAPL`.
- Returns structured company data with a Zod response schema.
- Resolves `COMPANY_QUERY` to a SEC CIK.
- Opens a Notte browser session and navigates to the EDGAR company page.
- Scrapes the visible company profile.
- Reads SEC submissions JSON for filing metadata.
- Prints structured JSON.
- Closes the session cleanly.

## Workflow inputs

Set `NOTTE_API_KEY` in `.env` before running the template.

## Selector and timing notes

- Missing credentials: verify `.env` contains `NOTTE_API_KEY`.
- The company must appear in SEC EDGAR.
- If a broad name query resolves to the wrong company, use a ticker or exact CIK.

## Reference

Notte documentation: https://docs.notte.cc/
