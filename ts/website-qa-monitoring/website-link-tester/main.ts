import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { config as loadEnv } from "dotenv";
import { NotteClient } from "notte-sdk";
import { z } from "zod";

const __dirname = dirname(fileURLToPath(import.meta.url));
loadEnv({ path: join(__dirname, ".env") });
loadEnv({ path: join(__dirname, "..", ".env") });

const URL_TO_TEST = process.env.TARGET_URL ?? "https://www.notte.cc";
const MAX_LINKS = Number.parseInt(process.env.MAX_LINKS ?? "10", 10);
const SOCIAL_DOMAINS = [
  "twitter.com",
  "x.com",
  "facebook.com",
  "linkedin.com",
  "instagram.com",
  "youtube.com",
  "tiktok.com",
  "reddit.com",
  "discord.com",
];

const ExtractedLink = z.object({
  url: z.string(),
  link_text: z.string(),
});

const LinkCollection = z.object({
  links: z.array(ExtractedLink).default([]),
});

const PageVerificationSummary = z.object({
  page_title: z.string(),
  content_matches: z.boolean(),
  assessment: z.string(),
});

type ExtractedLink = z.infer<typeof ExtractedLink>;

type LinkVerificationResult = {
  link_text: string;
  url: string;
  success: boolean;
  page_title?: string | null;
  content_matches?: boolean | null;
  assessment?: string | null;
  error?: string | null;
};

async function printViewerUrl(
  session: { status: () => Promise<{ viewer_url?: string | null }> },
  label = "Session",
) {
  const status = await session.status();
  if (status.viewer_url) {
    console.log(`[${label}] Live View: ${status.viewer_url}`);
  }
}

function deduplicateLinks(links: ExtractedLink[]): ExtractedLink[] {
  const seenUrls = new Set<string>();
  const uniqueLinks: ExtractedLink[] = [];

  for (const link of links) {
    if (seenUrls.has(link.url)) continue;
    seenUrls.add(link.url);
    uniqueLinks.push(link);
  }

  return uniqueLinks;
}

async function collectLinksFromHomepage(client: NotteClient): Promise<ExtractedLink[]> {
  console.log("Collecting links from homepage...");

  const links = await client.Session({ idle_timeout_minutes: 2 }).use(async (session) => {
    await printViewerUrl(session, "Collect");
    console.log(`Navigating to ${URL_TO_TEST}...`);
    await session.execute({ type: "goto", url: URL_TO_TEST });
    await session.execute({ type: "wait", time_ms: 1000 });

    const collection = await session.scrape({
      instructions:
        "Extract visible links from this homepage. Return absolute http or https URLs and concise link_text. " +
        "Use aria-label or surrounding visible text when anchor text is empty. Do not include duplicate URLs.",
      only_main_content: false,
      scrape_links: true,
      response_format: LinkCollection,
    });

    return collection.links.filter((link) => link.url.startsWith("http"));
  });

  const uniqueLinks = deduplicateLinks(links);
  const limitedLinks = uniqueLinks.slice(0, MAX_LINKS);
  console.log(`Collected ${uniqueLinks.length} unique links; verifying ${limitedLinks.length}`);
  console.log(JSON.stringify({ links: limitedLinks }, null, 2));
  return limitedLinks;
}

async function verifySingleLink(client: NotteClient, link: ExtractedLink): Promise<LinkVerificationResult> {
  console.log(`\nChecking: ${link.link_text} (${link.url})`);

  try {
    return await client.Session({ idle_timeout_minutes: 2 }).use(async (session) => {
      await printViewerUrl(session, link.link_text.slice(0, 30));
      const isSocialLink = SOCIAL_DOMAINS.some((domain) => link.url.includes(domain));

      await session.execute({ type: "goto", url: link.url });
      await session.execute({ type: "wait", time_ms: 1000 });
      console.log(`Link opened successfully: ${link.link_text}`);

      if (isSocialLink) {
        return {
          link_text: link.link_text,
          url: link.url,
          success: true,
          page_title: "Social Media Link",
          content_matches: true,
          assessment: "Loaded; detailed verification skipped",
        };
      }

      const verification = await session.scrape({
        instructions:
          `Does this page content match what the link text ${JSON.stringify(link.link_text)} suggests? ` +
          "Extract the page title and provide a brief assessment.",
        response_format: PageVerificationSummary,
      });

      console.log(`[${link.link_text}] Page Title: ${verification.page_title}`);
      console.log(`[${link.link_text}] Content Matches: ${verification.content_matches}`);
      console.log(`[${link.link_text}] Assessment: ${verification.assessment}`);

      return {
        link_text: link.link_text,
        url: link.url,
        success: true,
        page_title: verification.page_title,
        content_matches: verification.content_matches,
        assessment: verification.assessment,
      };
    });
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : String(error);
    console.log(`Failed to verify link "${link.link_text}": ${errorMessage}`);
    return {
      link_text: link.link_text,
      url: link.url,
      success: false,
      error: errorMessage,
    };
  }
}

function outputResults(results: LinkVerificationResult[], label = "FINAL RESULTS") {
  console.log(`\n${"=".repeat(80)}`);
  console.log(label);
  console.log("=".repeat(80));

  const finalReport = {
    total_links: results.length,
    successful: results.filter((result) => result.success).length,
    failed: results.filter((result) => !result.success).length,
    results,
  };

  console.log(JSON.stringify(finalReport, null, 2));
  console.log(`\n${"=".repeat(80)}`);
}

async function main() {
  console.log("Starting Website Link Tester...");
  const apiKey = process.env.NOTTE_API_KEY;
  if (!apiKey) {
    throw new Error("Missing NOTTE_API_KEY. Set it in your environment or .env file.");
  }

  const client = new NotteClient({ apiKey });
  const links = await collectLinksFromHomepage(client);
  const results: LinkVerificationResult[] = [];

  for (const link of links) {
    results.push(await verifySingleLink(client, link));
  }

  outputResults(results);
  console.log("Script completed successfully");
}

main().catch((error: unknown) => {
  console.error(`Application error: ${error instanceof Error ? error.message : String(error)}`);
  console.error("Common issues:");
  console.error("  - Check .env has NOTTE_API_KEY");
  console.error("  - Ensure TARGET_URL is reachable");
  process.exit(1);
});
