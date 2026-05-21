import { readFile, writeFile } from "node:fs/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { config as loadEnv } from "dotenv";
import { NotteClient } from "notte-sdk";
import { z } from "zod";

const __dirname = dirname(fileURLToPath(import.meta.url));
loadEnv({ path: join(__dirname, ".env") });
loadEnv({ path: join(__dirname, "..", ".env") });

const BASE_URL = "https://apartment-board-demo-nine.vercel.app";
const LOGIN_URL = `${BASE_URL}/auth/signin`;
const STATE_FILE = join(__dirname, ".vault-state.json");
const USERNAME_PLACEHOLDER = "cooljohnny1567";
const PASSWORD_PLACEHOLDER = "mycoolpassword";

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

type VaultState = {
  vault_id: string;
};

type RentalApplicationsData = z.infer<typeof RentalApplicationsData>;

async function loadState(): Promise<VaultState | null> {
  try {
    return JSON.parse(await readFile(STATE_FILE, "utf8")) as VaultState;
  } catch (error: unknown) {
    if ((error as NodeJS.ErrnoException).code === "ENOENT") {
      return null;
    }
    throw error;
  }
}

async function saveState(state: VaultState): Promise<void> {
  await writeFile(STATE_FILE, `${JSON.stringify(state, null, 2)}\n`);
}

async function setupVault(client: NotteClient): Promise<VaultState> {
  console.log("[setup] Creating Alder Apartments demo vault.");
  const vault = client.Vault({ name: "Alder Apartments Demo" });
  await vault.addCredentials(LOGIN_URL, {
    username: "alder",
    password: "rentals123",
  });

  const state = { vault_id: vault.vaultId };
  await saveState(state);
  console.log("[setup] Saved vault state to .vault-state.json.");
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

async function printViewerUrl(session: { status: () => Promise<{ viewer_url?: string | null }> }) {
  const status = await session.status();
  if (status.viewer_url) {
    console.log(`Live View Link: ${status.viewer_url}`);
  }
}

async function run() {
  const client = new NotteClient({ apiKey: process.env.NOTTE_API_KEY });
  const state = (await loadState()) ?? (await setupVault(client));

  return client.Session({
    headless: true,
    idle_timeout_minutes: 3,
    max_duration_minutes: 15,
    vault_id: state.vault_id,
  }).use(async (session) => {
    console.log(`Session started: ${session.getId()}`);
    await printViewerUrl(session);
    await session.execute({ type: "goto", url: BASE_URL });
    await session.execute({ type: "click", selector: 'internal:role=link[name="Log In"i]' });
    await session.observe();
    await session.execute({
      type: "form_fill",
      value: { username: USERNAME_PLACEHOLDER, password: PASSWORD_PLACEHOLDER },
    });
    await session.execute({ type: "click", selector: 'internal:role=button[name="Log In"i]' });
    await session.execute({ type: "wait", time_ms: 3000 });
    const applications = await scrapeApplications(session);

    return {
      vault_id: state.vault_id,
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
    console.error("  - Delete .vault-state.json to recreate the vault and demo credentials");
    process.exit(1);
  });
