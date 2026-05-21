import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { config as loadEnv } from "dotenv";
import { NotteClient } from "notte-sdk";
import { z } from "zod";

const __dirname = dirname(fileURLToPath(import.meta.url));
loadEnv({ path: join(__dirname, ".env") });
loadEnv({ path: join(__dirname, "..", ".env") });

const SEARCH_QUERY = "Browser automation";
const INFOBOX_TOPIC_URL = process.env.WIKIPEDIA_TOPIC_URL ?? "https://en.wikipedia.org/wiki/OpenAI";

const InfoboxField = z.object({
  label: z.string().nullable().default(null).describe("The label of the field in the infobox."),
  value: z.string().nullable().default(null).describe("The value associated with the field."),
});

const WikipediaInfobox = z.object({
  title: z.string().nullable().default(null).describe("The main title of the Wikipedia article."),
  description: z
    .string()
    .nullable()
    .default(null)
    .describe("A brief description of the article subject, usually the first paragraph."),
  fields: z
    .array(InfoboxField)
    .default([])
    .describe("A list of key-value pairs from the right-hand infobox."),
});

function validateWikipediaArticleUrl(topicUrl: string): string {
  const parsed = new URL(topicUrl);

  if (!["http:", "https:"].includes(parsed.protocol)) {
    throw new Error("WIKIPEDIA_TOPIC_URL must start with http:// or https://");
  }

  if (!parsed.hostname.endsWith("wikipedia.org")) {
    throw new Error("WIKIPEDIA_TOPIC_URL must point to wikipedia.org");
  }

  if (!parsed.pathname.startsWith("/wiki/")) {
    throw new Error("WIKIPEDIA_TOPIC_URL must point to a /wiki/ article");
  }

  return topicUrl;
}

async function printViewerUrl(session: { status: () => Promise<{ viewer_url?: string | null }> }) {
  const status = await session.status();
  if (status.viewer_url) {
    console.log(`Live view: ${status.viewer_url}`);
  }
}

async function demoStructuredInfobox(client: NotteClient) {
  console.log(`\n${"=".repeat(50)}`);
  console.log("4. STRUCTURED INFOBOX SCRAPE");
  console.log("=".repeat(50));

  const topicUrl = validateWikipediaArticleUrl(INFOBOX_TOPIC_URL);
  const instructions =
    "Extract the Wikipedia article title and the key/value rows from the right-hand " +
    "infobox only. Return JSON with title, description, and fields where each field " +
    "has label and value text. Do not include article body, references, navigation, " +
    "or unrelated page chrome.";

  await client.Session({ idle_timeout_minutes: 2, use_file_storage: true }).use(async (session) => {
    console.log(`Session ID: ${session.getId()}`);
    await printViewerUrl(session);
    console.log(`Opening ${topicUrl}`);

    await session.execute({ type: "goto", url: topicUrl });
    await session.execute({ type: "scroll_down" });
    await session.execute({ type: "scroll_up" });

    const result = await session.scrape({
      instructions,
      only_main_content: false,
      only_images: false,
      scrape_links: false,
      scrape_images: false,
      response_format: WikipediaInfobox,
    });

    console.log("\nInfobox JSON:");
    console.log(JSON.stringify(result, null, 2));
  });
}

async function main() {
  console.log("=".repeat(50));
  console.log("GETTING STARTED WITH NOTTE");
  console.log("=".repeat(50));
  console.log(`Demos: ${SEARCH_QUERY} lookup context, browser sessions, and structured scraping\n`);

  const apiKey = process.env.NOTTE_API_KEY;
  if (!apiKey) {
    throw new Error("Missing NOTTE_API_KEY. Set it in your environment or .env file.");
  }

  const client = new NotteClient({ apiKey });
  await demoStructuredInfobox(client);

  console.log(`\n${"=".repeat(50)}`);
  console.log("ALL DEMOS COMPLETE!");
  console.log("=".repeat(50));
}

main().catch((error: unknown) => {
  console.error(`Error: ${error instanceof Error ? error.message : String(error)}`);
  console.error("\nTroubleshooting:");
  console.error("  1. Check your .env file has NOTTE_API_KEY");
  console.error("  2. Verify internet connectivity and that the target sites are reachable");
  console.error("Docs: https://docs.notte.cc/");
  process.exit(1);
});
