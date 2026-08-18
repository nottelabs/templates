import assert from "node:assert/strict";
import test from "node:test";

import {
  contactLinks,
  extractEmails,
  normalizeUrl,
  scrapeWithSession,
  type EmailFinderSession,
} from "./main.js";

class FakeSession implements EmailFinderSession {
  currentUrl = "";
  visited: string[] = [];

  constructor(private readonly pages: Record<string, string>) {}

  async execute(
    action: unknown,
  ): Promise<{ success: boolean; message?: string }> {
    const url = (action as { url: string }).url;
    this.visited.push(url);
    this.currentUrl = url;
    return this.pages[url]
      ? { success: true }
      : { success: false, message: "Navigation failed" };
  }

  async scrape(): Promise<string> {
    return this.pages[this.currentUrl];
  }
}

test("normalizes URLs and extracts decoded email addresses", () => {
  assert.equal(normalizeUrl("example.com"), "https://example.com/");
  assert.deepEqual(
    extractEmails("A@Example.COM and &lt;b@example.org&gt;"),
    new Set(["a@example.com", "b@example.org"]),
  );
  assert.deepEqual(
    extractEmails("https://maps.google.com/@23.5232492,87.3"),
    new Set(),
  );
});

test("discovers same-site contact links from Markdown and HTML", () => {
  const links = contactLinks(
    '[Talk to us](/company/contact) <a href="/support" aria-label="Help center">Icon</a> ' +
      "[External support](https://other.example/support)",
    "https://example.com/",
    "https://example.com",
  );

  assert.deepEqual(
    links,
    new Set([
      "https://example.com/company/contact",
      "https://example.com/support",
    ]),
  );
});

test("scrapes the homepage and a discovered contact page", async () => {
  const session = new FakeSession({
    "https://example.com/":
      "[Talk to us](/company/locations) hello@example.com",
    "https://example.com/company/locations": "Support: support@example.org",
  });

  const result = await scrapeWithSession(session, "example.com");

  assert.deepEqual(
    [...result.emails],
    [
      ["hello@example.com", new Set(["https://example.com/"])],
      [
        "support@example.org",
        new Set(["https://example.com/company/locations"]),
      ],
    ],
  );
  assert.deepEqual(result.errors, []);
  assert.deepEqual(session.visited, [
    "https://example.com/",
    "https://example.com/company/locations",
  ]);
});

test("falls back to common contact paths", async () => {
  const session = new FakeSession({
    "https://example.com/": "Welcome",
    "https://example.com/contact-us": "fallback@example.net",
  });

  const result = await scrapeWithSession(session, "https://example.com");

  assert.deepEqual([...result.emails.keys()], ["fallback@example.net"]);
  assert.equal(result.errors.length, 3);
  assert.deepEqual(session.visited, [
    "https://example.com/",
    "https://example.com/contact",
    "https://example.com/contact-us",
    "https://example.com/get-in-touch",
    "https://example.com/support",
  ]);
});
