# Notte Templates

Ready-to-run browser automation examples for Notte.

This repository contains Python and TypeScript templates for common browser workflows: authenticated sessions, Vault-backed credentials, Persona inboxes, CAPTCHA handling, proxy routing, structured scraping, downloads, monitoring, and Notte Functions.

## Repository Layout

```text
notte-templates/
  python/        Python templates, one folder per workflow
  ts/            TypeScript templates and npm workspace
  run-outputs/   Local run logs and generated reports
```

Each template lives at:

```text
<language>/<category>/<template-name>/
```

Most template folders include:

- `README.md` with the goal, run command, and inputs
- `.env.example` with the expected environment variables
- `main.py` or `main.ts` as the entrypoint

## Requirements

- A Notte API key
- Python templates: `uv`
- TypeScript templates: Node.js and npm

Set your API key in the template you want to run:

```bash
cp .env.example .env
```

Then edit `.env` and add:

```bash
NOTTE_API_KEY=your_api_key_here
```

## Run A Python Template

```bash
cd python/getting-started/getting-started-with-notte
cp .env.example .env
uv run main.py
```

Python templates use inline `uv` script metadata, so each template can declare its own dependencies in `main.py`.

## Run A TypeScript Template

Install shared dependencies once:

```bash
cd ts
npm install
```

Then run a template:

```bash
cd getting-started/getting-started-with-notte
cp .env.example .env
npm start
```

The TypeScript folder is an npm workspace. See `ts/README.md` for workspace commands.

## Template Categories

- `auth`: Profiles, Vaults, Personas, and login flows
- `captcha-bot-handling`: CAPTCHA solving and bot-protected pages
- `deterministic-workflows`: repeatable browser workflows without agent planning
- `downloads-files`: browser workflows that save files locally
- `ecommerce-price-monitoring`: product scraping and price checks
- `functions`: deployable Notte Functions
- `playwright`: direct Playwright control of Notte browser sessions
- `proxies-geo`: proxy routing and location-sensitive browsing
- `structured-scraping`: structured extraction from public websites
- `website-qa-monitoring`: release, package, and website health checks

