import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { config as loadEnv } from "dotenv";
import { NotteClient } from "notte-sdk";
import { z } from "zod";

const __dirname = dirname(fileURLToPath(import.meta.url));
loadEnv({ path: join(__dirname, ".env") });
loadEnv({ path: join(__dirname, "..", ".env") });

const DEMO_URL = "https://nopecha.com/captcha/recaptcha#easy";
const SOLVE_CAPTCHAS = process.env.SOLVE_CAPTCHAS !== "false";
const MAX_CAPTCHA_SOLVE_ATTEMPTS = 3;

const PageText = z.object({
  text: z.string().describe("All visible text on the page."),
});

async function printViewerUrl(session: { status: () => Promise<{ viewer_url?: string | null }> }) {
  const status = await session.status();
  if (status.viewer_url) {
    console.log(`Live View Link: ${status.viewer_url}`);
  }
}

async function solveRecaptchaWithRetries(
  session: { execute: (action: Record<string, unknown>, raiseOnFailure?: boolean) => Promise<{ success?: boolean; message?: string | null }> },
  maxAttempts = MAX_CAPTCHA_SOLVE_ATTEMPTS,
) {
  let lastMessage = "captcha solve did not run";

  for (let attempt = 1; attempt <= maxAttempts; attempt += 1) {
    console.log(`Solving captcha, attempt ${attempt}/${maxAttempts}...`);
    const result = await session.execute(
      { type: "captcha_solve", captcha_type: "recaptcha" },
      false,
    );
    lastMessage = result.message ?? JSON.stringify(result);

    if (result.success) {
      console.log("Captcha solve action succeeded");
      return;
    }

    console.log(`Captcha solve action failed: ${lastMessage}`);
    if (attempt < maxAttempts) {
      await session.execute({ type: "wait", time_ms: 3000 });
    }
  }

  throw new Error(`Failed to solve captcha after ${maxAttempts} attempts: ${lastMessage}`);
}

async function main() {
  const apiKey = process.env.NOTTE_API_KEY;
  if (!apiKey) {
    throw new Error("Missing NOTTE_API_KEY. Set it in your environment or .env file.");
  }

  const client = new NotteClient({ apiKey });

  await client.Session({
    open_viewer: true,
    idle_timeout_minutes: 2,
    solve_captchas: SOLVE_CAPTCHAS,
    proxies: false,
    viewport_height: 320,
    viewport_width: 640,
  }).use(async (session) => {
    console.log("Notte session initialized successfully");
    console.log(`Session ID: ${session.getId()}`);
    await printViewerUrl(session);

    console.log("Navigating to reCAPTCHA demo page...");
    await session.execute({ type: "goto", url: DEMO_URL });

    if (SOLVE_CAPTCHAS) {
      await solveRecaptchaWithRetries(session);
    } else {
      console.log("Captcha solving is disabled. Skipping solve action...");
    }

    console.log("Waiting for the demo page to receive the solved token callback...");
    await session.execute({ type: "wait", time_ms: 2000 });

    console.log("Extracting page content...");
    const extracted = await session.scrape({
      instructions: "Extract all visible text on this page.",
      response_format: PageText,
    });

    console.log("Page content:");
    console.log(extracted.text);

    const pageText = extracted.text.toLowerCase();
    const successMarkers = ['"success":true', "'success': true", "success"];
    if (successMarkers.some((marker) => pageText.includes(marker))) {
      console.log("reCAPTCHA successfully solved!");
    } else {
      console.log("Could not verify captcha success from page content");
    }
  });

  console.log("Session closed successfully");
}

main().catch((error: unknown) => {
  console.error(`Error in reCAPTCHA solving example: ${error instanceof Error ? error.message : String(error)}`);
  console.error("Common issues:");
  console.error("  - Check .env has NOTTE_API_KEY");
  console.error("  - Verify captcha solving is enabled for your Notte account");
  console.error("  - Ensure the demo page is accessible");
  console.error("Docs: https://docs.notte.cc/");
  process.exit(1);
});
