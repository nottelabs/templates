# Automate MFA with Vaults

Store username, password, and a TOTP secret in a Notte Vault so browser sessions can complete MFA without manual input.

Template path: `notte-templates/ts/auth/mfa-vault-todo`
Runtime: TypeScript, entrypoint `main.ts`.

## Try the flow

```bash
cd notte-templates/ts/auth/mfa-vault-todo
cp .env.example .env
npm install --no-package-lock
npm start
```

## Credential flow

- Extracting demo credentials and a TOTP secret from a web page.
- Creating an ephemeral Notte vault.
- Filling login fields with vault placeholders.
- Letting Notte generate the current TOTP code from the stored secret.
- Checking the authentication result with a Zod schema.

## Secrets and state

Set `NOTTE_API_KEY` in `.env` before running the template.

## Reference

Notte documentation: https://docs.notte.cc/
