# Receive auth emails with Personas

Use a Notte Persona mailbox to receive verification emails and continue authenticated application workflows.

Template path: `notte-templates/python/auth/job-board-email-applications`
Runtime: Python, entrypoint `main.py`.

## Try the flow

```bash
cd notte-templates/python/auth/job-board-email-applications
cp .env.example .env
uv run main.py
```

Run from the repository root when you do not want to change directories:

```bash
uv run notte-templates/python/auth/job-board-email-applications/main.py
```

## Credential flow

- Creating a Notte persona.
- Receiving a real sign-in email in the persona inbox.
- Opening the Supabase verification link in the browser session.
- Scraping authenticated user data after email sign-in.

## Secrets and state

Set `NOTTE_API_KEY` in `.env` before running the template.

## Reference

Notte documentation: https://docs.notte.cc/
