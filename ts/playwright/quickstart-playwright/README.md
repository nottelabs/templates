# Quickstart: Playwright

Connect Playwright to a Notte browser session, interact with a real website, and extract page content.

Template path: `notte-templates/ts/playwright/quickstart-playwright`
Runtime: TypeScript, entrypoint `main.ts`.

## Connect Playwright

```bash
cd notte-templates/ts/playwright/quickstart-playwright
cp .env.example .env
npm install --no-package-lock
npm start
```

Useful alternate invocations:

```bash
npm run typecheck
```

## Browser control path

- Uses Node Playwright over the Notte session CDP URL.
- Uses Notte `session.scrape()` for structured extraction with a Zod schema.
- Creates a Notte browser session.
- Connects Playwright to the session with Chrome DevTools Protocol.
- Navigates to Wikipedia's Main Page.
- Opens the menu and clicks Random article.
- Prints the loaded article URL and heading.
- Extracts a generic article snapshot with title, description, lead paragraph, sections, and notable facts.
- Closes the Playwright connection and the Notte session cleanly.

## Connection settings

Set `NOTTE_API_KEY` in `.env` before running the template.

## Connection notes

- Missing credentials: verify `.env` contains `NOTTE_API_KEY`.
- Site changes: Wikipedia selector or navigation changes may require updating locators.
- CDP availability: the session status must include a `cdp_url`.
- Random pages: some Wikipedia pages have sparse content, so the scrape can return fewer sections or facts.

## Reference

Notte documentation: https://docs.notte.cc/
