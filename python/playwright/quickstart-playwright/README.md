# Quickstart: Playwright

Connect Playwright to a Notte browser session, interact with a real website, and extract page content.

Template path: `notte-templates/python/playwright/quickstart-playwright`
Runtime: Python, entrypoint `main.py`.

## Connect Playwright

```bash
cd notte-templates/python/playwright/quickstart-playwright
cp .env.example .env
uv run main.py
```

Run from the repository root when you do not want to change directories:

```bash
uv run notte-templates/python/playwright/quickstart-playwright/main.py
```

## Browser control path

- Uses Notte deterministic actions plus `session.scrape()` for structured extraction.
- Uses inline `uv` script metadata, so no template-specific `pyproject.toml` is required.
- Creates a Notte browser session.
- Connects to the session via Playwright using `session.page`.
- Navigates to Wikipedia's Main Page.
- Opens the menu and clicks Random article with `session.execute(...)`.
- Prints the loaded article URL and heading.
- Extracts a generic article snapshot with title, description, lead paragraph, sections, and notable facts.
- Closes the session cleanly.

## Connection settings

- Session: a Notte-hosted browser instance.
- CDP: Chrome DevTools Protocol, used by Playwright to control the remote browser.
- Playwright: browser automation library for deterministic UI interaction.
- Structured scrape: a Notte extraction call that returns data matching a Pydantic model.

## Connection notes

- Missing credentials: verify `.env` contains `NOTTE_API_KEY`.
- Site changes: Wikipedia selector or navigation changes may require updating locators.
- Playwright package: keep `notte-sdk[playwright]` in the script dependency metadata.
- Random pages: some Wikipedia pages have sparse content, so the scrape can return fewer sections or facts.

## Reference

Notte documentation: https://docs.notte.cc/
