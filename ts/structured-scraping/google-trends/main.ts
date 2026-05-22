import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { config as loadEnv } from "dotenv";
import { NotteClient } from "notte-sdk";
import { z } from "zod";

const __dirname = dirname(fileURLToPath(import.meta.url));
loadEnv({ path: join(__dirname, ".env") });
loadEnv({ path: join(__dirname, "..", ".env") });

const countryCodes = ["US", "GB"];
const storiesPerRegion = 5;
const language = "en-US";

const TrendStory = z.object({
  topic: z.string().describe("Main trend topic or story cluster"),
  search_volume: z.string().nullable().default(null).describe("Visible search volume for the trend, such as 200K+"),
  started: z.string().nullable().default(null).describe("Visible start time or freshness label for the trend"),
  related_queries: z.array(z.string()).default([]).describe("Related queries, breakdown terms, or variants shown with this trend"),
  news_headlines: z.array(z.string()).default([]).describe("Visible news headlines connected to this trend"),
});

const RegionalBriefing = z.object({
  stories: z.array(TrendStory).default([]).describe("Brief story clusters extracted from Google Trends"),
});

type RegionalBriefing = z.infer<typeof RegionalBriefing>;

async function printViewerUrl(session: { status: () => Promise<{ viewer_url?: string | null }> }) {
  const status = await session.status();
  if (status.viewer_url) {
    console.log(`Watch live: ${status.viewer_url}`);
  }
}

async function scrapeRegion(
  session: {
    execute: (action: unknown, raiseOnFailure?: boolean) => Promise<unknown>;
    scrape: <T>(options: { instructions: string; response_format: z.ZodSchema<T> }) => Promise<T>;
  },
  countryCode: string,
): Promise<RegionalBriefing> {
  const trendsUrl = `https://trends.google.com/trending?geo=${countryCode.toUpperCase()}&hl=${language}`;
  console.log(`Navigating to: ${trendsUrl}`);
  await session.execute({ type: "goto", url: trendsUrl });
  await session.execute({ type: "wait", time_ms: 2500 });

  console.log("Checking for consent dialogs...");
  await session.execute(
    {
      type: "click",
      selector: 'button:has-text("Got it")',
      timeout: 5000,
    },
    false,
  );
  await session.execute({ type: "wait", time_ms: 1500 });

  console.log(`Building briefing for ${countryCode.toUpperCase()}...`);
  return session.scrape({
    instructions:
      "Create a compact editorial briefing from the visible Google Trends page. " +
      "Do not transcribe the full trending table. Instead, group the most prominent " +
      `visible trends into up to ${storiesPerRegion} story clusters. For each ` +
      "cluster, capture the main topic, visible search volume, visible start time, " +
      "related queries or breakdown terms if shown, and any visible connected news " +
      "headlines. Leave fields empty or null when the page does not show them.",
    response_format: RegionalBriefing,
  });
}

function compareTopics(regionalResults: Record<string, RegionalBriefing>) {
  const topicSets = Object.values(regionalResults).map((briefing) =>
    new Set(briefing.stories.map((story) => story.topic.trim().toLowerCase()).filter(Boolean)),
  );

  if (topicSets.length < 2) {
    return { shared_topics: [] };
  }

  const sharedTopics = [...topicSets[0]].filter((topic) =>
    topicSets.every((topicSet) => topicSet.has(topic)),
  );
  return { shared_topics: sharedTopics.sort() };
}

async function main() {
  console.log("Starting Google Trends Regional Briefing...");
  console.log(`Country Codes: ${countryCodes.join(", ")}`);
  console.log(`Language: ${language}`);
  console.log(`Stories per region: ${storiesPerRegion}`);

  const apiKey = process.env.NOTTE_API_KEY;
  if (!apiKey) {
    throw new Error("Missing NOTTE_API_KEY. Set it in your environment or .env file.");
  }

  const client = new NotteClient({ apiKey });

  await client.Session({
    open_viewer: true,
    idle_timeout_minutes: 2,
    max_duration_minutes: 15,
    solve_captchas: true,
  }).use(async (session) => {
    console.log("Notte session started");
    console.log(`Session ID: ${session.getId()}`);
    await printViewerUrl(session);

    const regionalResults: Record<string, RegionalBriefing> = {};
    for (const countryCode of countryCodes) {
      regionalResults[countryCode.toUpperCase()] = await scrapeRegion(session, countryCode);
    }

    const result = {
      country_codes: countryCodes.map((countryCode) => countryCode.toUpperCase()),
      language,
      extracted_at: new Date().toISOString(),
      regional_briefings: regionalResults,
      comparison: compareTopics(regionalResults),
    };

    console.log("\n=== Results ===");
    console.log(JSON.stringify(result, null, 2));
  });

  console.log("Session closed successfully");
}

main().catch((error: unknown) => {
  console.error(`Application error: ${error instanceof Error ? error.message : String(error)}`);
  console.error("Common issues:");
  console.error("  - Check .env has NOTTE_API_KEY");
  console.error("  - Ensure country codes are valid 2-letter ISO codes (US, GB, IN, etc.)");
  console.error("  - Check if Google Trends page structure has changed");
  process.exit(1);
});
