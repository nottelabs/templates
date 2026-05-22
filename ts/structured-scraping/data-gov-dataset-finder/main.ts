import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { config as loadEnv } from "dotenv";
import { NotteClient } from "notte-sdk";
import { z } from "zod";

const __dirname = dirname(fileURLToPath(import.meta.url));
loadEnv({ path: join(__dirname, ".env") });
loadEnv({ path: join(__dirname, "..", ".env") });

const DATA_GOV_BASE_URL = "https://catalog.data.gov";

const DatasetSearchResult = z.object({
  rank: z.number().nullable().default(null).describe("Visible rank on the search results page."),
  title: z.string().nullable().default(null).describe("Dataset title."),
  url: z.string().nullable().default(null).describe("Dataset detail URL, absolute or relative."),
  organization: z.string().nullable().default(null).describe("Publishing organization."),
  last_updated_date: z.string().nullable().default(null).describe("Visible last updated date."),
  description_summary: z.string().nullable().default(null).describe("Short result-card description."),
  formats: z.array(z.string()).default([]).describe("Visible file/API formats."),
  relevance_text: z.string().nullable().default(null).describe("Visible search relevance score."),
  views_text: z.string().nullable().default(null).describe("Visible monthly views count."),
});

const SearchResults = z.object({
  search_query: z.string().nullable().default(null),
  result_count_text: z.string().nullable().default(null),
  current_url: z.string().nullable().default(null),
  sort_option: z.string().nullable().default(null),
  datasets: z.array(DatasetSearchResult).default([]),
});

const DatasetResource = z.object({
  name: z.string().nullable().default(null),
  format: z.string().nullable().default(null),
  url: z.string().nullable().default(null),
});

const DatasetDetail = z.object({
  title: z.string().nullable().default(null),
  organization: z.string().nullable().default(null),
  description: z.string().nullable().default(null),
  last_updated: z.string().nullable().default(null),
  homepage_source_link: z.string().nullable().default(null),
  license: z.string().nullable().default(null),
  metadata_fields: z.record(z.string(), z.unknown()).nullable().default(null),
  resources: z.array(DatasetResource).nullable().default(null),
});

type DatasetSearchResult = z.infer<typeof DatasetSearchResult>;
type SearchResults = z.infer<typeof SearchResults>;
type DatasetDetail = z.infer<typeof DatasetDetail>;

function parseArgs() {
  const args = process.argv.slice(2);
  const config = {
    query: process.env.DATA_GOV_QUERY ?? "climate",
    limit: Number.parseInt(process.env.DATA_GOV_RESULT_LIMIT ?? "5", 10),
  };

  for (let index = 0; index < args.length; index += 1) {
    const arg = args[index];
    if (arg === "--query" && args[index + 1]) {
      config.query = args[++index];
    } else if (arg === "--limit" && args[index + 1]) {
      config.limit = Number.parseInt(args[++index], 10);
    }
  }

  if (!Number.isFinite(config.limit) || config.limit < 1) {
    throw new Error("Limit must be at least 1.");
  }

  return { ...config, limit: Math.min(config.limit, 20) };
}

function dataGovSearchUrl(query: string): string {
  const cleanQuery = query.trim();
  if (!cleanQuery) {
    throw new Error("Search query cannot be empty.");
  }
  return `${DATA_GOV_BASE_URL}/?q=${encodeURIComponent(cleanQuery).replace(/%20/g, "+")}`;
}

function absoluteDataGovUrl(url: string | null): string | null {
  return url ? new URL(url, DATA_GOV_BASE_URL).toString() : null;
}

async function printViewerUrl(session: { status: () => Promise<{ viewer_url?: string | null }> }) {
  const status = await session.status();
  if (status.viewer_url) {
    console.log(`Live View: ${status.viewer_url}`);
  }
}

async function scrapeSearchResults(
  session: {
    execute: (action: unknown) => Promise<unknown>;
    scrape: <T>(options: { instructions: string; response_format: z.ZodSchema<T>; only_main_content?: boolean; only_images?: boolean; scrape_links?: boolean; scrape_images?: boolean }) => Promise<T>;
  },
  query: string,
  limit: number,
): Promise<SearchResults> {
  const searchUrl = dataGovSearchUrl(query);
  console.log(`Opening Data.gov search: ${searchUrl}`);
  await session.execute({ type: "goto", url: searchUrl });
  await session.execute({ type: "wait", time_ms: 1500 });

  return session.scrape({
    instructions:
      `Extract the top ${limit} Data.gov dataset search results for query ${JSON.stringify(query)}. ` +
      "Return search_query, result_count_text, current_url, sort_option, and datasets. " +
      "For each dataset include rank, title, URL, organization, last updated date, " +
      "description summary, visible formats, search relevance, and views last month. " +
      `Return no more than ${limit} datasets.`,
    only_main_content: true,
    only_images: false,
    scrape_links: true,
    scrape_images: false,
    response_format: SearchResults,
  });
}

async function scrapeDatasetDetail(
  session: {
    execute: (action: unknown) => Promise<unknown>;
    scrape: <T>(options: { instructions: string; response_format: z.ZodSchema<T>; only_main_content?: boolean; only_images?: boolean; scrape_links?: boolean; scrape_images?: boolean }) => Promise<T>;
  },
  datasetUrl: string,
): Promise<DatasetDetail> {
  console.log(`Opening dataset detail: ${datasetUrl}`);
  await session.execute({ type: "goto", url: datasetUrl });
  await session.execute({ type: "wait", time_ms: 1000 });

  return session.scrape({
    instructions:
      "Extract this Data.gov dataset detail page as JSON. Include title, organization, " +
      "description, last updated date, homepage/source link, license, any visible metadata " +
      "fields, and available resources/distributions with name, format, and URL.",
    only_main_content: true,
    only_images: false,
    scrape_links: true,
    scrape_images: false,
    response_format: DatasetDetail,
  });
}

async function main() {
  const { query, limit } = parseArgs();
  const apiKey = process.env.NOTTE_API_KEY;
  if (!apiKey) {
    throw new Error("Missing NOTTE_API_KEY. Set it in your environment or .env file.");
  }

  const client = new NotteClient({ apiKey });
  const searchUrl = dataGovSearchUrl(query);
  let searchResults: SearchResults | null = null;
  const findings: Array<{ search_result: DatasetSearchResult; detail: DatasetDetail | null; detail_error: string | null }> = [];

  await client.Session({ open_viewer: true, idle_timeout_minutes: 5, use_file_storage: true }).use(async (session) => {
    console.log(`Session ID: ${session.getId()}`);
    await printViewerUrl(session);

    searchResults = await scrapeSearchResults(session, query, limit);

    for (const result of searchResults.datasets.slice(0, limit)) {
      const detailUrl = absoluteDataGovUrl(result.url);
      const normalizedResult = { ...result, url: detailUrl };
      let detail: DatasetDetail | null = null;
      let detailError: string | null = null;

      if (detailUrl) {
        try {
          detail = await scrapeDatasetDetail(session, detailUrl);
        } catch (error) {
          detailError = error instanceof Error ? error.message : String(error);
          console.log(`Skipping detail extraction for ${detailUrl}: ${detailError}`);
        }
      }

      findings.push({ search_result: normalizedResult, detail, detail_error: detailError });
    }
  });

  console.log(JSON.stringify({
    query,
    limit,
    search_url: searchUrl,
    result_count_text: searchResults?.result_count_text ?? null,
    sort_option: searchResults?.sort_option ?? null,
    findings,
  }, null, 2));
}

main().catch((error: unknown) => {
  console.error(`Error finding Data.gov datasets: ${error instanceof Error ? error.message : String(error)}`);
  console.error("Common fixes:");
  console.error("  - Set NOTTE_API_KEY in your environment or .env file");
  console.error("  - Try a simpler query, for example: npm start -- --query climate --limit 3");
  console.error("  - Keep --limit small if you only need the top matches");
  process.exit(1);
});
