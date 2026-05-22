import { mkdir, writeFile } from "node:fs/promises";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { config as loadEnv } from "dotenv";
import { NotteClient } from "notte-sdk";
import { z } from "zod";

const __dirname = dirname(fileURLToPath(import.meta.url));
loadEnv({ path: join(__dirname, ".env") });
loadEnv({ path: join(__dirname, "..", ".env") });

const ARXIV_HOME_URL = "https://arxiv.org/";
const ARXIV_AI_LINK_SELECTOR = 'internal:role=link[name="Computing Research Repository Artificial Intelligence"i]';
const DEFAULT_CATEGORY = "cs.AI";
const DEFAULT_RESULT_INDEX = Number.parseInt(process.env.RESULT_INDEX ?? "1", 10);
const DEFAULT_DOWNLOAD_DIR = process.env.DOWNLOAD_DIR ?? "./downloads/arxiv";

const RECENT_LIST_RESULT_JS = `(resultIndex) => {
  const terms = Array.from(document.querySelectorAll("dl dt"));
  const term = terms[resultIndex];
  const details = term?.nextElementSibling?.matches("dd") ? term.nextElementSibling : null;
  const abs = term?.querySelector("a[href*='/abs/']");
  if (!abs || !term || !details) {
    return {
      url: location.href,
      error: "selected result not found",
      available_results: terms.length
    };
  }

  const pdf = term.querySelector("a[href*='/pdf/']");
  const abstractUrl = new URL(abs.getAttribute("href"), location.href).href;
  const arxivId =
    abstractUrl.match(/\\/abs\\/([^?#]+)/)?.[1] ||
    abs.textContent.replace(/^\\s*arXiv:\\s*/i, "").trim() ||
    null;
  const cleanPrefixed = (selector, prefixPattern) => details.querySelector(selector)?.textContent
    ?.replace(prefixPattern, "")
    ?.replace(/\\s+/g, " ")
    ?.trim() || null;

  return {
    url: location.href,
    available_results: terms.length,
    result_count_text: document.querySelector("h3")?.textContent.replace(/\\s+/g, " ").trim() || null,
    title: cleanPrefixed(".list-title", /^\\s*Title:\\s*/i),
    authors: Array.from(details.querySelectorAll(".list-authors a")).map((a) => a.textContent.trim()),
    arxiv_id: arxivId,
    abstract_url: abstractUrl,
    pdf_url: pdf ? new URL(pdf.getAttribute("href"), location.href).href : abstractUrl.replace("/abs/", "/pdf/"),
    submitted_date: document.querySelector("h3")?.textContent.replace(/\\s+/g, " ").trim() || null,
    subjects: (cleanPrefixed(".list-subjects", /^\\s*Subjects?:\\s*/i) || "")
      .split(";")
      .map((subject) => subject.trim())
      .filter(Boolean),
    abstract_snippet: cleanPrefixed(".list-comments", /^\\s*Comments?:\\s*/i)
  };
}`;

const OPEN_RECENT_ARTICLE_JS = `(resultIndex) => {
  const links = Array.from(document.querySelectorAll("a[href*='/abs/']"));
  const first = links[resultIndex];
  if (!first) {
    return {
      ok: false,
      url: location.href,
      error: "No abstract links found",
      available_results: links.length
    };
  }

  const href = new URL(first.getAttribute("href"), location.href).href;
  first.click();
  return { ok: true, href, text: first.textContent.trim() };
}`;

const ARTICLE_DETAILS_JS = `() => {
  const pdf = document.querySelector("a[href*='/pdf/']");
  const abstract = document.querySelector("blockquote.abstract")?.textContent
    ?.replace(/^\\s*Abstract:\\s*/, "")
    ?.replace(/\\s+/g, " ")
    ?.trim() || null;

  return {
    url: location.href,
    title: document.querySelector("h1.title")?.textContent
      ?.replace(/^\\s*Title:\\s*/, "")
      ?.replace(/\\s+/g, " ")
      ?.trim() || null,
    authors: Array.from(document.querySelectorAll(".authors a")).map((a) => a.textContent.trim()),
    arxiv_id: location.pathname.split("/").pop(),
    abstract_url: location.href,
    pdf_url: pdf ? new URL(pdf.getAttribute("href"), location.href).href : null,
    submitted_date: document.querySelector(".dateline")?.textContent?.replace(/\\s+/g, " ").trim() || null,
    subjects: Array.from(document.querySelectorAll(".subjects .primary-subject, .subjects a"))
      .map((subject) => subject.textContent.trim()),
    abstract
  };
}`;

const PaperResult = z.object({
  title: z.string().nullable().default(null).describe("Paper title."),
  authors: z.array(z.string()).default([]).describe("Paper authors."),
  arxiv_id: z.string().nullable().default(null).describe("arXiv identifier, for example 2605.07507."),
  abstract_url: z.string().nullable().default(null).describe("Link to the abstract page."),
  pdf_url: z.string().nullable().default(null).describe("Link to the PDF."),
  submitted_date: z.string().nullable().default(null).describe("Submission date shown in recent results."),
  subjects: z.array(z.string()).default([]).describe("arXiv subject tags."),
  abstract_snippet: z.string().nullable().default(null).describe("Short visible abstract snippet."),
});

const ArticleDetails = z.object({
  title: z.string().nullable().default(null).describe("Paper title from the arXiv article page."),
  authors: z.array(z.string()).default([]).describe("Paper authors from the arXiv article page."),
  arxiv_id: z.string().nullable().default(null).describe("arXiv identifier."),
  abstract_url: z.string().nullable().default(null).describe("Current abstract page URL."),
  pdf_url: z.string().nullable().default(null).describe("PDF URL from the article page."),
  submitted_date: z.string().nullable().default(null).describe("Submission date."),
  subjects: z.array(z.string()).default([]).describe("arXiv subject tags."),
  abstract: z.string().nullable().default(null).describe("Full visible abstract text."),
});

const LocalDownload = z.object({
  storage_name: z.string().describe("Downloaded filename."),
  local_path: z.string().describe("Local path where the file was downloaded."),
  downloaded: z.boolean().describe("Whether the file was saved locally."),
});

const ArxivDownloadReport = z.object({
  category: z.string().default(DEFAULT_CATEGORY).describe("arXiv category that was opened."),
  result_index: z.number().default(1).describe("1-based recent article index selected for download."),
  result_count_text: z.string().nullable().default(null).describe("Visible recent-submissions count text."),
  selected_result: PaperResult.nullable().default(null).describe("Selected recent result."),
  article: ArticleDetails.nullable().default(null).describe("Metadata extracted from the article page."),
  downloaded_files: z.array(LocalDownload).default([]).describe("Files downloaded into the local download directory."),
});

type PaperResult = z.infer<typeof PaperResult>;
type ArticleDetails = z.infer<typeof ArticleDetails>;
type LocalDownload = z.infer<typeof LocalDownload>;
type ArxivDownloadReport = z.infer<typeof ArxivDownloadReport>;

function parseArgs() {
  const args = process.argv.slice(2);
  let resultIndex = DEFAULT_RESULT_INDEX;
  let downloadDir = DEFAULT_DOWNLOAD_DIR;

  for (let index = 0; index < args.length; index += 1) {
    const arg = args[index];
    if (arg === "--result-index") {
      resultIndex = Number.parseInt(args[++index] ?? String(resultIndex), 10);
    } else if (arg === "--download-dir") {
      downloadDir = args[++index] ?? downloadDir;
    }
  }

  return { resultIndex, downloadDir };
}

function validateResultIndex(resultIndex: number): number {
  if (!Number.isFinite(resultIndex) || resultIndex < 1) {
    throw new Error("result index must be at least 1");
  }
  return resultIndex;
}

async function printViewerUrl(session: { status: () => Promise<{ viewer_url?: string | null }> }) {
  const status = await session.status();
  if (status.viewer_url) {
    console.log(`Live view: ${status.viewer_url}`);
  }
}

function firstJsonObject(text: string): string | null {
  const start = text.indexOf("{");
  const end = text.lastIndexOf("}");
  return start >= 0 && end > start ? text.slice(start, end + 1) : null;
}

function coerceJsonDict(candidate: unknown): Record<string, any> | null {
  if (candidate === null || candidate === undefined) {
    return null;
  }
  if (typeof candidate === "string") {
    const stripped = candidate.trim().replace(/^```(?:json)?/, "").replace(/```$/, "").trim();
    for (const value of [stripped, firstJsonObject(stripped)]) {
      if (!value) {
        continue;
      }
      try {
        const parsed = JSON.parse(value);
        if (parsed && typeof parsed === "object" && !Array.isArray(parsed)) {
          return parsed;
        }
      } catch {
        continue;
      }
    }
    return null;
  }
  if (typeof candidate !== "object" || Array.isArray(candidate)) {
    return null;
  }
  for (const key of ["result", "value", "output", "data", "structured", "json", "markdown", "message"]) {
    const nested = (candidate as Record<string, unknown>)[key];
    const parsed = coerceJsonDict(nested);
    if (parsed) {
      return parsed;
    }
  }
  return candidate as Record<string, any>;
}

async function evaluateJson(session: { execute: (action: any) => Promise<any> }, code: string, ...args: unknown[]) {
  const executable = args.length ? `(${code})(${args.map((arg) => JSON.stringify(arg)).join(", ")})` : `(${code})()`;
  const result = await session.execute({ type: "evaluate_js", code: executable });
  const data = coerceJsonDict(result);
  if (!data) {
    throw new Error(`Could not parse evaluate_js result: ${JSON.stringify(result)}`);
  }
  if (data.error) {
    throw new Error(`${data.error} on ${data.url ?? "current page"}`);
  }
  return data;
}

async function extractRecentListResult(session: { execute: (action: any) => Promise<any> }, resultIndex: number) {
  const data = await evaluateJson(session, RECENT_LIST_RESULT_JS, resultIndex - 1);
  const selected = PaperResult.parse({
    title: data.title ?? null,
    authors: data.authors ?? [],
    arxiv_id: data.arxiv_id ?? null,
    abstract_url: data.abstract_url ?? null,
    pdf_url: data.pdf_url ?? null,
    submitted_date: data.submitted_date ?? null,
    subjects: data.subjects ?? [],
    abstract_snippet: data.abstract_snippet ?? null,
  });
  return { resultCountText: data.result_count_text ?? null, selected };
}

async function openRecentArticle(session: { execute: (action: any) => Promise<any> }, resultIndex: number) {
  const data = await evaluateJson(session, OPEN_RECENT_ARTICLE_JS, resultIndex - 1);
  if (!data.ok) {
    throw new Error(`${data.error ?? "could not open recent article"} on ${data.url ?? "current page"}`);
  }
}

async function extractArticleDetails(session: { execute: (action: any) => Promise<any> }, selected: PaperResult): Promise<ArticleDetails> {
  const data = await evaluateJson(session, ARTICLE_DETAILS_JS);
  return ArticleDetails.parse({
    title: data.title ?? selected.title,
    authors: data.authors ?? selected.authors,
    arxiv_id: data.arxiv_id ?? selected.arxiv_id,
    abstract_url: data.abstract_url ?? selected.abstract_url,
    pdf_url: data.pdf_url ?? selected.pdf_url,
    submitted_date: data.submitted_date ?? selected.submitted_date,
    subjects: data.subjects ?? selected.subjects,
    abstract: data.abstract ?? selected.abstract_snippet,
  });
}

function selectedAbstractUrl(selected: PaperResult): string {
  if (selected.abstract_url) {
    return selected.abstract_url;
  }
  if (selected.arxiv_id) {
    return `https://arxiv.org/abs/${selected.arxiv_id}`;
  }
  throw new Error("selected result did not include an abstract URL or arXiv ID");
}

async function downloadPdf(pdfUrl: string, article: ArticleDetails, downloadDir: string): Promise<LocalDownload[]> {
  await mkdir(downloadDir, { recursive: true });
  const response = await fetch(pdfUrl);
  if (!response.ok) {
    throw new Error(`PDF download failed with HTTP ${response.status}`);
  }
  const bytes = Buffer.from(await response.arrayBuffer());
  const fallbackName = article.arxiv_id ? `${article.arxiv_id.replace(/[^a-zA-Z0-9_.-]/g, "_")}.pdf` : "arxiv-paper.pdf";
  const filename = pdfUrl.split("/").pop()?.replace(/[^a-zA-Z0-9_.-]/g, "_") || fallbackName;
  const localPath = resolve(downloadDir, filename.endsWith(".pdf") ? filename : `${filename}.pdf`);
  await writeFile(localPath, bytes);
  return [LocalDownload.parse({ storage_name: filename, local_path: localPath, downloaded: true })];
}

async function findAndDownloadPaper(
  resultIndex: number,
  downloadDir: string,
): Promise<ArxivDownloadReport> {
  const index = validateResultIndex(resultIndex);
  const client = new NotteClient({ apiKey: process.env.NOTTE_API_KEY });

  const report: ArxivDownloadReport = {
    category: DEFAULT_CATEGORY,
    result_index: index,
    result_count_text: null,
    selected_result: null,
    article: null,
    downloaded_files: [],
  };

  await client.Session({ open_viewer: true, idle_timeout_minutes: 3, proxies: true, use_file_storage: true }).use(async (session) => {
    console.log(`Session ID: ${session.getId()}`);
    await printViewerUrl(session);
    console.log("Opening arXiv Computing Research Repository Artificial Intelligence...");

    await session.execute({ type: "goto", url: ARXIV_HOME_URL });
    await session.execute({ type: "click", selector: ARXIV_AI_LINK_SELECTOR, timeout: 15000 });
    await session.execute({ type: "wait", time_ms: 1000 });

    const extracted = await extractRecentListResult(session, index);
    report.result_count_text = extracted.resultCountText;
    report.selected_result = extracted.selected;

    console.log(`Opening recent article ${index}: ${selectedAbstractUrl(extracted.selected)}`);
    await openRecentArticle(session, index);
    await session.execute({ type: "wait", time_ms: 1000 });

    report.article = await extractArticleDetails(session, extracted.selected);
  });

  const pdfUrl = report.article?.pdf_url ?? report.selected_result?.pdf_url;
  if (!pdfUrl || !report.article) {
    throw new Error("selected article did not include a PDF URL");
  }

  console.log(`Downloading PDF: ${pdfUrl}`);
  report.downloaded_files = await downloadPdf(pdfUrl, report.article, downloadDir);
  return ArxivDownloadReport.parse(report);
}

async function main() {
  const args = parseArgs();
  const report = await findAndDownloadPaper(args.resultIndex, args.downloadDir);
  console.log(JSON.stringify(report, null, 2));
}

main().catch((error: unknown) => {
  console.error(`Error downloading an arXiv paper: ${error instanceof Error ? error.message : String(error)}`);
  console.error("Common fixes:");
  console.error("  - Set NOTTE_API_KEY in your environment or .env file");
  console.error("  - Use --result-index to choose a different recent article if the selected paper has no PDF link");
  process.exit(1);
});
