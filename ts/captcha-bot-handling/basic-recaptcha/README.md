# Solve reCAPTCHAs automatically

Run a Notte browser session with CAPTCHA solving enabled and complete a protected page flow without manual intervention.

Template path: `notte-templates/ts/captcha-bot-handling/basic-recaptcha`
Runtime: TypeScript, entrypoint `main.ts`.

## Run the challenge

```bash
cd notte-templates/ts/captcha-bot-handling/basic-recaptcha
cp .env.example .env
npm install --no-package-lock
npm start
```

Useful alternate invocations:

```bash
npm run typecheck
SOLVE_CAPTCHAS=false npm start
```

## Challenge flow

- Uses `solve_captchas`, proxy routing, and the Notte `captcha_solve` action.
- Extracts page content with a Zod schema to verify successful form submission.
- Creates a Notte browser session with CAPTCHA solving enabled.
- Navigates to NopeCHA's reCAPTCHA V2 demo page.
- Runs the CAPTCHA solve action.
- Waits for the page callback to render the verification response.
- Extracts visible page text.
- Verifies the success message when the challenge is solved.
- Closes the session cleanly.

## Challenge settings

Set `NOTTE_API_KEY` in `.env` before running the template.

## Captcha and bot notes

- Missing credentials: verify `.env` contains `NOTTE_API_KEY`.
- Account access: CAPTCHA solving and proxies may need to be enabled for your Notte account.
- Solving time: allow time for CAPTCHA solving to complete.
- Demo page changes: update the verification logic if the NopeCHA demo changes.

## Reference

Notte documentation: https://docs.notte.cc/
