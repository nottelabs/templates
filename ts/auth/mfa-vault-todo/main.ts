import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { config as loadEnv } from "dotenv";
import { NotteClient } from "notte-sdk";
import { z } from "zod";

const __dirname = dirname(fileURLToPath(import.meta.url));
loadEnv({ path: join(__dirname, ".env") });
loadEnv({ path: join(__dirname, "..", ".env") });

const DEMO_URL = "https://authenticationtest.com/totpChallenge/";
const EMAIL_PLACEHOLDER = "user@example.org";
const PASSWORD_PLACEHOLDER = "mycoolpassword";
const MFA_PLACEHOLDER = "999779";

const Credentials = z.object({
  email: z.string().describe("Email address"),
  password: z.string().describe("Password"),
  totp_secret: z.string().describe("The TOTP secret key for generating codes"),
});

const AuthResult = z.object({
  success: z.boolean().describe("Whether authentication was successful"),
  message: z.string().describe("Success or error message"),
});

type Credentials = z.infer<typeof Credentials>;

async function printViewerUrl(session: { status: () => Promise<{ viewer_url?: string | null }> }) {
  const status = await session.status();
  if (status.viewer_url) {
    console.log(`Live View Link: ${status.viewer_url}`);
  }
}

async function extractDemoCredentials(client: NotteClient): Promise<Credentials> {
  return client.Session({ open_viewer: true, idle_timeout_minutes: 2 }).use(async (session) => {
    console.log("Opening demo page to extract one-time setup credentials...");
    await printViewerUrl(session);
    await session.execute({ type: "goto", url: DEMO_URL });
    return session.scrape({
      instructions: "Extract the test email, password, and TOTP secret key shown on the page",
      response_format: Credentials,
    });
  });
}

async function fillAndSubmit(session: {
  observe: () => Promise<unknown>;
  execute: (action: unknown) => Promise<unknown>;
}) {
  await session.observe();
  await session.execute({
    type: "form_fill",
    value: {
      email: EMAIL_PLACEHOLDER,
      password: PASSWORD_PLACEHOLDER,
      totp: MFA_PLACEHOLDER,
    },
  });
  console.log("Filled email, password, and TOTP fields from the vault");

  await session.execute({
    type: "click",
    selector: 'input[type="submit"], button[type="submit"], form button',
  });
  console.log("Submitted form");
  await session.execute({ type: "wait", time_ms: 3000 });
}

async function main() {
  console.log("Starting MFA with Vaults...");

  const client = new NotteClient({ apiKey: process.env.NOTTE_API_KEY });
  const credentials = await extractDemoCredentials(client);
  const vault = client.Vault({ name: "MFA Vault Demo" });

  try {
    await vault.addCredentials(DEMO_URL, {
      email: credentials.email,
      password: credentials.password,
      mfa_secret: credentials.totp_secret,
    });
    console.log("Created an ephemeral vault with email, password, and TOTP secret");

    await client.Session({
      open_viewer: true,
      idle_timeout_minutes: 2,
      vault_id: vault.vaultId,
    }).use(async (session) => {
      console.log("Notte session initialized with ephemeral vault");
      await printViewerUrl(session);

      console.log("Navigating to TOTP Challenge page...");
      await session.execute({ type: "goto", url: DEMO_URL });

      console.log("Filling and submitting login form with vault placeholders...");
      await fillAndSubmit(session);

      console.log("Checking authentication result...");
      const result = await session.scrape({
        instructions: "Check if the login was successful or if there's an error message",
        response_format: AuthResult,
      });

      if (result.success) {
        console.log("SUCCESS! TOTP authentication completed automatically!");
        console.log(`Authentication Result: ${result.message}`);
        return;
      }

      console.log(`Authentication may have failed. Message: ${result.message}`);
      console.log("Retrying with a fresh vault-generated TOTP code...");
      await session.execute({ type: "goto", url: DEMO_URL });
      await fillAndSubmit(session);

      const retryResult = await session.scrape({
        instructions: "Check if the login was successful",
        response_format: AuthResult,
      });

      if (retryResult.success) {
        console.log("Success on retry!");
      } else {
        console.log("Authentication failed after retry");
      }
    });
  } finally {
    await vault.stop();
  }

  console.log("Session closed successfully");
}

main().catch((error: unknown) => {
  console.error(`Error in MFA handling: ${error instanceof Error ? error.message : String(error)}`);
  console.error("Common issues:");
  console.error("  - Check .env file has NOTTE_API_KEY");
  console.error("  - TOTP code may have expired; rerun so the vault generates a fresh one");
  console.error("  - Page structure may have changed");
  console.error("Docs: https://docs.notte.cc/");
  process.exit(1);
});
