import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { config as loadEnv } from "dotenv";
import { NotteClient } from "notte-sdk";
import { z } from "zod";

const __dirname = dirname(fileURLToPath(import.meta.url));
loadEnv({ path: join(__dirname, ".env") });
loadEnv({ path: join(__dirname, "..", ".env") });

const COMPANY_QUERY = process.env.COMPANY_QUERY ?? "AAPL";
const SEC_HOME_URL = "https://www.sec.gov/";
const SEC_COMPANY_TICKERS_URL = "https://www.sec.gov/files/company_tickers_exchange.json";
const SEC_COMPANY_BROWSE_URL = "https://www.sec.gov/edgar/browse/?CIK=";
const SEC_SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK";
const HTTP_HEADERS = {
  "User-Agent": "bb-templates-notte-business-lookup/1.0 contact@example.com",
};

const VisibleCompanyProfile = z.object({
  company_name: z
    .string()
    .nullable()
    .default(null)
    .describe("Company name shown on the SEC company page"),
  cik: z.string().nullable().default(null).describe("SEC Central Index Key"),
  ticker_symbols: z
    .string()
    .nullable()
    .default(null)
    .describe("Ticker symbols shown on the SEC company page"),
  exchanges: z
    .string()
    .nullable()
    .default(null)
    .describe("Exchanges shown on the SEC company page"),
  sic: z
    .string()
    .nullable()
    .default(null)
    .describe("SIC code and description shown on the SEC company page"),
  fiscal_year_end: z
    .string()
    .nullable()
    .default(null)
    .describe("Fiscal year end shown on the SEC company page"),
  state_of_incorporation: z
    .string()
    .nullable()
    .default(null)
    .describe("State or jurisdiction shown on the page"),
  business_address: z
    .string()
    .nullable()
    .default(null)
    .describe("Business address shown on the SEC company page"),
  mailing_address: z
    .string()
    .nullable()
    .default(null)
    .describe("Mailing address shown on the SEC company page"),
  phone: z.string().nullable().default(null).describe("Phone number shown on the SEC company page"),
});

type VisibleCompanyProfile = z.infer<typeof VisibleCompanyProfile>;

type SecTickerRecord = {
  cik?: string | number;
  name?: string;
  ticker?: string;
  exchange?: string;
};

type SecAddress = {
  street1?: string;
  street2?: string;
  city?: string;
  stateOrCountry?: string;
  zipCode?: string;
};

type SecSubmission = {
  name?: string;
  cik?: string | number;
  tickers?: string[];
  exchanges?: string[];
  entityType?: string;
  sic?: string;
  sicDescription?: string;
  stateOfIncorporation?: string;
  stateOfIncorporationDescription?: string;
  fiscalYearEnd?: string;
  addresses?: {
    business?: SecAddress;
    mailing?: SecAddress;
  };
  phone?: string;
  filings?: {
    recent?: Record<string, string[]>;
  };
};

function normalizeCik(value: string | number | null | undefined): string {
  const digits = String(value ?? "").replace(/\D/g, "");
  if (!digits) {
    throw new Error("Could not read a CIK");
  }

  return digits.padStart(10, "0");
}

async function fetchJson<T>(url: string): Promise<T> {
  const response = await fetch(url, { headers: HTTP_HEADERS });
  if (!response.ok) {
    throw new Error(`${url} request failed with ${response.status}`);
  }

  return (await response.json()) as T;
}

async function resolveCik(companyQuery: string): Promise<string> {
  if (/^\s*\d{1,10}\s*$/.test(companyQuery)) {
    return normalizeCik(companyQuery);
  }

  const payload = await fetchJson<{ fields?: string[]; data?: unknown[][] }>(
    SEC_COMPANY_TICKERS_URL,
  );
  const fields = payload.fields ?? [];
  const rows = payload.data ?? [];
  const records = rows.map((row) =>
    Object.fromEntries(fields.map((field, index) => [field, row[index]])),
  ) as SecTickerRecord[];
  const normalizedQuery = companyQuery.trim().toLowerCase();

  const match =
    records.find((record) => String(record.ticker ?? "").toLowerCase() === normalizedQuery) ??
    records.find((record) => String(record.name ?? "").toLowerCase() === normalizedQuery) ??
    records.find((record) =>
      String(record.name ?? "")
        .toLowerCase()
        .includes(normalizedQuery),
    );

  if (!match) {
    throw new Error(`No SEC ticker dataset match found for query: ${companyQuery}`);
  }

  return normalizeCik(match.cik);
}

async function scrapeVisibleProfile(session: {
  scrape: <T>(options: { instructions: string; response_format: z.ZodSchema<T> }) => Promise<T>;
}): Promise<VisibleCompanyProfile> {
  return session.scrape({
    instructions:
      "Extract the SEC company profile header from this page. Return company_name, CIK, " +
      "ticker symbols, exchanges, SIC, fiscal year end, state of incorporation, " +
      "business address, mailing address, and phone. Do not include the filings table.",
    response_format: VisibleCompanyProfile,
  });
}

async function fetchSubmission(cik: string): Promise<SecSubmission> {
  return fetchJson<SecSubmission>(`${SEC_SUBMISSIONS_URL}${cik}.json`);
}

function formatAddress(address: SecAddress | undefined): string | null {
  if (!address) {
    return null;
  }

  const parts = [
    address.street1,
    address.street2,
    address.city,
    address.stateOrCountry,
    address.zipCode,
  ];
  return parts.filter(Boolean).join(", ") || null;
}

function firstRecentValue(submission: SecSubmission, key: string): string | null {
  return submission.filings?.recent?.[key]?.[0] ?? null;
}

function toCompanyInfo(submission: SecSubmission, visibleProfile: VisibleCompanyProfile) {
  const addresses = submission.addresses ?? {};
  return {
    company_name: submission.name ?? null,
    cik: normalizeCik(submission.cik),
    tickers: submission.tickers ?? [],
    exchanges: submission.exchanges ?? [],
    entity_type: submission.entityType ?? null,
    sic: submission.sic ?? null,
    sic_description: submission.sicDescription ?? null,
    state_of_incorporation: submission.stateOfIncorporation ?? null,
    state_of_incorporation_description: submission.stateOfIncorporationDescription ?? null,
    fiscal_year_end: submission.fiscalYearEnd ?? null,
    business_address: formatAddress(addresses.business),
    mailing_address: formatAddress(addresses.mailing),
    phone: submission.phone ?? null,
    latest_filing_form: firstRecentValue(submission, "form"),
    latest_filing_date: firstRecentValue(submission, "filingDate"),
    latest_filing_accession_number: firstRecentValue(submission, "accessionNumber"),
    visible_profile: visibleProfile,
  };
}

async function printViewerUrl(session: { status: () => Promise<{ viewer_url?: string | null }> }) {
  const status = await session.status();
  if (status.viewer_url) {
    console.log(`Live View Link: ${status.viewer_url}`);
  }
}

async function main() {
  console.log("Starting SEC company lookup...");

  const client = new NotteClient({ apiKey: process.env.NOTTE_API_KEY });

  await client.Session({ idle_timeout_minutes: 2 }).use(async (session) => {
    console.log("Notte session initialized successfully");
    console.log(`Session ID: ${session.getId()}`);
    await printViewerUrl(session);

    console.log(`Resolving SEC company query: ${COMPANY_QUERY}`);
    await session.execute({ type: "goto", url: SEC_HOME_URL });
    await session.execute({ type: "wait", time_ms: 1500 });

    const cik = await resolveCik(COMPANY_QUERY);
    console.log(`Opening SEC company page for CIK: ${cik}`);
    await session.execute({ type: "goto", url: `${SEC_COMPANY_BROWSE_URL}${cik}` });
    await session.execute({ type: "wait", time_ms: 4000 });

    const visibleProfile = await scrapeVisibleProfile(session);
    const submission = await fetchSubmission(cik);
    const companyInfo = toCompanyInfo(submission, visibleProfile);

    console.log("Company information extracted:");
    console.log(JSON.stringify(companyInfo, null, 2));
  });

  console.log("Session closed successfully");
}

main().catch((error: unknown) => {
  console.error(
    `Error in company lookup: ${error instanceof Error ? error.message : String(error)}`,
  );
  console.error("Common issues:");
  console.error("  - Check .env has NOTTE_API_KEY");
  console.error("  - Search for a public company name, ticker, or CIK that appears in SEC EDGAR");
  console.error("  - Set COMPANY_QUERY to search for a different public company");
  console.error("Docs: https://docs.notte.cc/");
  process.exit(1);
});
