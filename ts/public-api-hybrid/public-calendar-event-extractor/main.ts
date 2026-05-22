import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { config as loadEnv } from "dotenv";
import { NotteClient } from "notte-sdk";
import { z } from "zod";

const __dirname = dirname(fileURLToPath(import.meta.url));
loadEnv({ path: join(__dirname, ".env") });
loadEnv({ path: join(__dirname, "..", ".env") });

const DEFAULT_EVENTS_URL = process.env.LOC_EVENTS_URL ?? "https://www.loc.gov/events/";
const DEFAULT_RESULT_LIMIT = Number.parseInt(process.env.LOC_EVENT_LIMIT ?? "5", 10);
const USE_PROXY = !["0", "false", "no"].includes((process.env.USE_PROXY ?? "true").toLowerCase());
const HTTP_HEADERS = {
  Accept: "application/json",
  "User-Agent": "bb-templates-public-calendar-event-extractor/1.0",
};

const CalendarEvent = z.object({
  title: z.string().nullable().default(null).describe("Event title."),
  url: z.string().nullable().default(null).describe("Event detail URL."),
  date: z.string().nullable().default(null).describe("Event date from the listing."),
  start_time: z.string().nullable().default(null).describe("Local event start timestamp when available."),
  end_time: z.string().nullable().default(null).describe("Local event end timestamp when available."),
  venue: z.string().nullable().default(null).describe("Building, campus, or online venue text."),
  attendance: z.string().nullable().default(null).describe("Attendance condition, for example ticket or none."),
  status: z.string().nullable().default(null).describe("Event status."),
  categories: z.array(z.string()).default([]).describe("LOC event categories."),
  description: z.string().nullable().default(null).describe("Short event description."),
});

const EventExtractionReport = z.object({
  listing_url: z.string(),
  api_url: z.string(),
  limit: z.number(),
  pagination: z.string().nullable().default(null),
  result_count: z.number(),
  browser_status: z.string(),
  events: z.array(CalendarEvent).default([]),
});

type CalendarEvent = z.infer<typeof CalendarEvent>;
type EventExtractionReport = z.infer<typeof EventExtractionReport>;

function parseArgs() {
  const args = process.argv.slice(2);
  let url = DEFAULT_EVENTS_URL;
  let limit = DEFAULT_RESULT_LIMIT;

  for (let index = 0; index < args.length; index += 1) {
    const arg = args[index];
    if (arg === "--url") {
      url = args[++index] ?? url;
    } else if (arg === "--limit") {
      limit = Number.parseInt(args[++index] ?? String(limit), 10);
    }
  }

  return { url, limit };
}

function validateLimit(limit: number): number {
  if (!Number.isFinite(limit) || limit < 1) {
    throw new Error("Limit must be at least 1.");
  }

  return Math.min(limit, 50);
}

function locJsonUrl(listingUrl: string, limit: number): string {
  const parsed = new URL(listingUrl.trim());
  if (!parsed.hostname.endsWith("loc.gov")) {
    throw new Error("This template only accepts loc.gov event listing URLs.");
  }

  parsed.searchParams.set("fo", "json");
  parsed.searchParams.set("c", String(limit));
  return parsed.toString();
}

function cleanText(value: unknown): string | null {
  if (value === null || value === undefined) {
    return null;
  }

  const raw = Array.isArray(value) ? value.filter(Boolean).join(" ") : String(value);
  const text = raw
    .replace(/<[^>]+>/g, " ")
    .replace(/&nbsp;/g, " ")
    .replace(/&amp;/g, "&")
    .replace(/\s+/g, " ")
    .trim();
  return text || null;
}

function venueFromItem(item: Record<string, unknown>): string | null {
  const parts = [item.location_label, item.location, item.building, item.campus];
  if (item.online) {
    parts.unshift("Online");
  }

  const seen = new Set<string>();
  const cleanParts = parts
    .map(cleanText)
    .filter((part): part is string => Boolean(part) && !seen.has(part) && Boolean(seen.add(part)));
  return cleanParts.length ? cleanParts.join(", ") : null;
}

function normalizeEvent(rawEvent: Record<string, any>): CalendarEvent {
  const item = (rawEvent.item ?? {}) as Record<string, any>;
  const description = cleanText(rawEvent.description ?? item.description ?? item.article);

  return CalendarEvent.parse({
    title: cleanText(rawEvent.title ?? item.title),
    url: rawEvent.url ?? rawEvent.id ?? null,
    date: rawEvent.date ?? null,
    start_time: item.event_start ?? item.event_start_date_local ?? null,
    end_time: item.event_end ?? item.event_end_date_local ?? null,
    venue: venueFromItem(item),
    attendance: item.attendance_conditions ?? null,
    status: item.event_status ?? null,
    categories: Array.isArray(item.categories) ? item.categories.filter(Boolean).map(String) : [],
    description,
  });
}

async function printViewerUrl(session: { status: () => Promise<{ viewer_url?: string | null }> }) {
  const status = await session.status();
  if (status.viewer_url) {
    console.log(`Live View: ${status.viewer_url}`);
  }
}

async function browserProbe(client: NotteClient, listingUrl: string): Promise<string> {
  try {
    return await client
      .Session({
        open_viewer: true,
        idle_timeout_minutes: 3,
        proxies: USE_PROXY,
        use_file_storage: true,
      })
      .use(async (session) => {
        console.log(`Session ID: ${session.getId()}`);
        await printViewerUrl(session);
        console.log(`Opening LOC events listing for browser trace: ${listingUrl}`);
        await session.execute({ type: "goto", url: listingUrl });
        await session.execute({ type: "wait", time_ms: 1500 });
        const observed = await session.observe("fast");
        return `browser visit succeeded: ${observed?.metadata?.title ?? "LOC events page"}`;
      });
  } catch (error) {
    return `browser visit failed; continued with LOC JSON endpoint: ${
      error instanceof Error ? error.message : String(error)
    }`;
  }
}

async function fetchEvents(apiUrl: string, limit: number): Promise<{ pagination: string | null; events: CalendarEvent[] }> {
  const response = await fetch(apiUrl, { headers: HTTP_HEADERS });
  if (!response.ok) {
    throw new Error(`LOC JSON request failed with ${response.status}`);
  }

  const payload = (await response.json()) as any;
  const content = payload.content ?? {};
  const rawEvents = Array.isArray(content.results) ? content.results : [];
  return {
    pagination: typeof content.pagination === "string" ? content.pagination : null,
    events: rawEvents.slice(0, limit).map(normalizeEvent),
  };
}

async function extractEvents(listingUrl: string, requestedLimit: number): Promise<EventExtractionReport> {
  const limit = validateLimit(requestedLimit);
  const apiUrl = locJsonUrl(listingUrl, limit);

  let browserStatus = "browser probe skipped: NOTTE_API_KEY is not set";
  if (process.env.NOTTE_API_KEY) {
    browserStatus = await browserProbe(new NotteClient({ apiKey: process.env.NOTTE_API_KEY }), listingUrl);
  }
  console.log(browserStatus);

  console.log(`Fetching LOC events JSON: ${apiUrl}`);
  const { pagination, events } = await fetchEvents(apiUrl, limit);

  return EventExtractionReport.parse({
    listing_url: listingUrl,
    api_url: apiUrl,
    limit,
    pagination,
    result_count: events.length,
    browser_status: browserStatus,
    events,
  });
}

async function main() {
  const args = parseArgs();
  const report = await extractEvents(args.url, args.limit);
  console.log(JSON.stringify(report, null, 2));
}

main().catch((error: unknown) => {
  console.error(`Error extracting public calendar events: ${error instanceof Error ? error.message : String(error)}`);
  console.error("Common fixes:");
  console.error("  - Set NOTTE_API_KEY in your environment or .env file to enable the Notte browser probe");
  console.error("  - Use a Library of Congress events URL, for example: npm start -- --url https://www.loc.gov/events/ --limit 5");
  console.error("  - Set USE_PROXY=false if your Notte browser session has proxy issues");
  process.exit(1);
});
