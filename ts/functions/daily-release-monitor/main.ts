import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { config as loadEnv } from "dotenv";
import { NotteClient } from "notte-sdk";
import { z } from "zod";

const __dirname = dirname(fileURLToPath(import.meta.url));
loadEnv({ path: join(__dirname, ".env") });
loadEnv({ path: join(__dirname, "..", ".env") });

const DEFAULT_TARGET = "https://github.com/nottelabs/notte";

const ReleaseInfo = z.object({
  name: z.string().nullable().default(null).describe("Project, repo, or package name"),
  version: z.string().nullable().default(null).describe("Latest visible release, tag, or package version"),
  published_at: z.string().nullable().default(null).describe("Visible publish or release date"),
  url: z.string().nullable().default(null).describe("URL for the release or package page"),
  summary: z.string().nullable().default(null).describe("Short release summary"),
  notes: z.array(z.string()).default([]).describe("Important release notes or visible changes"),
});

const MonitorResult = z.object({
  target: z.string(),
  target_type: z.string(),
  latest: ReleaseInfo,
  previous_version: z.string().nullable().default(null),
  has_new_release: z.boolean().nullable().default(null),
});

type ReleaseInfo = z.infer<typeof ReleaseInfo>;
type MonitorResult = z.infer<typeof MonitorResult>;

function normalizeGithubRepo(target: string): string {
  const parsed = new URL(target.trim());
  if (parsed.hostname !== "github.com") {
    throw new Error("GitHub targets must point to github.com.");
  }

  const parts = parsed.pathname.split("/").filter(Boolean);
  if (parts.length < 2) {
    throw new Error("GitHub targets must include an owner and repository name.");
  }

  return `https://github.com/${parts[0]}/${parts[1]}`;
}

function normalizeNpmPackage(target: string) {
  const trimmed = target.trim();
  let packageName: string;
  if (trimmed.startsWith("npm:")) {
    packageName = trimmed.slice("npm:".length).trim();
  } else {
    try {
      const parsed = new URL(trimmed);
      packageName = parsed.hostname === "www.npmjs.com" ? parsed.pathname.replace(/^\/package\//, "").replace(/^\/|\/$/g, "") : trimmed;
    } catch {
      packageName = trimmed;
    }
  }

  if (!packageName) {
    throw new Error("npm target must include a package name.");
  }

  return {
    packageName,
    packageUrl: `https://www.npmjs.com/package/${encodeURIComponent(packageName).replace("%40", "@").replace("%2F", "/")}`,
  };
}

function detectTargetType(target: string): "github" | "npm" {
  const trimmed = target.trim();
  if (trimmed.startsWith("npm:")) {
    return "npm";
  }
  try {
    const parsed = new URL(trimmed);
    if (parsed.hostname === "www.npmjs.com") {
      return "npm";
    }
    if (parsed.hostname === "github.com") {
      return "github";
    }
  } catch {
    if (!trimmed.includes("/") && !trimmed.includes(".")) {
      return "npm";
    }
  }
  throw new Error("Target must be a GitHub repository URL, npm package URL, or npm:<package>.");
}

async function scrapeGithubRelease(
  session: {
    execute: (action: any) => Promise<any>;
    scrape: <T>(options: { instructions: string; response_format: z.ZodSchema<T> }) => Promise<T>;
  },
  repoUrl: string,
): Promise<ReleaseInfo> {
  const releasesUrl = `${repoUrl}/releases`;
  await session.execute({ type: "goto", url: releasesUrl });
  await session.execute({ type: "wait", time_ms: 1000 });
  await session.execute({ type: "scroll_down" });
  await session.execute({ type: "scroll_up" });
  return session.scrape({
    instructions:
      "Extract the latest GitHub release. Return the repository name, latest release tag or version, " +
      "publish date, release URL, a short summary, and up to 8 important visible release note bullets.",
    response_format: ReleaseInfo,
  });
}

async function scrapeNpmRelease(
  session: {
    execute: (action: any) => Promise<any>;
    scrape: <T>(options: { instructions: string; response_format: z.ZodSchema<T> }) => Promise<T>;
  },
  packageName: string,
  packageUrl: string,
): Promise<ReleaseInfo> {
  await session.execute({ type: "goto", url: packageUrl });
  await session.execute({ type: "wait", time_ms: 1000 });
  const release = await session.scrape({
    instructions:
      `Extract the latest npm package release information for ${packageName}. Return the package name, ` +
      "current version, last publish date or relative publish text, package URL, a short summary, " +
      "and any visible publish or health notes.",
    response_format: ReleaseInfo,
  });

  return ReleaseInfo.parse({
    ...release,
    url: release.url ?? packageUrl,
    name: release.name ?? packageName,
  });
}

export async function run(
  target: string = DEFAULT_TARGET,
  previous_version: string | null = null,
): Promise<MonitorResult> {
  const client = new NotteClient({ apiKey: process.env.NOTTE_API_KEY });
  const targetType = detectTargetType(target);
  let normalizedTarget: string;
  let latest: ReleaseInfo;

  await client
    .Session({
      headless: true,
      idle_timeout_minutes: 2,
      max_duration_minutes: 10,
      open_viewer: true,
    })
    .use(async (session) => {
      if (targetType === "github") {
        normalizedTarget = normalizeGithubRepo(target);
        latest = await scrapeGithubRelease(session, normalizedTarget);
      } else {
        const normalized = normalizeNpmPackage(target);
        normalizedTarget = normalized.packageUrl;
        latest = await scrapeNpmRelease(session, normalized.packageName, normalized.packageUrl);
      }
    });

  return MonitorResult.parse({
    target: normalizedTarget!,
    target_type: targetType,
    latest: latest!,
    previous_version,
    has_new_release: previous_version ? latest!.version !== previous_version : null,
  });
}

async function main() {
  const target = process.env.RELEASE_MONITOR_TARGET ?? DEFAULT_TARGET;
  const previousVersion = process.env.PREVIOUS_RELEASE_VERSION || null;
  console.log(JSON.stringify(await run(target, previousVersion), null, 2));
}

main().catch((error: unknown) => {
  console.error(`Error: ${error instanceof Error ? error.message : String(error)}`);
  console.error("\nCommon fixes:");
  console.error("  - Set NOTTE_API_KEY in your environment or .env file");
  console.error("  - Use a GitHub repo URL, npm package URL, or npm:<package>");
  console.error("  - For Functions, deploy with: notte functions create --file main.ts");
  process.exit(1);
});
