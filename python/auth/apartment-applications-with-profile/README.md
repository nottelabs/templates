# Persist login sessions with Profiles

Create a Notte Profile once, save authenticated browser state, and reuse it to access logged-in pages without repeating login.

Template path: `notte-templates/python/auth/apartment-applications-with-profile`
Runtime: Python, entrypoint `main.py`.

## Try the flow

```bash
cd notte-templates/python/auth/apartment-applications-with-profile
cp .env.example .env
uv run main.py
```

Run from the repository root when you do not want to change directories:

```bash
uv run notte-templates/python/auth/apartment-applications-with-profile/main.py
```

## Credential flow

- Creating a browser profile with the Notte SDK.
- Saving authenticated browser state with `persist=True`.
- Reusing the same profile in a later session.
- Scraping authenticated application data without replaying the login flow.

## Secrets and state

Set `NOTTE_API_KEY` in `.env` before running the template.

## Reference

Notte documentation: https://docs.notte.cc/
