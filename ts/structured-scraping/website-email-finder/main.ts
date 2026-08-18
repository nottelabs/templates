import { resolve } from "node:path";
import { pathToFileURL } from "node:url";
import { config as loadEnv } from "dotenv";
import { NotteClient } from "notte-sdk";

loadEnv({ path: new URL(".env", import.meta.url) });

const EMAIL_RE =
  /(?<![\w.+/@-])([a-z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-z0-9-]+(?:\.[a-z][a-z0-9-]{1,62})+)(?![\w.-])/gi;
const CONTACT_HINT_RE =
  /\b(contact(?: us)?|get in touch|reach us|email us|talk to us|support|customer service|help(?: center| desk)?)\b/i;
const MARKDOWN_LINK_RE = /\[([^\]]+)]\(([^)\s]+)(?:\s+"[^"]*")?\)/g;
const HTML_LINK_RE = /<a\b([^>]*?)>([\s\S]*?)<\/a>/gi;
const FALLBACK_PATHS = ["/contact", "/contact-us", "/get-in-touch", "/support"];
const NON_PAGE_SUFFIXES = [
  ".avi",
  ".gif",
  ".jpeg",
  ".jpg",
  ".mov",
  ".mp3",
  ".mp4",
  ".mpeg",
  ".pdf",
  ".png",
  ".svg",
  ".webm",
  ".webp",
];

type ExecutionResult = {
  success: boolean;
  message?: string | null;
};

export type EmailFinderSession = {
  execute: (
    action: unknown,
    raiseOnFailure?: boolean,
  ) => Promise<ExecutionResult>;
  scrape: (options?: {
    only_main_content?: boolean;
    scrape_links?: boolean;
  }) => Promise<string>;
};

export type ScrapeResult = {
  emails: Map<string, Set<string>>;
  errors: string[];
};

function decodeHtml(value: string): string {
  const namedEntities: Record<string, string> = {
    amp: "&",
    apos: "'",
    gt: ">",
    lt: "<",
    quot: '"',
  };

  return value
    .replace(/&#(x[0-9a-f]+|\d+);/gi, (entity, code: string) => {
      const radix = code.toLowerCase().startsWith("x") ? 16 : 10;
      const digits = radix === 16 ? code.slice(1) : code;
      return String.fromCodePoint(Number.parseInt(digits, radix));
    })
    .replace(
      /&(amp|apos|gt|lt|quot);/gi,
      (_entity, name: string) => namedEntities[name.toLowerCase()],
    );
}

function decodePercentEncoding(value: string): string {
  try {
    return decodeURIComponent(value);
  } catch {
    return value.replace(/%([0-9a-f]{2})/gi, (_encoded, byte: string) =>
      String.fromCharCode(Number.parseInt(byte, 16)),
    );
  }
}

function stripTags(value: string): string {
  return decodeHtml(value.replace(/<[^>]*>/g, " "))
    .replace(/\s+/g, " ")
    .trim();
}

function attributeValue(attributes: string, name: string): string {
  const pattern = new RegExp(
    `${name}\\s*=\\s*(?:"([^"]*)"|'([^']*)'|([^\\s>]+))`,
    "i",
  );
  const match = pattern.exec(attributes);
  return match?.[1] ?? match?.[2] ?? match?.[3] ?? "";
}

function extractedLinks(body: string): Array<{ href: string; label: string }> {
  const links: Array<{ href: string; label: string }> = [];

  for (const match of body.matchAll(MARKDOWN_LINK_RE)) {
    links.push({ href: match[2], label: match[1] });
  }

  for (const match of body.matchAll(HTML_LINK_RE)) {
    const attributes = match[1];
    const href = attributeValue(attributes, "href");
    if (!href) continue;
    const label = [
      attributeValue(attributes, "aria-label"),
      attributeValue(attributes, "title"),
      stripTags(match[2]),
    ].join(" ");
    links.push({ href, label });
  }

  return links;
}

export function normalizeUrl(value: string): string {
  const candidate = value.includes("://") ? value : `https://${value}`;
  const url = new URL(candidate);
  if (!["http:", "https:"].includes(url.protocol) || !url.host) {
    throw new Error(
      "URL must be an HTTP(S) address, for example https://example.com",
    );
  }
  url.hash = "";
  return url.toString();
}

export function siteOrigin(value: string): string {
  return new URL(value).origin;
}

export function extractEmails(body: string): Set<string> {
  const decoded = decodePercentEncoding(decodeHtml(body));
  return new Set(
    [...decoded.matchAll(EMAIL_RE)].map((match) =>
      match[1].toLowerCase().replace(/[.,;:]+$/, ""),
    ),
  );
}

export function contactLinks(
  body: string,
  pageUrl: string,
  origin: string,
): Set<string> {
  const links = new Set<string>();
  const siteHost = new URL(origin).host.toLowerCase();

  for (const { href, label } of extractedLinks(body)) {
    let candidate: URL;
    try {
      candidate = new URL(decodeHtml(href), pageUrl);
    } catch {
      continue;
    }

    const searchable = `${decodePercentEncoding(candidate.pathname).replace(/[-_]/g, " ")} ${label}`;
    if (
      ["http:", "https:"].includes(candidate.protocol) &&
      candidate.host.toLowerCase() === siteHost &&
      !NON_PAGE_SUFFIXES.some((suffix) =>
        candidate.pathname.toLowerCase().endsWith(suffix),
      ) &&
      CONTACT_HINT_RE.test(searchable)
    ) {
      candidate.hash = "";
      links.add(candidate.toString());
    }
  }

  return links;
}

async function scrapePage(
  session: EmailFinderSession,
  url: string,
): Promise<[string, string]> {
  const result = await session.execute({ type: "goto", url }, false);
  if (!result.success) {
    throw new Error(result.message ?? "Navigation failed");
  }
  const markdown = await session.scrape({
    only_main_content: false,
    scrape_links: true,
  });
  return [url, markdown];
}

export async function scrapeWithSession(
  session: EmailFinderSession,
  startUrl: string,
  verbose = false,
): Promise<ScrapeResult> {
  const normalizedStartUrl = normalizeUrl(startUrl);
  const emails = new Map<string, Set<string>>();
  const errors: string[] = [];

  const addEmails = (body: string, sourceUrl: string) => {
    for (const email of extractEmails(body)) {
      const sources = emails.get(email) ?? new Set<string>();
      sources.add(sourceUrl);
      emails.set(email, sources);
    }
  };

  if (verbose) console.error(`Fetching ${normalizedStartUrl}`);

  let finalUrl: string;
  let body: string;
  try {
    [finalUrl, body] = await scrapePage(session, normalizedStartUrl);
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    return { emails, errors: [`${normalizedStartUrl}: ${message}`] };
  }

  addEmails(body, finalUrl);
  const origin = siteOrigin(finalUrl);
  const discoveredLinks = [...contactLinks(body, finalUrl, origin)].sort();
  const candidates = discoveredLinks.length
    ? discoveredLinks
    : FALLBACK_PATHS.map((path) => new URL(path, origin).toString());

  for (const url of candidates) {
    if (url === finalUrl) continue;
    if (verbose) console.error(`Fetching ${url}`);
    try {
      const [contactUrl, contactBody] = await scrapePage(session, url);
      addEmails(contactBody, contactUrl);
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      errors.push(`${url}: ${message}`);
    }
  }

  return { emails, errors };
}

export async function scrape(
  startUrl: string,
  verbose = false,
): Promise<ScrapeResult> {
  const apiKey = process.env.NOTTE_API_KEY;
  if (!apiKey)
    throw new Error(
      "Missing NOTTE_API_KEY. Set it in your environment or .env file.",
    );

  const client = new NotteClient({ apiKey });
  return client
    .Session()
    .use((session) => scrapeWithSession(session, startUrl, verbose));
}

function usage(): string {
  return [
    "Usage: npm start -- <url> [--json] [--verbose]",
    "",
    "Find emails on a page and its likely contact pages.",
    "",
    "Options:",
    "  --json         Print machine-readable JSON",
    "  --verbose, -v  Show fetched pages and skipped-page errors",
  ].join("\n");
}

export async function main(args = process.argv.slice(2)): Promise<number> {
  if (args.includes("--help") || args.includes("-h")) {
    console.log(usage());
    return 0;
  }

  const jsonOutput = args.includes("--json");
  const verbose = args.includes("--verbose") || args.includes("-v");
  const positional = args.filter(
    (arg) => !["--json", "--verbose", "-v"].includes(arg),
  );
  if (positional.length !== 1 || positional[0].startsWith("-")) {
    console.error(usage());
    return 2;
  }

  try {
    const { emails, errors } = await scrape(positional[0], verbose);
    const entries = [...emails.entries()].sort(([first], [second]) =>
      first.localeCompare(second),
    );

    if (jsonOutput) {
      console.log(
        JSON.stringify(
          Object.fromEntries(
            entries.map(([email, pages]) => [email, [...pages].sort()]),
          ),
          null,
          2,
        ),
      );
    } else if (entries.length) {
      for (const [email] of entries) console.log(email);
    } else {
      console.error("No email addresses found.");
    }

    if (verbose) {
      for (const error of errors) console.error(`Skipped ${error}`);
    }
    return 0;
  } catch (error) {
    console.error(
      `error: ${error instanceof Error ? error.message : String(error)}`,
    );
    return 2;
  }
}

const entrypoint = process.argv[1]
  ? pathToFileURL(resolve(process.argv[1])).href
  : "";
if (entrypoint === import.meta.url) {
  process.exitCode = await main();
}
