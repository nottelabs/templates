import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { config as loadEnv } from "dotenv";
import { NotteClient } from "notte-sdk";
import { z } from "zod";

const __dirname = dirname(fileURLToPath(import.meta.url));
loadEnv({ path: join(__dirname, ".env") });
loadEnv({ path: join(__dirname, "..", ".env") });

const BASE_URL = process.env.BASE_URL ?? "https://quotes.toscrape.com/";
const MAX_PAGES = Number.parseInt(process.env.MAX_PAGES ?? "2", 10);
const MAX_AUTHORS = Number.parseInt(process.env.MAX_AUTHORS ?? "10", 10);
const INCLUDE_AUTHOR_PROFILES = !["0", "false", "no"].includes(
  (process.env.INCLUDE_AUTHOR_PROFILES ?? "true").toLowerCase(),
);

const QuotePageItem = z.object({
  text: z.string().describe("Quote text"),
  author: z.string().describe("Quote author"),
  author_path: z.string().describe("Relative or absolute author profile URL"),
  tags: z.array(z.string()).default([]).describe("Quote tags"),
});

const QuotePage = z.object({
  current_url: z.string().nullable().default(null),
  next_path: z.string().nullable().default(null).describe("Relative or absolute URL for the next quote page"),
  quotes: z.array(QuotePageItem).default([]),
});

const AuthorProfile = z.object({
  name: z.string(),
  born_date: z.string(),
  born_location: z.string(),
  description: z.string(),
  url: z.string(),
});

type QuotePage = z.infer<typeof QuotePage>;
type AuthorProfile = z.infer<typeof AuthorProfile>;

type Quote = {
  text: string;
  author: string;
  author_url: string;
  tags: string[];
  source_url: string;
};

function validatePositiveInt(name: string, value: number) {
  if (!Number.isFinite(value) || value < 1) {
    throw new Error(`${name} must be at least 1`);
  }
}

async function printViewerUrl(session: { status: () => Promise<{ viewer_url?: string | null }> }) {
  const status = await session.status();
  if (status.viewer_url) {
    console.log(`Live view: ${status.viewer_url}`);
  }
}

async function scrapeQuotePage(
  session: {
    execute: (action: unknown) => Promise<unknown>;
    scrape: <T>(options: { instructions: string; response_format: z.ZodSchema<T>; only_main_content?: boolean; scrape_links?: boolean }) => Promise<T>;
  },
  pageUrl: string,
): Promise<QuotePage> {
  await session.execute({ type: "goto", url: pageUrl });
  await session.execute({ type: "wait", time_ms: 1000 });

  return session.scrape({
    instructions:
      "Extract all visible quotes on this Quotes to Scrape listing page. For each quote, " +
      "return text, author, author_path from the author profile link, and tags. Also return " +
      "current_url and next_path from the pagination next link if one is visible.",
    only_main_content: true,
    scrape_links: true,
    response_format: QuotePage,
  });
}

async function collectQuotePages(
  session: {
    execute: (action: unknown) => Promise<unknown>;
    scrape: <T>(options: { instructions: string; response_format: z.ZodSchema<T>; only_main_content?: boolean; scrape_links?: boolean }) => Promise<T>;
  },
  baseUrl: string,
  maxPages: number,
): Promise<{ quotes: Quote[]; pagesScraped: number }> {
  const quotes: Quote[] = [];
  let currentUrl = baseUrl;

  for (let pageNumber = 1; pageNumber <= maxPages; pageNumber += 1) {
    console.log(`Loading quote page ${pageNumber}: ${currentUrl}`);
    const pageData = await scrapeQuotePage(session, currentUrl);
    const sourceUrl = pageData.current_url ?? currentUrl;
    const pageQuotes = pageData.quotes
      .filter((item) => item.text && item.author && item.author_path)
      .map((item) => ({
        text: item.text,
        author: item.author,
        author_url: new URL(item.author_path, baseUrl).toString(),
        tags: item.tags,
        source_url: sourceUrl,
      }));

    console.log(`  Found ${pageQuotes.length} quotes`);
    quotes.push(...pageQuotes);

    if (!pageData.next_path) {
      return { quotes, pagesScraped: pageNumber };
    }
    currentUrl = new URL(pageData.next_path, sourceUrl).toString();
  }

  return { quotes, pagesScraped: maxPages };
}

async function collectAuthorProfiles(
  session: {
    execute: (action: unknown) => Promise<unknown>;
    scrape: <T>(options: { instructions: string; response_format: z.ZodSchema<T>; only_main_content?: boolean; scrape_links?: boolean }) => Promise<T>;
  },
  quotes: Quote[],
  maxAuthors: number,
): Promise<AuthorProfile[]> {
  const authorUrls = new Map<string, string>();
  for (const quote of quotes) {
    if (!authorUrls.has(quote.author)) {
      authorUrls.set(quote.author, quote.author_url);
    }
  }

  const profiles: AuthorProfile[] = [];
  for (const [authorName, authorUrl] of [...authorUrls.entries()].slice(0, maxAuthors)) {
    console.log(`Loading author profile: ${authorName}`);
    await session.execute({ type: "goto", url: authorUrl });
    await session.execute({ type: "wait", time_ms: 800 });
    const profile = await session.scrape({
      instructions:
        "Extract the author profile from this Quotes to Scrape page. Return name, born_date, " +
        "born_location, description, and the current profile URL.",
      only_main_content: true,
      scrape_links: true,
      response_format: AuthorProfile,
    });
    profiles.push({ ...profile, url: profile.url || authorUrl });
  }

  return profiles;
}

async function main() {
  console.log("Starting Quotes Author Scraper...");
  validatePositiveInt("MAX_PAGES", MAX_PAGES);
  validatePositiveInt("MAX_AUTHORS", MAX_AUTHORS);

  const apiKey = process.env.NOTTE_API_KEY;
  if (!apiKey) {
    throw new Error("Missing NOTTE_API_KEY. Set it in your environment or .env file.");
  }

  const client = new NotteClient({ apiKey });

  const result = await client.Session({ open_viewer: true, idle_timeout_minutes: 2 }).use(async (session) => {
    console.log(`Session ID: ${session.getId()}`);
    await printViewerUrl(session);

    const { quotes, pagesScraped } = await collectQuotePages(session, BASE_URL, MAX_PAGES);
    const authors = INCLUDE_AUTHOR_PROFILES
      ? await collectAuthorProfiles(session, quotes, MAX_AUTHORS)
      : [];

    return {
      base_url: BASE_URL,
      pages_scraped: pagesScraped,
      quote_count: quotes.length,
      author_count: authors.length,
      quotes,
      authors,
    };
  });

  console.log("\nFINAL RESULT");
  console.log(JSON.stringify(result, null, 2));
  console.log("\nScript completed successfully");
}

main().catch((error: unknown) => {
  console.error(`Application error: ${error instanceof Error ? error.message : String(error)}`);
  console.error("Common issues:");
  console.error("  - Check .env has NOTTE_API_KEY set");
  console.error("  - Ensure BASE_URL points to a Quotes to Scrape-compatible site");
  console.error("  - Lower MAX_PAGES or MAX_AUTHORS if you only need a quick sample");
  process.exit(1);
});
