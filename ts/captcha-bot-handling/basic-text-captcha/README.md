# Solve text CAPTCHAs automatically

Use Notte to read and complete a simple text CAPTCHA challenge inside an automated browser workflow.

Template path: `notte-templates/ts/captcha-bot-handling/basic-text-captcha`
Runtime: TypeScript, entrypoint `main.ts`.

## Run the challenge

```bash
cd notte-templates/ts/captcha-bot-handling/basic-text-captcha
cp .env.example .env
npm install --no-package-lock
npm start
```

Useful alternate invocations:

```bash
npm run typecheck
```

## Challenge flow

- Uses `solve_captchas`, proxy routing, and the Notte `captcha_solve` action with `captcha_type="text"`.
- Validates the CAPTCHA demo form and scrapes the result message with a Zod schema.
- Creates a Notte browser session with CAPTCHA solving enabled.
- Navigates to the captcha.com text CAPTCHA demo.
- Runs the text CAPTCHA solve action.
- Clicks Validate.
- Scrapes the validation message.
- Reports whether the page says `Correct!` or `Incorrect!`.

## Challenge settings

Set `NOTTE_API_KEY` in `.env` before running the template.

## Captcha and bot notes

- Missing credentials: verify `.env` contains `NOTTE_API_KEY`.
- Account access: CAPTCHA solving and proxies may need to be enabled for your Notte account.
- Demo page changes: update selectors if captcha.com changes the form markup.

## Reference

Notte documentation: https://docs.notte.cc/
