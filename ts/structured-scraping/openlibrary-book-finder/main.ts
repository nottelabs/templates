import { writeFile } from "node:fs/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { config as loadEnv } from "dotenv";
import { NotteClient } from "notte-sdk";
import { z } from "zod";

const __dirname = dirname(fileURLToPath(import.meta.url));
loadEnv({ path: join(__dirname, ".env") });
loadEnv({ path: join(__dirname, "..", ".env") });

const OPENLIBRARY_HOME_URL = "https://openlibrary.org/";
const DEFAULT_QUERY = process.env.OPENLIBRARY_QUERY ?? "the hobbit";
const DEFAULT_MAX_RESULTS = Number.parseInt(process.env.OPENLIBRARY_MAX_RESULTS ?? "5", 10);

const BookResult = z.object({
  title: z.string().nullable().default(null).describe("Visible work title"),
  authors: z.array(z.string()).default([]).describe("Visible author names"),
  first_published_year: z.number().nullable().default(null).describe("First published year"),
  editions_count: z.number().nullable().default(null).describe("Number of editions shown"),
  ebook_count: z.number().nullable().default(null).describe("Number of ebooks shown"),
  availability_text: z.string().nullable().default(null).describe("Borrow, Preview Only, Locate, or similar"),
  rating_text: z.string().nullable().default(null).describe("Visible rating summary"),
  want_to_read_text: z.string().nullable().default(null).describe("Want-to-read count text"),
  work_url: z.string().nullable().default(null).describe("Open Library work URL"),
});

const SearchResults = z.object({
  search_query: z.string().nullable().default(null),
  total_hit_count: z.number().nullable().default(null),
  results: z.array(BookResult).default([]),
});

type SearchResults = z.infer<typeof SearchResults>;

function searchUrl(query: string): string {
  return new URL(`search?q=${encodeURIComponent(query).replace(/%20/g, "+")}`, OPENLIBRARY_HOME_URL).toString();
}

async function printViewerUrl(session: { status: () => Promise<{ viewer_url?: string | null }> }) {
  const status = await session.status();
  if (status.viewer_url) {
    console.log(`Live View: ${status.viewer_url}`);
  }
}

async function scrapeVisibleResults(
  session: {
    scrape: <T>(options: { instructions: string; response_format: z.ZodSchema<T>; only_main_content?: boolean; only_images?: boolean; scrape_links?: boolean; scrape_images?: boolean }) => Promise<T>;
  },
  query: string,
  maxResults: number,
): Promise<SearchResults> {
  return session.scrape({
    instructions:
      "Extract the visible Open Library book search results as structured JSON. " +
      `Use the search query ${JSON.stringify(query)}. Include the total hit count and the first ` +
      `${maxResults} results. For each result include title, authors as a list, ` +
      "first published year, editions count, ebook count, availability text such as " +
      "Borrow or Preview Only or Locate, rating text, want_to_read text, and work URL.",
    only_main_content: false,
    only_images: false,
    scrape_links: true,
    scrape_images: false,
    response_format: SearchResults,
  });
}

function normalizeResults(results: SearchResults, query: string, maxResults: number) {
  const books = results.results.slice(0, maxResults).map((result) => ({
    ...result,
    work_url: result.work_url ? new URL(result.work_url, OPENLIBRARY_HOME_URL).toString() : null,
  }));

  return {
    observed_at: new Date().toISOString(),
    search_query: results.search_query ?? query,
    search_url: searchUrl(query),
    total_hit_count: results.total_hit_count,
    returned_count: books.length,
    books,
  };
}

async function run(query = DEFAULT_QUERY, maxResults = DEFAULT_MAX_RESULTS) {
  const apiKey = process.env.NOTTE_API_KEY;
  if (!apiKey) {
    throw new Error("Missing NOTTE_API_KEY. Set it in your environment or .env file.");
  }

  const client = new NotteClient({ apiKey });

  return client.Session({ browser_type: "chrome", open_viewer: true, idle_timeout_minutes: 3 }).use(async (session) => {
    console.log(`Session ID: ${session.getId()}`);
    await printViewerUrl(session);

    const url = searchUrl(query);
    console.log(`Searching Open Library for: ${query}`);
    await session.execute({ type: "goto", url });
    await session.execute({ type: "wait", time_ms: 1500 });

    const results = await scrapeVisibleResults(session, query, maxResults);
    return normalizeResults(results, query, maxResults);
  });
}

async function main() {
  const query = process.argv[2] ?? DEFAULT_QUERY;
  const maxResults = process.argv[3] ? Number.parseInt(process.argv[3], 10) : DEFAULT_MAX_RESULTS;
  const report = await run(query, maxResults);

  if (process.env.OPENLIBRARY_OUTPUT_PATH) {
    await writeFile(process.env.OPENLIBRARY_OUTPUT_PATH, JSON.stringify(report, null, 2), "utf8");
  }

  console.log(JSON.stringify(report, null, 2));
}

main().catch((error: unknown) => {
  console.error(`Error: ${error instanceof Error ? error.message : String(error)}`);
  console.error("Troubleshooting:");
  console.error("  - Set NOTTE_API_KEY in your environment or .env file");
  console.error("  - Try a simpler query, for example: npm start -- hobbit");
  process.exit(1);
});
