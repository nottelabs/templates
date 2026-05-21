import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { config as loadEnv } from "dotenv";
import { NotteClient } from "notte-sdk";
import { z } from "zod";

const __dirname = dirname(fileURLToPath(import.meta.url));
loadEnv({ path: join(__dirname, ".env") });
loadEnv({ path: join(__dirname, "..", ".env") });

const PACKAGE_NAME = process.argv[2] ?? process.env.PACKAGE_NAME ?? "react";
const NPM_PACKAGE_BASE_URL = "https://www.npmjs.com/package";
const WARMUP_URL = process.env.WARMUP_URL ?? "https://example.com";

const PackageOverview = z.object({
  package_name: z.string().nullable().default(null).describe("Package name shown by npm"),
  current_version: z.string().nullable().default(null).describe("Current published package version"),
  publish_status: z.string().nullable().default(null).describe("Public/private and published state"),
  weekly_downloads: z.number().nullable().default(null).describe("Weekly download count"),
  license: z.string().nullable().default(null).describe("Package license"),
  repository_link: z.string().nullable().default(null).describe("Repository URL"),
  homepage_link: z.string().nullable().default(null).describe("Homepage URL"),
  last_publish: z.string().nullable().default(null).describe("Last publish text"),
  dependency_count: z.number().nullable().default(null).describe("Dependency count visible on the tab"),
  dependent_count: z.number().nullable().default(null).describe("Dependent count visible on the tab"),
  version_count: z.number().nullable().default(null).describe("Version count visible on the tab"),
  maintainers: z.array(z.string()).default([]).describe("Visible maintainers or collaborators"),
  health_links: z.array(z.string()).default([]).describe("Visible health/security/tool links"),
});

const CodeMetadata = z.object({
  unpacked_size: z.string().nullable().default(null).describe("Unpacked package size"),
  total_files: z.number().nullable().default(null).describe("Total files in the package"),
  visible_top_level_files_or_folders: z.array(z.string()).default([]).describe("Visible top-level files and folders on npm's Code tab"),
  package_quality_details: z.record(z.string(), z.string()).default({}).describe("Visible links to third-party quality tools"),
});

const DependencyMetadata = z.object({
  dependencies_count: z.number().nullable().default(null).describe("Runtime dependency count"),
  dev_dependencies_count: z.number().nullable().default(null).describe("Dev dependency count"),
  dependencies: z.array(z.string()).default([]).describe("Visible runtime dependencies"),
  dev_dependencies: z.array(z.string()).default([]).describe("Visible dev dependencies"),
});

type PackageOverview = z.infer<typeof PackageOverview>;
type CodeMetadata = z.infer<typeof CodeMetadata>;
type DependencyMetadata = z.infer<typeof DependencyMetadata>;

function packageUrl(packageName: string, activeTab?: string): string {
  const encodedName = encodeURIComponent(packageName).replace("%40", "@").replace("%2F", "/");
  const url = `${NPM_PACKAGE_BASE_URL}/${encodedName}`;
  return activeTab ? `${url}?activeTab=${activeTab}` : url;
}

async function printViewerUrl(session: { status: () => Promise<{ viewer_url?: string | null }> }) {
  const status = await session.status();
  if (status.viewer_url) {
    console.log(`Live View: ${status.viewer_url}`);
  }
}

async function scrapeOverview(
  session: {
    execute: (action: unknown) => Promise<unknown>;
    scrape: <T>(options: { instructions: string; response_format: z.ZodSchema<T> }) => Promise<T>;
  },
  packageName: string,
): Promise<PackageOverview> {
  await session.execute({ type: "goto", url: packageUrl(packageName) });
  await session.execute({ type: "wait", time_ms: 1000 });
  return session.scrape({
    instructions:
      `Extract npm package health facts for package ${packageName}. ` +
      "Return the package name, current version, public/published state, weekly downloads, " +
      "license, repository link, homepage link, last publish text, dependency count, " +
      "dependent count, version count, maintainers/collaborators, and visible health, " +
      "security, provenance, bundle-size, dependency, or malware-report links.",
    response_format: PackageOverview,
  });
}

async function scrapeCodeMetadata(
  session: {
    execute: (action: unknown) => Promise<unknown>;
    scrape: <T>(options: { instructions: string; response_format: z.ZodSchema<T> }) => Promise<T>;
  },
  packageName: string,
): Promise<CodeMetadata> {
  await session.execute({ type: "goto", url: packageUrl(packageName, "code") });
  await session.execute({ type: "wait", time_ms: 1000 });
  return session.scrape({
    instructions:
      `On npm's Code tab for package ${packageName}, extract package file metadata: ` +
      "unpacked size, total file count, visible top-level files or folders, and links " +
      "to package quality tools such as Socket, Bundlephobia, Snyk, or npmgraph.",
    response_format: CodeMetadata,
  });
}

async function scrapeDependencyMetadata(
  session: {
    execute: (action: unknown) => Promise<unknown>;
    scrape: <T>(options: { instructions: string; response_format: z.ZodSchema<T> }) => Promise<T>;
  },
  packageName: string,
): Promise<DependencyMetadata> {
  await session.execute({ type: "goto", url: packageUrl(packageName, "dependencies") });
  await session.execute({ type: "wait", time_ms: 1000 });
  return session.scrape({
    instructions:
      `On npm's Dependencies tab for package ${packageName}, extract runtime and dev ` +
      "dependency counts plus any visible dependency names.",
    response_format: DependencyMetadata,
  });
}

function buildHealthReport(
  packageName: string,
  overview: PackageOverview,
  code: CodeMetadata,
  dependencies: DependencyMetadata,
) {
  const warnings: string[] = [];
  const dependencyCount = dependencies.dependencies_count ?? overview.dependency_count;

  if (!overview.repository_link) warnings.push("No repository link found");
  if (!overview.license) warnings.push("No license found");
  if (dependencyCount && dependencyCount > 20) warnings.push(`High runtime dependency count: ${dependencyCount}`);
  if (!overview.last_publish) warnings.push("No last publish signal found");

  return {
    package: packageName,
    status: warnings.length === 0 ? "pass" : "review",
    warnings,
    overview,
    code,
    dependencies,
  };
}

async function main() {
  const apiKey = process.env.NOTTE_API_KEY;
  if (!apiKey) {
    throw new Error("Missing NOTTE_API_KEY. Set it in your environment or .env file.");
  }

  const client = new NotteClient({ apiKey });

  const report = await client.Session({ idle_timeout_minutes: 3 }).use(async (session) => {
    console.log(`Session ID: ${session.getId()}`);
    await printViewerUrl(session);

    console.log(`Warming up browser with ${WARMUP_URL}...`);
    await session.execute({ type: "goto", url: WARMUP_URL });

    console.log(`Checking npm package: ${PACKAGE_NAME}`);
    const overview = await scrapeOverview(session, PACKAGE_NAME);
    const code = await scrapeCodeMetadata(session, PACKAGE_NAME);
    const dependencies = await scrapeDependencyMetadata(session, PACKAGE_NAME);
    return buildHealthReport(PACKAGE_NAME, overview, code, dependencies);
  });

  console.log(JSON.stringify(report, null, 2));
}

main().catch((error: unknown) => {
  console.error(`Error: ${error instanceof Error ? error.message : String(error)}`);
  console.error("Troubleshooting:");
  console.error("  - Set NOTTE_API_KEY in your environment or .env file");
  console.error("  - Try another package with: npm start -- <package-name>");
  console.error("  - npm may occasionally block first navigation; keep WARMUP_URL enabled");
  process.exit(1);
});
