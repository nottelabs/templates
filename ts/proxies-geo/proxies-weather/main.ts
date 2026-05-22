import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { config as loadEnv } from "dotenv";
import { NotteClient } from "notte-sdk";
import { z } from "zod";

const __dirname = dirname(fileURLToPath(import.meta.url));
loadEnv({ path: join(__dirname, ".env") });
loadEnv({ path: join(__dirname, "..", ".env") });

type LocationConfig = {
  label: string;
  proxyCountry: string;
};

type WeatherResult = {
  label: string;
  proxy_country: string;
  location: string | null;
  region: string | null;
  country: string | null;
  temperature: number | null;
  unit: string | null;
  condition: string | null;
  humidity: number | null;
  error: string | null;
};

const TemperatureData = z.object({
  location: z.string().nullable().default(null).describe("The nearest area name from the weather response"),
  region: z.string().nullable().default(null).describe("The region or state from the weather response"),
  country: z.string().nullable().default(null).describe("The country from the weather response"),
  temperature: z.number().nullable().default(null).describe("The current temperature value in Celsius"),
  unit: z.string().nullable().default(null).describe("The temperature unit, usually C"),
  condition: z.string().nullable().default(null).describe("The current weather description"),
  humidity: z.number().nullable().default(null).describe("The current humidity percentage"),
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

async function getWeatherForLocation(client: NotteClient, location: LocationConfig): Promise<WeatherResult> {
  console.log(`\n=== Getting weather through ${location.label} proxy ===`);

  try {
    let weatherResult: z.infer<typeof TemperatureData> | null = null;

    await client
      .Session({
        open_viewer: true,
        idle_timeout_minutes: 2,
        proxies: countryProxy(location.proxyCountry) as any,
        viewport_width: 1080,
        viewport_height: 720,
      })
      .use(async (session) => {
        console.log(`Session ID: ${session.getId()}`);
        await printViewerUrl(session);

        console.log("Navigating to wttr.in weather service...");
        await session.execute({ type: "goto", url: "https://wttr.in/" });
        await session.execute({ type: "wait", time_ms: 1000 });

        console.log("Extracting temperature data...");
        weatherResult = await session.scrape({
          instructions:
            "Extract the location shown in the weather report, the region or state if visible, " +
            "the country if visible, the current temperature in Celsius as temperature, " +
            "C as unit, the current weather condition, and humidity from the wttr.in page.",
          response_format: TemperatureData,
        });
      });

    const weather = weatherResult ?? TemperatureData.parse({});
    console.log(
      `Extracted weather data: ${weather.location}, ${weather.region}, ${weather.country} - ` +
        `${weather.temperature} ${weather.unit}, ${weather.condition}`,
    );

    return {
      label: location.label,
      proxy_country: location.proxyCountry,
      location: weather.location,
      region: weather.region,
      country: weather.country,
      temperature: weather.temperature,
      unit: weather.unit,
      condition: weather.condition,
      humidity: weather.humidity,
      error: null,
    };
  } catch (error: unknown) {
    console.error(`Error getting weather through ${location.label}: ${error instanceof Error ? error.message : String(error)}`);
    return {
      label: location.label,
      proxy_country: location.proxyCountry,
      location: null,
      region: null,
      country: null,
      temperature: null,
      unit: null,
      condition: null,
      humidity: null,
      error: error instanceof Error ? error.message : String(error),
    };
  }
}

function displayResults(results: WeatherResult[]) {
  console.log("\n=== Weather Results ===");
  for (const result of results) {
    if (result.error) {
      console.log(`${result.label} (${result.proxy_country}): Error - ${result.error}`);
    } else {
      console.log(
        `${result.label} (${result.proxy_country}): ` +
          `${result.location}, ${result.region}, ${result.country} - ` +
          `${result.temperature} ${result.unit}, ${result.condition}, humidity ${result.humidity}%`,
      );
    }
  }
}

async function main() {
  const apiKey = process.env.NOTTE_API_KEY;
  if (!apiKey) {
    throw new Error("Missing NOTTE_API_KEY. Set it in your environment or .env file.");
  }

  const locations: LocationConfig[] = [
    { label: "United States", proxyCountry: "us" },
    { label: "United Kingdom", proxyCountry: "gb" },
    { label: "Japan", proxyCountry: "jp" },
    { label: "Brazil", proxyCountry: "br" },
  ];

  const client = new NotteClient({ apiKey });

  console.log("=== Weather Proxy Demo - Running Sequentially ===\n");
  console.log(`Processing ${locations.length} locations with country proxies...\n`);

  const results: WeatherResult[] = [];
  for (const location of locations) {
    results.push(await getWeatherForLocation(client, location));
  }

  displayResults(results);
  console.log("\n=== All locations completed ===");
}

main().catch((error: unknown) => {
  console.error(`Application error: ${error instanceof Error ? error.message : String(error)}`);
  console.error("Common issues:");
  console.error("  - Check .env has NOTTE_API_KEY");
  console.error("  - Verify proxy access is enabled for your Notte account");
  console.error("Docs: https://docs.notte.cc/");
  process.exit(1);
});
