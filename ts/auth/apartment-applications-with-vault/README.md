# Log in with Vault credentials

Store credentials in a Notte Vault and use them to authenticate browser sessions without hardcoding secrets.

Template path: `notte-templates/ts/auth/apartment-applications-with-vault`
Runtime: TypeScript, entrypoint `main.ts`.

## Try the flow

```bash
cd notte-templates/ts/auth/apartment-applications-with-vault
cp .env.example .env
npm install --no-package-lock
npm start
```

Useful alternate invocations:

```bash
Later runs reuse the vault and fill Notte's credential sentinels:
```

## Credential flow

- Creating a vault during setup.
- Storing username/password credentials in the vault.
- Attaching `vault_id` to a session.
- Filling credential sentinel values instead of hardcoding real credentials into browser actions.
- Scraping authenticated application data with a Zod schema.

## Secrets and state

Set `NOTTE_API_KEY` in `.env` before running the template.

## Reference

Notte documentation: https://docs.notte.cc/
