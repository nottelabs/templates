# Log in with Vault credentials

Store credentials in a Notte Vault and use them to authenticate browser sessions without hardcoding secrets.

Template path: `notte-templates/python/auth/apartment-applications-with-vault`
Runtime: Python, entrypoint `main.py`.

## Try the flow

```bash
cd notte-templates/python/auth/apartment-applications-with-vault
cp .env.example .env
uv run main.py
```

Run from the repository root when you do not want to change directories:

```bash
uv run notte-templates/python/auth/apartment-applications-with-vault/main.py
```

Useful alternate invocations:

```bash
Later runs reuse the vault and fill Notte's credential sentinels:
```

## Credential flow

- Creating a vault during setup.
- Storing username/password credentials in the vault.
- Attaching `vault_id` to a session.
- Filling credential sentinel values instead of hardcoding the real credentials into browser actions.
- Scraping authenticated application data.

## Secrets and state

Set `NOTTE_API_KEY` in `.env` before running the template.

## Reference

Notte documentation: https://docs.notte.cc/
