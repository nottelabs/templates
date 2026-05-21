# Persist login sessions with Profiles

Create a Notte Profile once, save authenticated browser state, and reuse it to access logged-in pages without repeating login.

Template path: `notte-templates/ts/auth/apartment-applications-with-profile`
Runtime: TypeScript, entrypoint `main.ts`.

## Try the flow

```bash
cd notte-templates/ts/auth/apartment-applications-with-profile
cp .env.example .env
npm install --no-package-lock
npm start
```

## Credential flow

- Creating a browser profile with the Notte SDK.
- Saving authenticated browser state with `persist: true`.
- Reusing the same profile in a later session.
- Scraping authenticated application data with a Zod schema.

## Secrets and state

Set `NOTTE_API_KEY` in `.env` before running the template.

## Reference

Notte documentation: https://docs.notte.cc/
