import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { config as loadEnv } from "dotenv";
import { NotteClient } from "notte-sdk";
import { z } from "zod";

const __dirname = dirname(fileURLToPath(import.meta.url));
loadEnv({ path: join(__dirname, ".env") });
loadEnv({ path: join(__dirname, "..", ".env") });

const DEFAULT_CATEGORY_URL =
  process.env.WEBSCRAPER_CATEGORY_URL ??
  "http://webscraper.io/test-sites/e-commerce/static/computers/laptops";
const DEFAULT_RESULT_LIMIT = Number(process.env.WEBSCRAPER_RESULT_LIMIT ?? "12");
const MAX_RESULT_LIMIT = 120;

const ProductCard = z.object({
  page_position: z.number().nullable().default(null),
  title: z.string().nullable().default(null),
  detail_url: z.string().nullable().default(null),
  price_text: z.string().nullable().default(null),
  description: z.string().nullable().default(null),
  reviews_text: z.string().nullable().default(null),
  image_url: z.string().nullable().default(null),
});

const CategoryPage = z.object({
  category_title: z.string().nullable().default(null),
  total_item_count_text: z.string().nullable().default(null),
  products: z.array(ProductCard).default([]),
  next_page_url: z.string().nullable().default(null),
});

type Product = z.infer<typeof ProductCard> & {
  listing_page: number;
  price: number | null;
  review_count: number | null;
};

function webscraperBrowserUrl(url: string): string {
  const parsed = new URL(url);
  if (parsed.hostname === "webscraper.io" && parsed.protocol === "https:") {
    parsed.protocol = "http:";
  }
  return parsed.toString();
}

function currentPageNumber(url: string): number {
  const value = new URL(url).searchParams.get("page") ?? "1";
  const parsed = Number(value);
  return Number.isInteger(parsed) ? parsed : 1;
}

function parsePrice(value: string | null | undefined): number | null {
  const match = value?.match(/[\d.]+/);
  return match ? Number(match[0]) : null;
}

function parseReviewCount(value: string | null | undefined): number | null {
  const match = value?.match(/\d+/);
  return match ? Number(match[0]) : null;
}

function absoluteUrl(currentUrl: string, candidate: string | null | undefined): string | null {
  if (!candidate) {
    return null;
  }
  return new URL(candidate, currentUrl).toString();
}

async function printViewerUrl(session: { status: () => Promise<{ viewer_url?: string | null }> }) {
  const status = await session.status();
  if (status.viewer_url) {
    console.log(`Live View: ${status.viewer_url}`);
  }
}

async function scrapeCategoryPage(session: { scrape: any }) {
  return session.scrape({
    instructions:
      "Extract this Webscraper.io ecommerce listing page. Return category title, total item count text, " +
      "visible product cards with page position, title, detail URL, price text, description, review text, " +
      "image URL, and the absolute next pagination URL if there is a next page link.",
    only_main_content: true,
    scrape_links: true,
    scrape_images: false,
    response_format: CategoryPage,
  }) as Promise<z.infer<typeof CategoryPage>>;
}

async function scrapeCategory(categoryUrl: string, resultLimit: number) {
  if (resultLimit < 1) {
    throw new Error("Limit must be at least 1.");
  }

  const requestedUrl = categoryUrl;
  const browserUrl = webscraperBrowserUrl(categoryUrl);
  const limit = Math.min(resultLimit, MAX_RESULT_LIMIT);
  const apiKey = process.env.NOTTE_API_KEY;
  if (!apiKey) {
    throw new Error("Missing NOTTE_API_KEY. Set it in your environment or .env file.");
  }

  const client = new NotteClient({ apiKey });
  const products: Product[] = [];
  let metadata: Pick<z.infer<typeof CategoryPage>, "category_title" | "total_item_count_text"> = {
    category_title: null,
    total_item_count_text: null,
  };

  await client.Session({ idle_timeout_minutes: 5, use_file_storage: true }).use(async (session) => {
    console.log(`Session ID: ${session.getId()}`);
    await printViewerUrl(session);

    let nextUrl: string | null = browserUrl;
    while (nextUrl && products.length < limit) {
      const pageNumber = currentPageNumber(nextUrl);
      console.log(`Scraping page ${pageNumber}: ${nextUrl}`);

      await session.execute({ type: "goto", url: nextUrl });
      await session.execute({ type: "wait", time_ms: 1500 });

      const page = await scrapeCategoryPage(session);
      if (!metadata.category_title && !metadata.total_item_count_text) {
        metadata = {
          category_title: page.category_title,
          total_item_count_text: page.total_item_count_text,
        };
      }

      const remaining = limit - products.length;
      products.push(
        ...page.products.slice(0, remaining).map((product, index) => ({
          ...product,
          page_position: product.page_position ?? index + 1,
          listing_page: pageNumber,
          detail_url: absoluteUrl(nextUrl ?? browserUrl, product.detail_url),
          image_url: absoluteUrl(nextUrl ?? browserUrl, product.image_url),
          price: parsePrice(product.price_text),
          review_count: parseReviewCount(product.reviews_text),
        })),
      );

      nextUrl = products.length >= limit ? null : absoluteUrl(nextUrl, page.next_page_url);
    }
  });

  return {
    observed_at: new Date().toISOString(),
    requested_category_url: requestedUrl,
    browser_category_url: browserUrl,
    category_title: metadata.category_title,
    total_item_count_text: metadata.total_item_count_text,
    result_limit: limit,
    products_returned: products.length,
    products,
  };
}

async function main() {
  const report = await scrapeCategory(DEFAULT_CATEGORY_URL, DEFAULT_RESULT_LIMIT);
  console.log(JSON.stringify(report, null, 2));
}

main().catch((error: unknown) => {
  console.error(`Error scraping Webscraper.io ecommerce demo: ${error instanceof Error ? error.message : String(error)}`);
  console.error("Common fixes:");
  console.error("  - Set NOTTE_API_KEY in your environment or .env file");
  console.error("  - Use a Webscraper.io static category URL");
  console.error("  - Keep WEBSCRAPER_RESULT_LIMIT small while testing");
  process.exit(1);
});
