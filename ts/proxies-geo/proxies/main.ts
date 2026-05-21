import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { config as loadEnv } from "dotenv";
import { NotteClient } from "notte-sdk";
import { z } from "zod";

const __dirname = dirname(fileURLToPath(import.meta.url));
loadEnv({ path: join(__dirname, ".env") });
loadEnv({ path: join(__dirname, "..", ".env") });

const GeoInfo = z.object({
  ip: z.string().nullable().default(null).describe("The detected public IPv4 or IPv6 address"),
  city: z.string().nullable().default(null).describe("The city name"),
  state: z.string().nullable().default(null).describe("The state or region"),
  country: z.string().nullable().default(null).describe("The country code if available"),
  country_name: z.string().nullable().default(null).describe("The country name"),
  latitude: z.number().nullable().default(null).describe("The latitude coordinate"),
  longitude: z.number().nullable().default(null).describe("The longitude coordinate"),
  postal: z.string().nullable().default(null).describe("The postal code"),
});

async function printViewerUrl(session: { status: () => Promise<{ viewer_url?: string | null }> }) {
  const status = await session.status();
  if (status.viewer_url) {
    console.log(`Session URL: ${status.viewer_url}`);
  }
}

function countryProxy(country: string) {
  return [{ type: "notte", country }];
}

async function testSession(client: NotteClient, sessionName: string, proxies: boolean | ReturnType<typeof countryProxy>) {
  console.log(`\n=== Testing ${sessionName} ===`);

  await client.Session({ idle_timeout_minutes: 2, proxies: proxies as any }).use(async (session) => {
    console.log(`Session ID: ${session.getId()}`);
    await printViewerUrl(session);

    await session.execute({ type: "goto", url: "https://browserleaks.com/ip" });
    await session.execute({ type: "wait", time_ms: 1500 });
    await session.execute({ type: "scroll_down" });
    await session.execute({ type: "scroll_up" });

    const geoInfo = await session.scrape({
      instructions:
        "Extract the detected public IP address, city, state or region, country code if shown, " +
        "country name, latitude, longitude, and postal code from the BrowserLeaks IP page. " +
        "Use the IP address and geolocation tables on the page.",
      response_format: GeoInfo,
    });

    console.log("Geo Info:", JSON.stringify(geoInfo, null, 2));
  });

  console.log(`${sessionName} test completed`);
}

async function main() {
  const apiKey = process.env.NOTTE_API_KEY;
  if (!apiKey) {
    throw new Error("Missing NOTTE_API_KEY. Set it in your environment or .env file.");
  }

  const client = new NotteClient({ apiKey });

  await testSession(client, "Built-in Proxies", true);
  await testSession(client, "Country Proxy (United States)", countryProxy("us"));

  console.log("\n=== All tests completed ===");
}

main().catch((error: unknown) => {
  console.error(`Application error: ${error instanceof Error ? error.message : String(error)}`);
  console.error("Common issues:");
  console.error("  - Check .env has NOTTE_API_KEY");
  console.error("  - Verify proxy access is enabled for your Notte account");
  console.error("Docs: https://docs.notte.cc/");
  process.exit(1);
});
