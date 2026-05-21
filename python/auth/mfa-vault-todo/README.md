# Automate MFA with Vaults

Store username, password, and a TOTP secret in a Notte Vault so browser sessions can complete MFA without manual input.

Template path: `notte-templates/python/auth/mfa-vault-todo`
Runtime: Python, entrypoint `main.py`.

## Try the flow

```bash
cd notte-templates/python/auth/mfa-vault-todo
cp .env.example .env
uv run main.py
```

Run from the repository root when you do not want to change directories:

```bash
uv run notte-templates/python/auth/mfa-vault-todo/main.py
```

## Credential flow

- Vault setup: opens the demo page, extracts the test credentials and TOTP secret, and saves them to an ephemeral Notte vault.
- Automatic TOTP filling: uses vault placeholders in a form fill action; Notte generates the current TOTP code from the stored secret.
- Retry logic: reloads the page and fills from the vault again if the first TOTP window expires.
- Initializes a Notte browser session.
- Displays live session link for monitoring.
- Creates an ephemeral vault with `with client.Vault() as vault`.
- Extracts test credentials and TOTP secret from the demo page during setup.
- Stores email, password, and `mfa_secret` in the temporary vault.
- Opens a new session with `vault_id`.
- Fills email, password, and TOTP fields with vault placeholders.
- Lets the vault generate the current TOTP code from the stored secret.
- Submits authentication form.
- Checks authentication result.
- Retries with a fresh vault-generated code if the initial TOTP window expires.
- Closes the session cleanly.
- Deletes the vault automatically when the context manager exits.

## Secrets and state

- session.page: use Playwright primitives through a Notte browser session.
- scrape: extract structured data from web pages using natural language instructions and Pydantic models.
- Vault: encrypted Notte credential storage attached to a browser session with `vault_id`.
- mfa_secret: a stored TOTP secret key. The vault turns it into a fresh one-time code when the fill action uses the MFA placeholder.
- TOTP: Time-based One-Time Password - a 6-digit code that changes every 30 seconds.

## Where to adapt it

- Vault-backed MFA: Store encrypted TOTP secrets alongside username and password credentials.
- Automated authentication: Complete MFA challenges automatically when session persistence isn't enough.
- Zero-touch MFA: Eliminate user interaction for MFA completion in automated workflows.
- Session recovery: Automatically handle MFA prompts when re-authenticating expired sessions.

- Multiple accounts: store multiple vault credentials for different application URLs.
- SMS/Email MFA: Extend to support SMS codes (via Twilio/Bandwidth API) or email codes (via Gmail API/IMAP)
- Backup codes: Implement fallback to backup codes stored during initial MFA setup
- Session persistence: Combine with persistent browser state to minimize MFA prompts.
- Error handling: Add graceful fallback to user prompts when automation fails

## Auth checks

- "ModuleNotFoundError": ensure all dependencies are installed via pip
- Missing credentials: verify .env contains NOTTE_API_KEY
- Vault lifetime: the vault is intentionally temporary and is deleted after the run
- TOTP code expiration: codes are valid for 30 seconds; the script automatically retries with a fresh vault-generated code
- Page structure changes: if the demo site structure changes, extraction may fail
- Network timeouts: ensure stable internet connection for reliable page loading
- Import errors: activate your virtual environment if you created one

## Reference

Notte documentation: https://docs.notte.cc/
