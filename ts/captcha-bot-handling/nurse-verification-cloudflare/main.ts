import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { config as loadEnv } from "dotenv";
import { NotteClient } from "notte-sdk";
import { z } from "zod";

const __dirname = dirname(fileURLToPath(import.meta.url));
loadEnv({ path: join(__dirname, ".env") });
loadEnv({ path: join(__dirname, "..", ".env") });

const LicenseRecord = z.object({
  name: z.string().nullable().default(null).describe("The name of the license holder."),
  license_number: z.string().nullable().default(null).describe("The license number."),
  status: z.string().nullable().default(null).describe("The status of the license."),
  more_info_url: z.string().nullable().default(null).describe("URL for more information."),
});

const LicenseResults = z.object({
  list_of_licenses: z
    .array(LicenseRecord)
    .default([])
    .describe("Array of license verification results."),
});

const LICENSE_RECORDS = [
  {
    site: "https://pod-search.kalmservices.net/",
    firstName: "Angelo",
    lastName: "Agee",
    licenseNumber: "91",
  },
];

async function printViewerUrl(session: { status: () => Promise<{ viewer_url?: string | null }> }) {
  const status = await session.status();
  if (status.viewer_url) {
    console.log(`Watch live: ${status.viewer_url}`);
  }
}

async function attemptCloudflareSolve(session: {
  execute: (action: Record<string, unknown>, raiseOnFailure?: boolean) => Promise<{ success?: boolean; message?: string | null }>;
}) {
  try {
    const result = await session.execute(
      { type: "captcha_solve", captcha_type: "cloudflare" },
      false,
    );
    if (result.success) {
      console.log("Cloudflare solve action succeeded");
    } else {
      console.log(`Cloudflare solve action did not complete: ${result.message ?? "unknown result"}`);
    }
  } catch (error) {
    console.log(`Captcha solve step did not complete: ${error instanceof Error ? error.message : String(error)}`);
  }
}

async function main() {
  console.log("Starting License Verification Automation...");

  const apiKey = process.env.NOTTE_API_KEY;
  if (!apiKey) {
    throw new Error("Missing NOTTE_API_KEY. Set it in your environment or .env file.");
  }

  const client = new NotteClient({ apiKey });

  await client.Session({
    idle_timeout_minutes: 2,
    solve_captchas: true,
    proxies: true,
  }).use(async (session) => {
    console.log("Notte session started successfully");
    console.log(`Session ID: ${session.getId()}`);
    await printViewerUrl(session);

    for (const licenseRecord of LICENSE_RECORDS) {
      console.log(`Verifying license for: ${licenseRecord.firstName} ${licenseRecord.lastName}`);
      console.log(`Navigating to: ${licenseRecord.site}`);
      await session.execute({ type: "goto", url: licenseRecord.site });
      await session.execute({ type: "wait", time_ms: 1000 });

      console.log("Filling in license information...");
      await session.execute({
        type: "fill",
        selector: "input >> nth=0",
        value: licenseRecord.firstName,
        clear_before_fill: true,
      });
      await session.execute({ type: "wait", time_ms: 1000 });
      await session.execute({
        type: "fill",
        selector: "input >> nth=1",
        value: licenseRecord.lastName,
        clear_before_fill: true,
      });
      await session.execute({ type: "wait", time_ms: 1000 });
      await session.execute({
        type: "fill",
        selector: "input >> nth=3",
        value: licenseRecord.licenseNumber,
        clear_before_fill: true,
      });

      console.log("Clicking search button...");
      await session.execute({ type: "click", selector: 'internal:role=button[name="Search"i]' });
      await session.execute({ type: "wait", time_ms: 6000 });

      await attemptCloudflareSolve(session);

      console.log("Extracting license verification results...");
      let extracted: z.infer<typeof LicenseResults>;
      try {
        extracted = await session.scrape({
          instructions:
            "Extract all license verification results from the page, including name, " +
            "license number, status, and more info URL if present.",
          response_format: LicenseResults,
        });
      } catch (error) {
        console.log(`No extractable license results found: ${error instanceof Error ? error.message : String(error)}`);
        extracted = { list_of_licenses: [] };
      }

      console.log("License verification results extracted:");
      console.log(JSON.stringify(extracted, null, 2));
    }
  });

  console.log("Session closed successfully");
}

main().catch((error: unknown) => {
  console.error(`Application error: ${error instanceof Error ? error.message : String(error)}`);
  console.error("Common issues:");
  console.error("  - Check .env has NOTTE_API_KEY");
  console.error("  - The license site may require captcha solving");
  console.error("Docs: https://docs.notte.cc/");
  process.exit(1);
});
