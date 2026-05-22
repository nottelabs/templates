import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { config as loadEnv } from "dotenv";
import { NotteClient } from "notte-sdk";
import { z } from "zod";

const __dirname = dirname(fileURLToPath(import.meta.url));
loadEnv({ path: join(__dirname, ".env") });
loadEnv({ path: join(__dirname, "..", ".env") });

const FORM_URL = "https://www.selenium.dev/selenium/web/web-form.html";

const formData = {
  textValue: process.env.FORM_TEXT_VALUE ?? "Notte deterministic form test",
  passwordValue: process.env.FORM_PASSWORD_VALUE ?? "sample-password",
  textareaValue:
    process.env.FORM_TEXTAREA_VALUE ??
    "Filled by a Notte browser session against Selenium's public demo form.",
  selectValue: process.env.FORM_SELECT_VALUE ?? "2",
  datalistValue: process.env.FORM_DATALIST_VALUE ?? "Seattle",
  dateValue: process.env.FORM_DATE_VALUE ?? "05/19/2026",
  colorValue: process.env.FORM_COLOR_VALUE ?? "#2f80ed",
};

const FormSnapshot = z.object({
  text_value: z.string().nullable().default(null).describe("Value in the text input."),
  textarea_value: z.string().nullable().default(null).describe("Value in the textarea."),
  select_value: z.string().nullable().default(null).describe("Selected dropdown value or label."),
  datalist_value: z.string().nullable().default(null).describe("Value in the datalist input."),
  date_value: z.string().nullable().default(null).describe("Value in the date input."),
  color_value: z.string().nullable().default(null).describe("Value in the color input."),
  checkbox_selected: z.boolean().nullable().default(null).describe("Whether the selected checkbox is checked."),
  radio_selected: z.boolean().nullable().default(null).describe("Whether the selected radio button is checked."),
});

async function printViewerUrl(session: { status: () => Promise<{ viewer_url?: string | null }> }) {
  const status = await session.status();
  if (status.viewer_url) {
    console.log(`Live View Link: ${status.viewer_url}`);
  }
}

async function main() {
  console.log("Starting Form Filling Example...");

  const apiKey = process.env.NOTTE_API_KEY;
  if (!apiKey) {
    throw new Error("Missing NOTTE_API_KEY. Set it in your environment or .env file.");
  }

  const client = new NotteClient({ apiKey });

  await client.Session({ open_viewer: true, idle_timeout_minutes: 2 }).use(async (session) => {
    console.log("Notte session initialized successfully");
    console.log(`Session ID: ${session.getId()}`);
    await printViewerUrl(session);

    console.log("Navigating to Selenium web form demo...");
    await session.execute({ type: "goto", url: FORM_URL });
    await session.execute({ type: "wait", time_ms: 1000 });

    console.log("Filling in demo form fields...");
    await session.execute({
      type: "fill",
      selector: 'input[name="my-text"]',
      value: formData.textValue,
      clear_before_fill: true,
    });
    await session.execute({
      type: "fill",
      selector: 'input[name="my-password"]',
      value: formData.passwordValue,
      clear_before_fill: true,
    });
    await session.execute({
      type: "fill",
      selector: 'textarea[name="my-textarea"]',
      value: formData.textareaValue,
      clear_before_fill: true,
    });
    await session.execute({
      type: "select_dropdown_option",
      selector: 'select[name="my-select"]',
      value: formData.selectValue,
    });
    await session.execute({
      type: "fill",
      selector: 'input[name="my-datalist"]',
      value: formData.datalistValue,
      clear_before_fill: true,
    });
    await session.execute({
      type: "fill",
      selector: 'input[name="my-date"]',
      value: formData.dateValue,
      clear_before_fill: true,
    });
    await session.execute({
      type: "fill",
      selector: 'input[name="my-colors"]',
      value: formData.colorValue,
      clear_before_fill: true,
    });
    await session.execute({ type: "click", selector: "#my-check-2" });
    await session.execute({ type: "click", selector: "#my-radio-2" });

    console.log("Form filled successfully");
    const snapshot = await session.scrape({
      instructions:
        "Extract the currently filled values from Selenium's demo form. Include the text, " +
        "textarea, select, datalist, date, and color values, plus whether checkbox 2 and " +
        "radio 2 are selected. Do not include unrelated page text.",
      only_main_content: false,
      scrape_links: false,
      scrape_images: false,
      response_format: FormSnapshot,
    });

    console.log("Form snapshot:");
    console.log(JSON.stringify(snapshot, null, 2));

    // Uncomment this line if you want to submit the form.
    // await session.execute({ type: "click", selector: 'button[type="submit"]' });

    await session.execute({ type: "wait", time_ms: 5000 });
  });

  console.log("Session closed successfully");
}

main().catch((error: unknown) => {
  console.error(`Error in form filling example: ${error instanceof Error ? error.message : String(error)}`);
  console.error("Common issues:");
  console.error("  - Check .env has NOTTE_API_KEY set");
  console.error("  - Ensure form fields are available on the Selenium demo page");
  console.error("Docs: https://docs.notte.cc/");
  process.exit(1);
});
