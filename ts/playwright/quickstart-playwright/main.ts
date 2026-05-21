import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { config as loadEnv } from "dotenv";
import { chromium, type Browser, type Page } from "playwright";
import { NotteClient } from "notte-sdk";
import { z } from "zod";

const __dirname = dirname(fileURLToPath(import.meta.url));
loadEnv({ path: join(__dirname, ".env") });
loadEnv({ path: join(__dirname, "..", ".env") });

const ArticleSnapshot = z.object({
  title: z.string().nullable().default(null).describe("The article title."),
  url: z.string().nullable().default(null).describe("The article URL."),
  description: z.string().nullable().default(null).describe("A concise description of the subject."),
  lead_paragraph: z.string().nullable().default(null).describe("The first substantial paragraph."),
  sections: z.array(z.string()).default([]).describe("Visible article section headings."),
  notable_facts: z.array(z.string()).default([]).describe("A few notable facts from the article."),
});

async function printViewerUrl(session: { status: () => Promise<{ viewer_url?: string | null }> }) {
  const status = await session.status();
  if (status.viewer_url) {
    console.log(`Live debug URL: ${status.viewer_url}`);
  }
}

async function getCdpUrl(session: { status: () => Promise<{ cdp_url?: string | null }> }) {
  const status = await session.status();
  if (!status.cdp_url) {
    throw new Error("The Notte session did not return a CDP URL.");
  }

  return status.cdp_url;
}

async function getActivePage(browser: Browser): Promise<Page> {
  const context = browser.contexts()[0] ?? (await browser.newContext());
  return context.pages()[0] ?? (await context.newPage());
}

async function main() {
  const apiKey = process.env.NOTTE_API_KEY;
  if (!apiKey) {
    throw new Error("Missing NOTTE_API_KEY. Set it in your environment or .env file.");
  }

  const client = new NotteClient({ apiKey });

  await client.Session({
    idle_timeout_minutes: 2,
    browser_type: "chromium",
  }).use(async (session) => {
    console.log(`Session created, id: ${session.getId()}`);
    await printViewerUrl(session);

    const cdpUrl = await getCdpUrl(session);
    const browser = await chromium.connectOverCDP(cdpUrl);

    try {
      const page = await getActivePage(browser);
      const waitTimeout = 10_000;

      await page.goto("https://en.wikipedia.org/wiki/Main_Page", {
        waitUntil: "domcontentloaded",
        timeout: waitTimeout,
      });

      await page.getByRole("button", { name: "Main menu" }).click({ timeout: waitTimeout });
      await page.getByRole("link", { name: "Random article" }).click({ timeout: waitTimeout });
      await page.waitForLoadState("domcontentloaded", { timeout: waitTimeout });

      console.log(`Random article URL: ${page.url()} | Title: ${await page.title()}`);

      const heading = page.locator("#firstHeading");
      await heading.waitFor({ state: "visible", timeout: waitTimeout });
      console.log(`Heading: ${await heading.textContent()}`);

      const article = await session.scrape({
        instructions:
          "Extract a compact summary of the current Wikipedia article. Include the title, " +
          "current URL, short description, first substantial paragraph, visible section " +
          "headings, and 3 to 5 notable facts. Ignore references, navigation, and page chrome.",
        only_main_content: true,
        scrape_links: false,
        scrape_images: false,
        response_format: ArticleSnapshot,
      });

      if (article.url === null) {
        article.url = page.url();
      }

      console.log(JSON.stringify(article, null, 2));
    } finally {
      await browser.close();
    }
  });

  console.log("Session complete");
}

main().catch((error: unknown) => {
  console.error(`Error: ${error instanceof Error ? error.message : String(error)}`);
  console.error("\nTroubleshooting:");
  console.error("  1. Check your .env file has NOTTE_API_KEY");
  console.error("  2. Verify the target site is reachable");
  console.error("Docs: https://docs.notte.cc/");
  process.exit(1);
});
