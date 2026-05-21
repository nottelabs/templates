import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { config as loadEnv } from "dotenv";
import { NotteClient } from "notte-sdk";
import { z } from "zod";

const __dirname = dirname(fileURLToPath(import.meta.url));
loadEnv({ path: join(__dirname, ".env") });
loadEnv({ path: join(__dirname, "..", ".env") });

const SEARCH_QUERY = process.env.SEARCH_QUERY ?? "portable espresso maker travel";

const MonitorCandidate = z.object({
  title: z.string().nullable().default(null).describe("The full product title shown in search results"),
  current_price: z.string().nullable().default(null).describe("The visible current price, including currency symbol"),
  list_price: z.string().nullable().default(null).describe("The crossed-out list price or typical price, if shown"),
  deal_or_coupon: z.string().nullable().default(null).describe("Any deal badge, coupon, or savings message"),
  delivery_promise: z.string().nullable().default(null).describe("Prime, shipping speed, or delivery promise text"),
  purchase_context: z.string().nullable().default(null).describe("Short note such as bundle, pack size, or variant info"),
  product_url: z.string().nullable().default(null).describe("The URL link to the product detail page"),
});

const MonitoringSnapshot = z.object({
  search_intent: z.string().nullable().default(null).describe("Brief summary of what the search results are for"),
  candidates: z
    .array(MonitorCandidate)
    .default([])
    .describe("Up to 5 non-sponsored product candidates with pricing and delivery signals"),
});

async function printViewerUrl(session: { status: () => Promise<{ viewer_url?: string | null }> }) {
  const status = await session.status();
  if (status.viewer_url) {
    console.log(`Live View Link: ${status.viewer_url}`);
  }
}

async function main() {
  console.log("Starting Amazon Product Scraping...");

  const apiKey = process.env.NOTTE_API_KEY;
  if (!apiKey) {
    throw new Error("Missing NOTTE_API_KEY. Set it in your environment or .env file.");
  }

  const client = new NotteClient({ apiKey });
  const searchUrl = `https://www.amazon.com/s?k=${encodeURIComponent(SEARCH_QUERY).replace(/%20/g, "+")}`;

  await client
    .Session({
      idle_timeout_minutes: 2,
      proxies: true,
      solve_captchas: true,
    })
    .use(async (session) => {
      console.log("Notte session initialized successfully");
      console.log(`Session ID: ${session.getId()}`);
      await printViewerUrl(session);

      console.log(`Navigating to: ${searchUrl}`);
      await session.execute({ type: "goto", url: searchUrl });
      await session.execute({ type: "wait", time_ms: 4000 });

      console.log("Extracting price-monitoring signals...");
      const snapshot = await session.scrape({
        instructions:
          "Build a price-monitoring snapshot from the organic Amazon search results. " +
          "Find up to 5 relevant non-sponsored product candidates for the search intent. " +
          "For each candidate, extract the title, current price, any crossed-out list price " +
          "or typical price, visible deal or coupon text, Prime/shipping/delivery promise, " +
          "a short purchase-context note such as bundle, pack size, or variant, and the " +
          "product page URL. Ignore ratings, review counts, sponsored placements, banners, " +
          "navigation, filters, and ads.",
        response_format: MonitoringSnapshot,
      });

      console.log("Monitoring snapshot:");
      console.log(JSON.stringify(snapshot, null, 2));
    });

  console.log("Session closed successfully");
}

main().catch((error: unknown) => {
  console.error(`Error in Amazon product scraping: ${error instanceof Error ? error.message : String(error)}`);
  console.error("Common issues:");
  console.error("  - Check .env has NOTTE_API_KEY");
  console.error("  - Amazon may show bot checks or vary layout by region");
  console.error("Docs: https://docs.notte.cc/");
  process.exit(1);
});
