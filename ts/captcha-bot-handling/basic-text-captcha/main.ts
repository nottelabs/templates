import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { config as loadEnv } from "dotenv";
import { NotteClient } from "notte-sdk";
import { z } from "zod";

const __dirname = dirname(fileURLToPath(import.meta.url));
loadEnv({ path: join(__dirname, ".env") });
loadEnv({ path: join(__dirname, "..", ".env") });

const DEMO_URL = "https://captcha.com/demos/features/captcha-demo.aspx#";
const VALIDATE_SELECTOR = 'internal:role=button[name="Validate"i]';
const RESULT_SELECTOR =
  "xpath=/html[1]/body[1]/div[1]/div[1]/div[1]/form[1]/fieldset[1]/div[2]/span[1]/span[1]";
const SOLVE_CAPTCHAS = process.env.SOLVE_CAPTCHAS !== "false";
const MAX_CAPTCHA_SOLVE_ATTEMPTS = 3;

const ValidationResult = z.object({
  result_text: z.string().describe("The CAPTCHA validation result message shown on the page."),
});

async function printViewerUrl(session: { status: () => Promise<{ viewer_url?: string | null }> }) {
  const status = await session.status();
  if (status.viewer_url) {
    console.log(`Live View Link: ${status.viewer_url}`);
  }
}

async function solveTextCaptchaWithRetries(
  session: { execute: (action: Record<string, unknown>, raiseOnFailure?: boolean) => Promise<{ success?: boolean; message?: string | null }> },
  maxAttempts = MAX_CAPTCHA_SOLVE_ATTEMPTS,
) {
  let lastMessage = "captcha solve did not run";

  for (let attempt = 1; attempt <= maxAttempts; attempt += 1) {
    console.log(`Solving text captcha, attempt ${attempt}/${maxAttempts}...`);
    const result = await session.execute({ type: "captcha_solve", captcha_type: "text" }, false);
    lastMessage = result.message ?? JSON.stringify(result);

    if (result.success) {
      console.log("Text captcha solve action succeeded");
      return;
    }

    console.log(`Text captcha solve action failed: ${lastMessage}`);
    if (attempt < maxAttempts) {
      await session.execute({ type: "wait", time_ms: 3000 });
    }
  }

  throw new Error(`Failed to solve text captcha after ${maxAttempts} attempts: ${lastMessage}`);
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
    proxies: true,
    viewport_width: 720,
    viewport_height: 640,
  }).use(async (session) => {
    console.log("Notte session initialized successfully");
    console.log(`Session ID: ${session.getId()}`);
    await printViewerUrl(session);

    console.log("Navigating to text CAPTCHA demo page...");
    await session.execute({ type: "goto", url: DEMO_URL });

    if (SOLVE_CAPTCHAS) {
      await solveTextCaptchaWithRetries(session);
    } else {
      console.log("Captcha solving is disabled. Skipping solve action...");
    }

    console.log("Clicking Validate button after captcha solve step...");
    await session.execute({ type: "click", selector: VALIDATE_SELECTOR });

    console.log("Scraping validation result...");
    const data = await session.scrape({
      instructions: "Extract only the CAPTCHA validation result message from the selected element.",
      only_main_content: false,
      use_link_placeholders: false,
      selector: RESULT_SELECTOR,
      response_format: ValidationResult,
    });

    const resultText = data.result_text.trim();
    console.log("Validation result:");
    console.log(resultText);

    if (resultText.includes("Correct!")) {
      console.log("Text CAPTCHA successfully solved!");
    } else if (resultText.includes("Incorrect!")) {
      throw new Error("Text CAPTCHA validation failed: Incorrect!");
    } else {
      throw new Error(`Could not verify text CAPTCHA result from scraped content: ${resultText}`);
    }
  });

  console.log("Session closed successfully");
}

main().catch((error: unknown) => {
  console.error(`Error in text CAPTCHA solving example: ${error instanceof Error ? error.message : String(error)}`);
  console.error("Common issues:");
  console.error("  - Check .env has NOTTE_API_KEY");
  console.error("  - Verify captcha solving and proxy access are enabled for your Notte account");
  console.error("  - Ensure the demo page is accessible");
  console.error("Docs: https://docs.notte.cc/");
  process.exit(1);
});
