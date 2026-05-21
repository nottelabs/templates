import { readFile, writeFile } from "node:fs/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { config as loadEnv } from "dotenv";
import { NotteClient, profileCreate, type ProfileResponse } from "notte-sdk";
import { z } from "zod";

const __dirname = dirname(fileURLToPath(import.meta.url));
loadEnv({ path: join(__dirname, ".env") });
loadEnv({ path: join(__dirname, "..", ".env") });

const BASE_URL = "https://apartment-board-demo-nine.vercel.app";
const LOGIN_URL = `${BASE_URL}/auth/signin`;
const STATE_FILE = join(__dirname, ".profile-state.json");

const RentalApplication = z.object({
  applicant: z.string().nullable().default(null),
  application_id: z.string().nullable().default(null),
  building: z.string().nullable().default(null),
  unit: z.string().nullable().default(null),
  income: z.string().nullable().default(null),
  move_in_date: z.string().nullable().default(null),
  status: z.string().nullable().default(null),
  submitted_date: z.string().nullable().default(null),
});

const RentalApplicationsData = z.object({
  applications: z.array(RentalApplication).default([]),
});

type ProfileState = {
  profile_id: string;
};

type RentalApplicationsData = z.infer<typeof RentalApplicationsData>;

async function loadState(): Promise<ProfileState | null> {
  try {
    return JSON.parse(await readFile(STATE_FILE, "utf8")) as ProfileState;
  } catch (error: unknown) {
    if ((error as NodeJS.ErrnoException).code === "ENOENT") {
      return null;
    }
    throw error;
  }
}

async function saveState(state: ProfileState): Promise<void> {
  await writeFile(STATE_FILE, `${JSON.stringify(state, null, 2)}\n`);
}

async function createProfile(client: NotteClient): Promise<ProfileResponse> {
  const response = await profileCreate({
    client: client.getClient(),
    body: { name: "Alder Apartments Profile Demo" },
  });

  if (response.error) {
    throw new Error(`Failed to create profile: ${JSON.stringify(response.error)}`);
  }

  return response.data as ProfileResponse;
}

async function printViewerUrl(session: { status: () => Promise<{ viewer_url?: string | null }> }) {
  const status = await session.status();
  if (status.viewer_url) {
    console.log(`Live View Link: ${status.viewer_url}`);
  }
}

async function setupProfile(client: NotteClient): Promise<ProfileState> {
  console.log("[setup] No saved profile state found. Creating a new Notte profile.");
  const profile = await createProfile(client);
  const profileId = profile.profile_id;
  console.log(`[setup] Created profile: ${profileId}`);
  console.log("[setup] Starting seed session with persist=true.");

  await client.Session({
    headless: true,
    idle_timeout_minutes: 3,
    max_duration_minutes: 15,
    profile: { id: profileId, persist: true },
  }).use(async (session) => {
    console.log(`[setup] Seed session started: ${session.getId()}`);
    console.log("[setup] Logging into Alder Apartments.");
    await session.execute({ type: "goto", url: LOGIN_URL });
    await session.execute({ type: "fill", selector: "input#username", value: "alder" });
    await session.execute({ type: "fill", selector: "input#password", value: "rentals123" });
    await session.execute({ type: "click", selector: "button[type='submit']" });
    await session.execute({ type: "wait", time_ms: 5000 });
    console.log("[setup] Login complete. Closing this session will persist cookies to the profile.");
  });

  const state = { profile_id: profileId };
  await saveState(state);
  console.log("[setup] Saved profile state to .profile-state.json.");
  return state;
}

async function scrapeApplications(session: {
  scrape: <T>(options: { instructions: string; response_format: z.ZodSchema<T> }) => Promise<T>;
}): Promise<RentalApplicationsData> {
  return session.scrape({
    instructions:
      "Extract the rental applications for the signed-in user. Return each application " +
      "with applicant, application id, building, unit, income, move-in date, status, " +
      "and submitted date.",
    response_format: RentalApplicationsData,
  });
}

async function run() {
  const client = new NotteClient({ apiKey: process.env.NOTTE_API_KEY });
  let state = await loadState();

  if (state) {
    console.log(`[setup] Reusing saved profile: ${state.profile_id}`);
  } else {
    state = await setupProfile(client);
    console.log("[setup] Waiting 5 seconds for the persisted profile state to become available.");
    await new Promise((resolve) => setTimeout(resolve, 5000));
  }

  console.log("[reuse] Starting application scrape session with persist=false.");
  return client.Session({
    headless: true,
    idle_timeout_minutes: 3,
    max_duration_minutes: 15,
    profile: { id: state.profile_id, persist: false },
  }).use(async (session) => {
    console.log(`[reuse] Scrape session started: ${session.getId()}`);
    await printViewerUrl(session);
    console.log("[reuse] Opening homepage and clicking Applications with the persisted profile.");
    await session.execute({ type: "goto", url: BASE_URL });
    await session.execute({ type: "click", selector: 'internal:role=link[name="Applications"i]' });
    await session.execute({ type: "wait", time_ms: 3000 });
    console.log("[reuse] Scraping rental applications from persisted profile session.");
    const applications = await scrapeApplications(session);
    console.log("[reuse] Scrape complete.");

    return {
      profile_id: state.profile_id,
      applications: applications.applications,
    };
  });
}

run()
  .then((result) => {
    console.log(JSON.stringify(result, null, 2));
  })
  .catch((error: unknown) => {
    console.error(`Error: ${error instanceof Error ? error.message : String(error)}`);
    console.error("\nCommon fixes:");
    console.error("  - Set NOTTE_API_KEY in your environment or .env file");
    console.error("  - Delete .profile-state.json to create and authenticate a fresh browser profile");
    process.exit(1);
  });
