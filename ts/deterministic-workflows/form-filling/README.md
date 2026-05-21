# Fill forms automatically

Map structured data onto web form fields and submit a deterministic browser workflow with Notte.

Template path: `notte-templates/ts/deterministic-workflows/form-filling`
Runtime: TypeScript, entrypoint `main.ts`.

## Run the workflow

```bash
cd notte-templates/ts/deterministic-workflows/form-filling
cp .env.example .env
npm install --no-package-lock
npm start
```

Useful alternate invocations:

```bash
npm run typecheck
```

## Deterministic path

- Demonstrates deterministic form interactions with `goto`, `fill`, `select_dropdown_option`, checkbox/radio clicks, and optional submit.
- Scrapes a final form snapshot with a Zod schema.
- Creates a Notte browser session.
- Displays session details for monitoring.
- Navigates to Selenium's public web form demo.
- Fills text, password, textarea, datalist, date, and color fields.
- Selects a dropdown option and toggles checkbox/radio controls.
- Scrapes the filled form state as structured JSON.
- Leaves submission commented out by default.
- Closes the session cleanly.

## Workflow inputs

Set `NOTTE_API_KEY` in `.env` before running the template.

## Workflow variants

- Lead and intake automation from CRM or CSV records.
- QA checks for required fields and form behavior.
- Repeatable internal workflows for known form layouts.

- Load form data from CSV, JSON, or a CRM.
- Add success-state validation after enabling submission.
- Add screenshots or extracted confirmation messages for audit trails.

## Selector and timing notes

- Missing credentials: verify `.env` contains `NOTTE_API_KEY`.
- Form changes: if Selenium's demo page changes field names, update the selectors in `main.ts`.
- Submission side effects: the submit action is intentionally commented out.

## Reference

Notte documentation: https://docs.notte.cc/
