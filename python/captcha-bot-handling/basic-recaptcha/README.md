# Solve reCAPTCHAs automatically

Run a Notte browser session with CAPTCHA solving enabled and complete a protected page flow without manual intervention.

Template path: `notte-templates/python/captcha-bot-handling/basic-recaptcha`
Runtime: Python, entrypoint `main.py`.

## Run the challenge

```bash
cd notte-templates/python/captcha-bot-handling/basic-recaptcha
cp .env.example .env
uv run main.py
```

Run from the repository root when you do not want to change directories:

```bash
uv run notte-templates/python/captcha-bot-handling/basic-recaptcha/main.py
```

## Challenge flow

- Uses `solve_captchas=True`, proxy routing, and the Notte `captcha_solve` action.
- Extracts page content to verify successful form submission.
- Uses inline `uv` script metadata, so no template-specific `pyproject.toml` is required.
- Creates a Notte browser session with CAPTCHA solving enabled.
- Navigates to NopeCHA's reCAPTCHA V2 demo page.
- Runs the CAPTCHA solve action.
- Waits for the page callback to render the verification response.
- Extracts visible page text.
- Verifies the success message when the challenge is solved.
- Closes the session cleanly.

## Challenge settings

- `solve_captchas`: Notte session option that enables CAPTCHA solving support.
- `captcha_solve`: Notte action for solving a visible CAPTCHA challenge.
- Scrape: Notte structured extraction from the current page.

## Captcha and bot notes

- Missing credentials: verify `.env` contains `NOTTE_API_KEY`.
- Account access: CAPTCHA solving and proxies may need to be enabled for your Notte account.
- Solving time: allow time for CAPTCHA solving to complete.
- Demo page changes: update selectors if the NopeCHA demo page changes.

## Reference

Notte documentation: https://docs.notte.cc/
