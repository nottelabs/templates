import { readFile, writeFile } from "node:fs/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { config as loadEnv } from "dotenv";
import { NotteClient, type NottePersona } from "notte-sdk";
import { z } from "zod";

const __dirname = dirname(fileURLToPath(import.meta.url));
loadEnv({ path: join(__dirname, ".env") });
loadEnv({ path: join(__dirname, "..", ".env") });

const JOB_BOARD_URL = "https://job-board-demo-one.vercel.app/";
const STATE_FILE = join(__dirname, ".persona-state.json");
const VERIFY_LINK_PATTERN = /href="([^"]+)"/;

const Application = z.object({
  title: z.string().nullable().default(null),
  company: z.string().nullable().default(null),
  location: z.string().nullable().default(null),
  job_type: z.string().nullable().default(null),
  submitted_date: z.string().nullable().default(null),
  status: z.string().nullable().default(null),
});

const ApplicationsData = z.object({
  applications: z.array(Application).default([]),
});

type PersonaState = {
  persona_id: string;
  email: string;
  vault_id?: string | null;
};

type ApplicationsData = z.infer<typeof ApplicationsData>;

async function loadState(): Promise<PersonaState | null> {
  try {
    return JSON.parse(await readFile(STATE_FILE, "utf8")) as PersonaState;
  } catch (error: unknown) {
    if ((error as NodeJS.ErrnoException).code === "ENOENT") {
      return null;
    }
    throw error;
  }
}

async function saveState(state: PersonaState): Promise<void> {
  await writeFile(STATE_FILE, `${JSON.stringify(state, null, 2)}\n`);
}

function decodeHtml(value: string): string {
  return value
    .replace(/&amp;/g, "&")
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">");
}

async function latestVerifyLink(persona: NottePersona, attempts = 12): Promise<string> {
  for (let attempt = 0; attempt < attempts; attempt += 1) {
    const emails = await persona.emails({ limit: 10, only_unread: false });
    for (const message of emails) {
      const body = message.html_content ?? message.text_content ?? "";
      if (!body.includes("job-board-demo-one.vercel.app")) {
        continue;
      }

      const match = VERIFY_LINK_PATTERN.exec(body);
      if (match?.[1]) {
        return decodeHtml(match[1]);
      }
    }
    await new Promise((resolve) => setTimeout(resolve, 5000));
  }

  throw new Error("No job board sign-in email arrived for the persona.");
}

async function setupPersona(client: NotteClient): Promise<{ state: PersonaState; persona: NottePersona }> {
  const persona = client.Persona({ create_vault: true });
  await persona.emails({ limit: 1 });
  const info = persona.info;
  const state = {
    persona_id: info.persona_id,
    email: info.email,
    vault_id: info.vault_id,
  };
  await saveState(state);
  return { state, persona };
}

async function getPersona(client: NotteClient): Promise<{ state: PersonaState; persona: NottePersona }> {
  const existingState = await loadState();
  if (!existingState) {
    return setupPersona(client);
  }

  const persona = client.Persona({ persona_id: existingState.persona_id });
  await persona.emails({ limit: 1 });
  return { state: existingState, persona };
}

async function signInWithPersona(
  session: {
    execute: (action: unknown) => Promise<unknown>;
  },
  persona: NottePersona,
  state: PersonaState,
): Promise<void> {
  await session.execute({ type: "goto", url: JOB_BOARD_URL });
  await session.execute({ type: "click", selector: 'internal:role=button[name="Sign In"i]' });
  await session.execute({
    type: "fill",
    selector: 'internal:role=textbox[name="you@example.com"i]',
    value: state.email,
  });
  await session.execute({ type: "click", selector: 'internal:role=button[name="Send Sign-In Link"i]' });

  const verifyUrl = await latestVerifyLink(persona);
  await session.execute({ type: "goto", url: verifyUrl });
  await session.execute({ type: "wait", time_ms: 3000 });
}

async function openApplications(session: { execute: (action: unknown) => Promise<unknown> }) {
  await session.execute({ type: "click", selector: 'internal:role=button[name="Open account menu"i]' });
  await session.execute({ type: "click", selector: 'internal:role=menuitem[name="Applications"i]' });
  await session.execute({ type: "wait", time_ms: 3000 });
}

async function scrapeApplications(session: {
  scrape: <T>(options: { instructions: string; response_format: z.ZodSchema<T> }) => Promise<T>;
}): Promise<ApplicationsData> {
  return session.scrape({
    instructions:
      "Extract the signed-in user's applications. Return each application with title, " +
      "company, location, job type, submitted date, and status.",
    response_format: ApplicationsData,
  });
}

async function run() {
  const client = new NotteClient({ apiKey: process.env.NOTTE_API_KEY });
  const { state, persona } = await getPersona(client);

  return client.Session({
    headless: true,
    idle_timeout_minutes: 3,
    max_duration_minutes: 15,
  }).use(async (session) => {
    await signInWithPersona(session, persona, state);
    await openApplications(session);
    const applications = await scrapeApplications(session);

    return {
      persona_id: state.persona_id,
      email: state.email,
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
    console.error("  - Delete .persona-state.json to create a fresh persona");
    console.error("  - Wait a few seconds and rerun if Supabase email delivery is delayed");
    process.exit(1);
  });
