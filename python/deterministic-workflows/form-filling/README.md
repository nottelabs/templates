# Fill forms automatically

Map structured data onto web form fields and submit a deterministic browser workflow with Notte.

Template path: `notte-templates/python/deterministic-workflows/form-filling`
Runtime: Python, entrypoint `main.py`.

## Run the workflow

```bash
cd notte-templates/python/deterministic-workflows/form-filling
cp .env.example .env
uv run main.py
```

Run from the repository root when you do not want to change directories:

```bash
uv run notte-templates/python/deterministic-workflows/form-filling/main.py
```

## Deterministic path

- Demonstrates deterministic form interactions with `goto`, `fill`, `select_dropdown_option`, checkbox/radio clicks, and optional submit.
- Uses inline `uv` script metadata, so no template-specific `pyproject.toml` is required.
- Creates a Notte browser session.
- Displays session details for monitoring.
- Navigates to Selenium's public web form demo.
- Fills text, password, textarea, datalist, date, and color fields.
- Selects a dropdown option and toggles checkbox/radio controls.
- Leaves submission commented out by default.
- Closes the session cleanly.

## Workflow inputs

- Session: a Notte-hosted browser used to load and interact with web pages.
- Fill: a Notte primitive for typing values into input and textarea fields.
- Select dropdown option: a Notte primitive for choosing an option from a native HTML select.

## Workflow variants

- Lead and intake automation from CRM or CSV records.
- QA checks for required fields and form behavior.
- Repeatable internal workflows for known form layouts.

- Load form data from CSV, JSON, or a CRM.
- Add success-state validation after enabling submission.
- Add screenshots or extracted confirmation messages for audit trails.

## Selector and timing notes

- Missing credentials: verify `.env` contains `NOTTE_API_KEY`.
- Form changes: if Selenium's demo page changes field names, update the selectors in `main.py`.
- Submission side effects: the submit action is intentionally commented out.

## Reference

Notte documentation: https://docs.notte.cc/
