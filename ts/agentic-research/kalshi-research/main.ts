import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { config as loadEnv } from "dotenv";
import { NotteClient } from "notte-sdk";
import { z } from "zod";

const __dirname = dirname(fileURLToPath(import.meta.url));
loadEnv({ path: join(__dirname, ".env") });
loadEnv({ path: join(__dirname, "..", ".env") });

const SEARCH_QUERY = process.env.SEARCH_QUERY ?? "lowest temperature in Los Angeles today";

const MarketData = z.object({
  marketTitle: z.string().nullable().default(null).describe("the title of the market"),
  currentOdds: z.string().nullable().default(null).describe("the current odds or probability"),
  yesPrice: z.string().nullable().default(null).describe("the yes price"),
  noPrice: z.string().nullable().default(null).describe("the no price"),
  totalVolume: z.string().nullable().default(null).describe("the total trading volume"),
  priceChange: z.string().nullable().default(null).describe("the recent price change"),
});

async function printViewerUrl(session: { status: () => Promise<{ viewer_url?: string | null }> }) {
  const status = await session.status();
  if (status.viewer_url) {
    console.log(`Watch live: ${status.viewer_url}`);
  }
}

async function main() {
  console.log("Starting Kalshi research automation...");

  const client = new NotteClient({ apiKey: process.env.NOTTE_API_KEY });

  await client.Session({
    idle_timeout_minutes: 2,
    proxies: true,
    solve_captchas: true,
  }).use(async (session) => {
    console.log("Notte session started successfully");
    console.log(`Session ID: ${session.getId()}`);
    await printViewerUrl(session);

    const agent = client.Agent({ session, max_steps: 25 });
    const result = await agent.run({
      url: "https://kalshi.com/",
      task:
        `Search Kalshi for "${SEARCH_QUERY}", open the most relevant market, ` +
        "and extract the current market title, odds or probability, yes price, " +
        "no price, total volume, and recent price change if visible.",
      response_format: MarketData,
    });

    if (result.answer === null || result.answer === undefined) {
      throw new Error("Agent did not return market data");
    }

    console.log("Market data extracted successfully:");
    console.log(JSON.stringify(result.answer, null, 2));
  });

  console.log("Session closed successfully");
}

main().catch((error: unknown) => {
  console.error(`Error in Kalshi research: ${error instanceof Error ? error.message : String(error)}`);
  console.error("Common issues:");
  console.error("  - Check .env has NOTTE_API_KEY");
  console.error("  - Ensure internet access and https://kalshi.com is accessible");
  console.error("  - The search query may not map to an active market");
  console.error("Docs: https://docs.notte.cc/");
  process.exit(1);
});
