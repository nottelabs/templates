# Handle bot checks while verifying licenses

Use Notte browser settings for CAPTCHA and bot protection while extracting license status from a public verification site.

Template path: `notte-templates/python/captcha-bot-handling/nurse-verification-cloudflare`
Runtime: Python, entrypoint `main.py`.

## Run the challenge

```bash
cd notte-templates/python/captcha-bot-handling/nurse-verification-cloudflare
cp .env.example .env
uv run main.py
```

Run from the repository root when you do not want to change directories:

```bash
uv run notte-templates/python/captcha-bot-handling/nurse-verification-cloudflare/main.py
```

## Challenge flow

- Uses Notte with Playwright for deterministic form filling.
- Enables Notte CAPTCHA solving because the target site may show an anti-captcha step.
- Uses Notte `scrape()` with a Pydantic schema for results.
- Uses inline `uv` script metadata, so no template-specific `pyproject.toml` is required.
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
