import { mkdir, writeFile } from "node:fs/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { config as loadEnv } from "dotenv";
import { NotteClient } from "notte-sdk";
import { chromium, type Browser, type Page } from "playwright";

const __dirname = dirname(fileURLToPath(import.meta.url));
loadEnv({ path: join(__dirname, ".env") });
loadEnv({ path: join(__dirname, "..", ".env") });

const MAX_IMAGES = Number.parseInt(process.env.MAX_IMAGES ?? "10", 10);
const OUTPUT_DIR = process.env.OUTPUT_DIR ?? "./images";
const DEFAULT_URL = "https://yandex.com/images/search?text=flowers";

const MIME_TO_EXT: Record<string, string> = {
  "image/jpeg": "jpg",
  "image/png": "png",
  "image/webp": "webp",
  "image/gif": "gif",
  "image/svg+xml": "svg",
  "image/avif": "avif",
  "image/bmp": "bmp",
  "image/tiff": "tiff",
};

function isValidUrl(url: string): boolean {
  try {
    const parsed = new URL(url);
    return ["http:", "https:"].includes(parsed.protocol);
  } catch {
    return false;
  }
}

function imageFilename(url: string, mimeType: string, index: number): string {
  const ext = MIME_TO_EXT[mimeType] ?? "bin";
  try {
    const parsed = new URL(url);
    const segment = parsed.pathname.split("/").filter(Boolean).pop() ?? "";
    const base = segment.replace(/\.[^.]+$/, "") || `image-${index}`;
    const safe = base.replace(/[^a-zA-Z0-9_-]/g, "_").slice(0, 80);
    return `${safe}-${Date.now()}.${ext}`;
  } catch {
    return `image-${index}-${Date.now()}.${ext}`;
  }
}

async function printViewerUrl(session: { status: () => Promise<{ viewer_url?: string | null }> }) {
  const status = await session.status();
  if (status.viewer_url) {
    console.log(`Live View Link: ${status.viewer_url}`);
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

async function extractImageUrlsFromDom(page: Page): Promise<string[]> {
  return page.evaluate(() => {
    const urls = new Set();
    for (const img of document.querySelectorAll("img")) {
      if (img.currentSrc) urls.add(img.currentSrc);
      if (img.src) urls.add(img.src);
    }
    for (const el of document.querySelectorAll("*")) {
      const bg = getComputedStyle(el).backgroundImage;
      for (const match of bg.matchAll(/url\\(["']?([^"')]+)["']?\\)/g)) {
        urls.add(new URL(match[1], document.baseURI).href);
      }
    }
    return Array.from(urls);
  }) as Promise<string[]>;
}

async function fetchImageBytes(page: Page, url: string) {
  const response = await page.context().request.get(url);
  if (!response.ok()) {
    throw new Error(`HTTP ${response.status()}`);
  }
  const mimeType = (response.headers()["content-type"] ?? "").split(";")[0]?.trim() ?? "";
  const bytes = await response.body();
  return { bytes, mimeType };
}

async function main() {
  if (!process.env.NOTTE_API_KEY) {
    throw new Error("Missing NOTTE_API_KEY. Set it in your environment or .env file.");
  }

  const targetUrl = process.argv[2] ?? DEFAULT_URL;
  console.log(`Image URL Download - target: ${targetUrl}`);
  console.log(`Max images: ${MAX_IMAGES} | Output: ${OUTPUT_DIR}/<hostname>/\n`);

  const client = new NotteClient({ apiKey: process.env.NOTTE_API_KEY });

  await client
    .Session({ idle_timeout_minutes: 2, browser_type: "chromium" })
    .use(async (session) => {
      console.log("Notte session initialized successfully");
      console.log(`Session ID: ${session.getId()}`);
      await printViewerUrl(session);

      const browser = await chromium.connectOverCDP(await getCdpUrl(session));

      try {
        const page = await getActivePage(browser);

        console.log(`\nNavigating to ${targetUrl}...`);
        await page.goto(targetUrl, { waitUntil: "networkidle", timeout: 60_000 });
        await session.execute({ type: "scroll_down" });
        await session.execute({ type: "scroll_down" });

        console.log("Extracting image URLs from rendered DOM...");
        const allUrls = await extractImageUrlsFromDom(page);

        const uniqueUrls = [
          ...new Set(allUrls.filter((url): url is string => typeof url === "string")),
        ].filter(isValidUrl);
        console.log(`Found ${uniqueUrls.length} unique image URL(s)`);

        const urls = uniqueUrls.slice(0, MAX_IMAGES);
        if (uniqueUrls.length > MAX_IMAGES) {
          console.log(`Capping at ${MAX_IMAGES} (adjust MAX_IMAGES to change this)`);
        }
        if (!urls.length) {
          console.log("No image URLs found on the page.");
          return;
        }

        const hostname = new URL(targetUrl).hostname || "unknown";
        const outputDir = join(OUTPUT_DIR, hostname);
        await mkdir(outputDir, { recursive: true });

        let saved = 0;
        let failed = 0;
        console.log(`\nDownloading ${urls.length} image(s) via browser context...\n`);

        for (const [index, url] of urls.entries()) {
          process.stdout.write(`[${index + 1}/${urls.length}] ${url} -> `);
          try {
            const { bytes, mimeType } = await fetchImageBytes(page, url);
            const filename = imageFilename(url, mimeType, index);
            await writeFile(join(outputDir, filename), bytes);
            console.log(`saved as ${filename} (${bytes.length} bytes)`);
            saved += 1;
          } catch (error) {
            console.log(
              `FAILED (${error instanceof Error ? error.message : String(error)}, skipping)`,
            );
            failed += 1;
          }
        }

        console.log(`\nDone! ${saved} saved, ${failed} failed -> ${outputDir}/`);
      } finally {
        await browser.close();
      }
    });

  console.log("Session closed successfully");
}

main().catch((error: unknown) => {
  console.error(`Error: ${error instanceof Error ? error.message : String(error)}`);
  console.error("Common issues:");
  console.error("  - Check .env has NOTTE_API_KEY");
  console.error("  - Verify the target URL is accessible");
  console.error("Docs: https://docs.notte.cc/");
  process.exit(1);
});
