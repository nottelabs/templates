# Receive auth emails with Personas

Use a Notte Persona mailbox to receive verification emails and continue authenticated application workflows.

Template path: `notte-templates/ts/auth/job-board-email-applications`
Runtime: TypeScript, entrypoint `main.ts`.

## Try the flow

```bash
cd notte-templates/ts/auth/job-board-email-applications
cp .env.example .env
npm install --no-package-lock
npm start
```

## Credential flow

- Creating a Notte persona.
- Receiving a real sign-in email in the persona inbox.
- Opening the Supabase verification link in the browser session.
- Scraping authenticated user data with a Zod schema.

## Secrets and state

Set `NOTTE_API_KEY` in `.env` before running the template.

## Reference

Notte documentation: https://docs.notte.cc/
