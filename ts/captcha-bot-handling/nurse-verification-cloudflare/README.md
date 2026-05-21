# Handle bot checks while verifying licenses

Use Notte browser settings for CAPTCHA and bot protection while extracting license status from a public verification site.

Template path: `notte-templates/ts/captcha-bot-handling/nurse-verification-cloudflare`
Runtime: TypeScript, entrypoint `main.ts`.

## Run the challenge

```bash
cd notte-templates/ts/captcha-bot-handling/nurse-verification-cloudflare
cp .env.example .env
npm install --no-package-lock
npm start
```

Useful alternate invocations:

```bash
npm run typecheck
```

## Challenge flow

- Uses Notte deterministic actions for form filling.
- Enables Notte CAPTCHA solving because the target site may show an anti-bot step.
- Uses Notte `scrape()` with a Zod schema for results.
- Creates a Notte browser session.
- Loops through `LICENSE_RECORDS`.
- Uses `Angelo Agee` / license `91` as the default public sample record.
- Navigates to the verification site.
- Fills first name, last name, and license number.
- Runs the search and attempts CAPTCHA solving if needed.
- Extracts verification results as structured JSON.
- Closes the session cleanly.

## Challenge settings

Set `NOTTE_API_KEY` in `.env` before running the template.

## Challenge variants

- HR compliance.
- Credential verification.
- Batch license status checks.

## Captcha and bot notes

- Missing credentials: verify `.env` contains `NOTTE_API_KEY`.
- CAPTCHA solving may be required and can be flaky depending on the site.
- The current target form uses anonymous inputs, so the script fills by input position.
- Update selectors if the verification site changes.

## Reference

Notte documentation: https://docs.notte.cc/
