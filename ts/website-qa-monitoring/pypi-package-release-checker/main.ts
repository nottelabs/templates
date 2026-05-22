import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { config as loadEnv } from "dotenv";
import { NotteClient } from "notte-sdk";
import { z } from "zod";

const __dirname = dirname(fileURLToPath(import.meta.url));
loadEnv({ path: join(__dirname, ".env") });
loadEnv({ path: join(__dirname, "..", ".env") });

const DEFAULT_PACKAGE_NAME = process.env.PACKAGE_NAME ?? "requests";
const KNOWN_VERSION = process.env.KNOWN_VERSION;
const USE_PROXY = !["0", "false", "no"].includes((process.env.USE_PROXY ?? "true").toLowerCase());

const ReleaseFile = z.object({
  filename: z.string(),
  package_type: z.string().nullable().default(null),
  python_version: z.string().nullable().default(null),
  size: z.number().nullable().default(null),
  upload_time_iso_8601: z.string().nullable().default(null),
  requires_python: z.string().nullable().default(null),
});

const PypiPayload = z.object({
  info: z.object({
    name: z.string().nullable().optional(),
    version: z.string(),
    summary: z.string().nullable().optional(),
    requires_python: z.string().nullable().optional(),
    license: z.string().nullable().optional(),
    project_urls: z.record(z.string(), z.string()).nullable().optional(),
  }),
  releases: z.record(z.string(), z.array(ReleaseFile)).default({}),
  urls: z.array(ReleaseFile).default([]),
});

type ReleaseFile = z.infer<typeof ReleaseFile>;
type PypiPayload = z.infer<typeof PypiPayload>;

function normalizedPackagePath(packageName: string): string {
  const trimmed = packageName.trim();
  if (!trimmed) {
    throw new Error("Package name cannot be empty");
  }
  return encodeURIComponent(trimmed);
}

async function printViewerUrl(session: { status: () => Promise<{ viewer_url?: string | null }> }) {
  const status = await session.status();
  if (status.viewer_url) {
    console.log(`Live View Link: ${status.viewer_url}`);
  }
}

async function fetchPackageJson(apiUrl: string): Promise<PypiPayload> {
  const response = await fetch(apiUrl, { headers: { Accept: "application/json" } });
  if (!response.ok) {
    throw new Error(`PyPI JSON request failed with ${response.status}`);
  }
  return PypiPayload.parse(await response.json());
}

function releaseDatetime(files: ReleaseFile[]): string | null {
  const timestamps = files
    .map((file) => file.upload_time_iso_8601)
    .filter((timestamp): timestamp is string => Boolean(timestamp));
  return timestamps.length > 0 ? timestamps.sort()[0] : null;
}

function versionParts(version: string): Array<number | string> {
  return version
    .split(/[.+!_-]/)
    .flatMap((part) => part.match(/\d+|[a-zA-Z]+/g) ?? [])
    .map((part) => (/^\d+$/.test(part) ? Number.parseInt(part, 10) : part.toLowerCase()));
}

function isNewerVersion(latestVersion: string, knownVersion: string | undefined): boolean | null {
  if (!knownVersion) return null;
  const latest = versionParts(latestVersion);
  const known = versionParts(knownVersion);
  const length = Math.max(latest.length, known.length);

  for (let index = 0; index < length; index += 1) {
    const left = latest[index] ?? 0;
    const right = known[index] ?? 0;
    if (left === right) continue;
    if (typeof left === "number" && typeof right === "number") return left > right;
    return String(left) > String(right);
  }

  return false;
}

function buildReport(payload: PypiPayload, packageName: string, projectUrl: string, apiUrl: string) {
  const latestVersion = payload.info.version;
  const latestFiles = payload.releases[latestVersion] ?? payload.urls;

  return {
    package_name: payload.info.name ?? packageName,
    project_url: projectUrl,
    api_url: apiUrl,
    summary: payload.info.summary ?? null,
    latest_version: latestVersion,
    latest_release_date: releaseDatetime(latestFiles),
    requires_python:
      payload.info.requires_python ??
      latestFiles.find((file) => file.requires_python)?.requires_python ??
      null,
    license: payload.info.license || null,
    project_urls: payload.info.project_urls ?? {},
    release_files: latestFiles,
    known_version: KNOWN_VERSION ?? null,
    is_newer_than_known: isNewerVersion(latestVersion, KNOWN_VERSION),
  };
}

async function checkPackageRelease(packageName: string) {
  const packagePath = normalizedPackagePath(packageName);
  const projectUrl = `https://pypi.org/project/${packagePath}/`;
  const apiUrl = `https://pypi.org/pypi/${packagePath}/json`;
  const apiKey = process.env.NOTTE_API_KEY;
  if (!apiKey) {
    throw new Error("Missing NOTTE_API_KEY. Set it in your environment or .env file.");
  }

  const client = new NotteClient({ apiKey });

  return client.Session({
    open_viewer: true,
    idle_timeout_minutes: 2,
    proxies: USE_PROXY,
    use_file_storage: true,
  }).use(async (session) => {
    console.log("Notte session initialized successfully");
    console.log(`Session ID: ${session.getId()}`);
    await printViewerUrl(session);

    console.log(`Opening PyPI project page: ${projectUrl}`);
    await session.execute({ type: "goto", url: projectUrl });
    await session.execute({ type: "wait", time_ms: 1000 });

    console.log(`Fetching release metadata: ${apiUrl}`);
    const payload = await fetchPackageJson(apiUrl);
    return buildReport(payload, packageName, projectUrl, apiUrl);
  });
}

async function main() {
  const packageName = process.argv[2] ?? DEFAULT_PACKAGE_NAME;
  console.log(`Starting PyPI release check at ${new Date().toISOString()}`);
  const report = await checkPackageRelease(packageName);

  console.log("\nLatest release:");
  console.log(JSON.stringify(report, null, 2));

  if (report.known_version) {
    const status = report.is_newer_than_known ? "new release available" : "no newer release found";
    console.log(`\nCompared with KNOWN_VERSION=${report.known_version}: ${status}`);
  }
}

main().catch((error: unknown) => {
  console.error(`Error in PyPI release checker: ${error instanceof Error ? error.message : String(error)}`);
  console.error("Common issues:");
  console.error("  - Check .env has NOTTE_API_KEY");
  console.error("  - Verify PACKAGE_NAME exists on PyPI");
  console.error("  - Keep USE_PROXY=true if PyPI blocks direct browser traffic");
  process.exit(1);
});
