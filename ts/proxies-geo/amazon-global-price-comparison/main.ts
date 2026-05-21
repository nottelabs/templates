import { mkdir, writeFile } from "node:fs/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { config as loadEnv } from "dotenv";
import { NotteClient } from "notte-sdk";
import { z } from "zod";

const __dirname = dirname(fileURLToPath(import.meta.url));
loadEnv({ path: join(__dirname, ".env") });
loadEnv({ path: join(__dirname, "..", ".env") });

const DEFAULT_OUTPUT_PATH = "output/amazon-global-price-comparison/results.json";

const Offer = z.object({
  title: z.string().default("Unknown").describe("The full product title shown in search results"),
  local_price: z.string().default("N/A").describe("The visible local price including currency symbol"),
  availability: z.string().default("N/A").describe("Availability or stock message shown on the listing"),
  delivery_estimate: z.string().default("N/A").describe("Delivery date, Prime, or shipping promise"),
  seller_or_fulfillment: z.string().default("N/A").describe("Seller, fulfillment, or marketplace badge text"),
  deal_note: z.string().default("N/A").describe("Coupon, discount, or savings note if visible"),
  product_url: z.string().default("N/A").describe("The product detail URL"),
});

const OffersResult = z.object({
  offers: z.array(Offer).default([]),
});

type Offer = z.infer<typeof Offer>;

type CountryConfig = {
  name: string;
  code: string;
  currency: string;
};

type CountryResult = {
  country: string;
  countryCode: string;
  currency: string;
  offers: Offer[];
  error: string | null;
  sessionId: string | null;
};

const COUNTRIES: CountryConfig[] = [
  { name: "United States", code: "us", currency: "USD" },
  { name: "Canada", code: "ca", currency: "CAD" },
  { name: "United Kingdom", code: "gb", currency: "GBP" },
  { name: "Australia", code: "au", currency: "AUD" },
  { name: "Japan", code: "jp", currency: "JPY" },
];

function createClient(): NotteClient {
  const apiKey = process.env.NOTTE_API_KEY;
  if (!apiKey) {
    throw new Error("Missing NOTTE_API_KEY. Set it in your environment or .env file.");
  }
  return new NotteClient({ apiKey });
}

function countryProxy(country: string) {
  return [{ type: "notte", country }];
}

function cleanOffers(offers: Offer[], resultsCount: number): Offer[] {
  return offers.slice(0, resultsCount).map((offer) => {
    const productUrl =
      offer.product_url && offer.product_url.startsWith("/")
        ? `https://www.amazon.com${offer.product_url}`
        : offer.product_url || "N/A";

    return {
      title: offer.title || "Unknown",
      local_price: offer.local_price || "N/A",
      availability: offer.availability || "N/A",
      delivery_estimate: offer.delivery_estimate || "N/A",
      seller_or_fulfillment: offer.seller_or_fulfillment || "N/A",
      deal_note: offer.deal_note || "N/A",
      product_url: productUrl,
    };
  });
}

async function getOffersForCountry(
  client: NotteClient,
  searchQuery: string,
  country: CountryConfig,
  resultsCount: number,
): Promise<CountryResult> {
  let sessionId: string | null = null;
  let countryOffers: Offer[] = [];

  try {
    await client
      .Session({
        idle_timeout_minutes: 2,
        proxies: countryProxy(country.code) as any,
        solve_captchas: true,
      })
      .use(async (session) => {
        sessionId = session.getId();
        const searchUrl = `https://www.amazon.com/s?k=${encodeURIComponent(searchQuery).replace(/%20/g, "+")}`;

        await session.execute({ type: "goto", url: searchUrl });
        await session.execute({ type: "wait", time_ms: 5000 });

        const result = await session.scrape({
          instructions:
            `Extract up to ${resultsCount} organic offers from this Amazon search results page. ` +
            "For each offer, extract the title, visible local price with currency symbol, " +
            "availability or stock message, delivery date or shipping promise, seller or fulfillment " +
            "badge, deal/coupon/savings note if visible, and product URL. Ignore ratings, review " +
            "counts, sponsored placements, banners, filters, and navigation.",
          response_format: OffersResult,
        });

        const offers = cleanOffers(result.offers, resultsCount);
        countryOffers = offers;
      });

    return {
      country: country.name,
      countryCode: country.code.toUpperCase(),
      currency: country.currency,
      offers: countryOffers,
      error: null,
      sessionId,
    };
  } catch (error: unknown) {
    return {
      country: country.name,
      countryCode: country.code.toUpperCase(),
      currency: country.currency,
      offers: [],
      error: error instanceof Error ? error.message : String(error),
      sessionId,
    };
  }
}

function displayComparisonTable(results: CountryResult[]) {
  console.log(`\n${"=".repeat(100)}`);
  console.log("GLOBAL OFFER AVAILABILITY SNAPSHOT");
  console.log("=".repeat(100));

  if (!results.some((result) => result.offers.length > 0)) {
    console.log("No offers found in any country.");
    return;
  }

  const maxOffers = Math.max(...results.map((result) => result.offers.length));
  for (let index = 0; index < maxOffers; index += 1) {
    console.log(`\n--- Offer ${index + 1} ---`);

    const offerTitle = results.find((result) => result.offers[index])?.offers[index]?.title;
    if (offerTitle) {
      console.log(`Offer: ${offerTitle.length > 80 ? `${offerTitle.slice(0, 77)}...` : offerTitle}`);
    }

    console.log("\nAvailability by Country:");
    console.log("-".repeat(70));

    for (const result of results) {
      const countryPad = result.country.padEnd(20, " ");
      if (result.error) {
        const sessionSuffix = result.sessionId ? ` [${result.sessionId}]` : "";
        console.log(`  ${countryPad} | Error${sessionSuffix}: ${result.error}`);
      } else if (result.offers[index]) {
        const offer = result.offers[index];
        console.log(
          `  ${countryPad} | ${offer.local_price.padEnd(18, " ")} | ${offer.availability} | ${offer.delivery_estimate} | ${offer.deal_note}`,
        );
      } else {
        console.log(`  ${countryPad} | No comparable offer found`);
      }
    }
  }

  console.log(`\n${"=".repeat(100)}`);
}

async function saveResults(results: CountryResult[]) {
  const outputPath = process.env.OUTPUT_PATH ?? DEFAULT_OUTPUT_PATH;
  await mkdir(dirname(outputPath), { recursive: true });
  await writeFile(outputPath, JSON.stringify(results, null, 2), "utf8");
}

async function main() {
  const searchQuery = process.env.SEARCH_QUERY ?? "65W GaN travel charger international adapters";
  const resultsCount = Number(process.env.RESULTS_COUNT ?? "2");
  const client = createClient();

  const results = await Promise.all(
    COUNTRIES.map((country) => getOffersForCountry(client, searchQuery, country, resultsCount)),
  );

  displayComparisonTable(results);
  await saveResults(results);
}

main().catch((error: unknown) => {
  console.error(`Application error: ${error instanceof Error ? error.message : String(error)}`);
  console.error("\nCommon issues:");
  console.error("  - Check .env file has NOTTE_API_KEY");
  console.error("  - Verify proxy countries are supported");
  console.error("  - Amazon may block or vary content by region");
  console.error("Docs: https://docs.notte.cc/");
  process.exit(1);
});
