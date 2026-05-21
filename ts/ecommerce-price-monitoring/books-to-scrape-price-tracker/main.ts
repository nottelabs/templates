import { mkdir, writeFile } from "node:fs/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { config as loadEnv } from "dotenv";
import { NotteClient } from "notte-sdk";
import { z } from "zod";

const __dirname = dirname(fileURLToPath(import.meta.url));
loadEnv({ path: join(__dirname, ".env") });
loadEnv({ path: join(__dirname, "..", ".env") });

const BASE_URL = "http://books.toscrape.com/";
const DEFAULT_MAX_PAGES = 2;
const DEFAULT_MAX_BOOKS = 40;
const DEFAULT_PRICE_ALERT_BELOW = 20.0;

const BookCard = z.object({
  title: z.string().nullable().default(null).describe("Book title from the listing card"),
  price_text: z.string().nullable().default(null).describe("Visible price text including currency symbol"),
  stock_status: z.string().nullable().default(null).describe("Visible availability text"),
  rating: z.string().nullable().default(null).describe("Star rating text or class such as One, Two, Three, Four, or Five"),
  detail_url: z.string().nullable().default(null).describe("Absolute product detail URL"),
  image_url: z.string().nullable().default(null).describe("Absolute product image URL"),
});

const ListingPage = z.object({
  books: z.array(BookCard).default([]).describe("Books visible on the current catalog page"),
  next_page_url: z.string().nullable().default(null).describe("Absolute URL for the next catalog page, if present"),
});

const BookDetail = z.object({
  upc: z.string().nullable().default(null),
  product_type: z.string().nullable().default(null),
  price_excluding_tax_text: z.string().nullable().default(null),
  price_including_tax_text: z.string().nullable().default(null),
  tax_text: z.string().nullable().default(null),
  availability_text: z.string().nullable().default(null),
  category_path: z.array(z.string()).default([]),
  description: z.string().nullable().default(null),
  detail_rating: z.string().nullable().default(null),
  detail_image_url: z.string().nullable().default(null),
  review_count: z.number().nullable().default(null),
});

type BookRecord = z.infer<typeof BookCard> &
  Partial<z.infer<typeof BookDetail>> & {
    price: number | null;
    currency: string;
    availability_count: number | null;
    listing_page: number;
  };

function envBool(name: string, defaultValue: boolean): boolean {
  const value = process.env[name];
  if (value === undefined) {
    return defaultValue;
  }
  return ["1", "true", "yes", "on"].includes(value.trim().toLowerCase());
}

function parseNumberEnv(name: string, defaultValue: number): number {
  const value = process.env[name];
  if (!value) {
    return defaultValue;
  }
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : defaultValue;
}

function parsePrice(value: string | null | undefined): number | null {
  const match = value?.match(/[\d.]+/);
  return match ? Number(match[0]) : null;
}

function parseAvailableCount(value: string | null | undefined): number | null {
  const match = value?.match(/\((\d+) available\)/);
  return match ? Number(match[1]) : null;
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
    console.log(`Live View Link: ${status.viewer_url}`);
  }
}

async function scrapeListing(session: { scrape: any }) {
  return session.scrape({
    instructions:
      "Extract the visible books on this catalog page as JSON. Include each listing card's title, " +
      "visible price text, stock status text, star rating text or rating class, absolute product detail URL, " +
      "absolute image URL, and the absolute next page URL if the pagination has a next link.",
    only_main_content: false,
    scrape_links: true,
    scrape_images: false,
    response_format: ListingPage,
  }) as Promise<z.infer<typeof ListingPage>>;
}

async function scrapeDetail(session: { scrape: any }) {
  return session.scrape({
    instructions:
      "Extract this Books to Scrape product detail page. Return UPC, product type, price excluding tax, " +
      "price including tax, tax, availability text, category breadcrumb labels excluding Home, description, " +
      "detail star rating, detail image URL, and numeric review count.",
    only_main_content: false,
    scrape_links: true,
    scrape_images: false,
    response_format: BookDetail,
  }) as Promise<z.infer<typeof BookDetail>>;
}

async function run() {
  const apiKey = process.env.NOTTE_API_KEY;
  if (!apiKey) {
    throw new Error("Missing NOTTE_API_KEY. Set it in your environment or .env file.");
  }

  const startUrl = process.env.BOOKS_START_URL ?? BASE_URL;
  const maxPages = parseNumberEnv("BOOKS_MAX_PAGES", DEFAULT_MAX_PAGES);
  const maxBooks = parseNumberEnv("BOOKS_MAX_BOOKS", DEFAULT_MAX_BOOKS);
  const priceAlertBelow = parseNumberEnv("BOOKS_PRICE_ALERT_BELOW", DEFAULT_PRICE_ALERT_BELOW);
  const lowStockThreshold = parseNumberEnv("BOOKS_LOW_STOCK_THRESHOLD", 5);
  const includeDetails = envBool("BOOKS_INCLUDE_DETAILS", true);

  const client = new NotteClient({ apiKey });
  const observedAt = new Date().toISOString();
  const books: BookRecord[] = [];
  let pageUrl: string | null = startUrl;

  await client.Session({ idle_timeout_minutes: 2 }).use(async (session) => {
    console.log("Notte session initialized successfully");
    console.log(`Session ID: ${session.getId()}`);
    await printViewerUrl(session);

    for (let pageNumber = 1; pageNumber <= maxPages && pageUrl && books.length < maxBooks; pageNumber += 1) {
      console.log(`Scraping catalog page ${pageNumber}: ${pageUrl}`);
      await session.execute({ type: "goto", url: pageUrl });
      await session.execute({ type: "wait", time_ms: 1500 });

      const listing = await scrapeListing(session);
      const remaining = maxBooks - books.length;
      const pageBooks = listing.books.slice(0, remaining).map((book) => {
        const detailUrl = absoluteUrl(pageUrl ?? startUrl, book.detail_url);
        const stockText = book.stock_status;
        return {
          ...book,
          detail_url: detailUrl,
          image_url: absoluteUrl(pageUrl ?? startUrl, book.image_url),
          price: parsePrice(book.price_text),
          currency: "GBP",
          availability_count: parseAvailableCount(stockText),
          listing_page: pageNumber,
        };
      });

      if (includeDetails) {
        for (const book of pageBooks) {
          if (!book.detail_url) {
            continue;
          }
          console.log(`  Fetching detail fields: ${book.title ?? book.detail_url}`);
          await session.execute({ type: "goto", url: book.detail_url });
          await session.execute({ type: "wait", time_ms: 1000 });
          const detail = await scrapeDetail(session);
          Object.assign(book, {
            ...detail,
            availability_count: parseAvailableCount(detail.availability_text) ?? book.availability_count,
            detail_image_url: absoluteUrl(book.detail_url, detail.detail_image_url),
          });
        }
      }

      books.push(...pageBooks);
      pageUrl = absoluteUrl(pageUrl, listing.next_page_url);
    }
  });

  const priceAlerts = books.filter((book) => book.price !== null && book.price <= priceAlertBelow);
  const lowStockAlerts = books.filter(
    (book) => book.availability_count !== null && book.availability_count <= lowStockThreshold,
  );
  const cheapestBooks = books
    .filter((book) => book.price !== null)
    .sort((left, right) => (left.price ?? Number.POSITIVE_INFINITY) - (right.price ?? Number.POSITIVE_INFINITY))
    .slice(0, 5);

  return {
    observed_at: observedAt,
    source: startUrl,
    books_checked: books.length,
    price_alert_below: priceAlertBelow,
    low_stock_threshold: lowStockThreshold,
    price_alerts: priceAlerts,
    low_stock_alerts: lowStockAlerts,
    cheapest_books: cheapestBooks,
    books,
  };
}

async function main() {
  const result = await run();
  const outputPath = process.env.BOOKS_OUTPUT_PATH;
  if (outputPath) {
    await mkdir(dirname(outputPath), { recursive: true });
    await writeFile(outputPath, JSON.stringify(result, null, 2), "utf8");
    console.log(`Wrote snapshot to ${outputPath}`);
  }
  console.log(JSON.stringify(result, null, 2));
}

main().catch((error: unknown) => {
  console.error(`Error in Books to Scrape price tracker: ${error instanceof Error ? error.message : String(error)}`);
  console.error("Common issues:");
  console.error("  - Check .env has NOTTE_API_KEY");
  console.error("  - Use http://books.toscrape.com/; HTTPS may fail in some browser sessions");
  console.error("  - Lower BOOKS_MAX_PAGES or set BOOKS_INCLUDE_DETAILS=false for a faster run");
  console.error("Docs: https://docs.notte.cc/");
  process.exit(1);
});
