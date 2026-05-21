# Notte: Website Link Tester - See README.md for full documentation
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "notte-sdk[playwright]",
#     "pydantic",
#     "python-dotenv",
# ]
# ///

import json
import os
from pathlib import Path

from dotenv import load_dotenv
from notte_sdk import NotteClient
from pydantic import BaseModel

load_dotenv(Path(__file__).with_name(".env"))

URL = os.environ.get("TARGET_URL", "https://www.notte.cc")
MAX_LINKS = int(os.environ.get("MAX_LINKS", "10"))

SOCIAL_DOMAINS = [
    "twitter.com",
    "x.com",
    "facebook.com",
    "linkedin.com",
    "instagram.com",
    "youtube.com",
    "tiktok.com",
    "reddit.com",
    "discord.com",
]


class ExtractedLink(BaseModel):
    url: str
    link_text: str


class LinkVerificationResult(BaseModel):
    link_text: str
    url: str
    success: bool
    page_title: str | None = None
    content_matches: bool | None = None
    assessment: str | None = None
    error: str | None = None


class PageVerificationSummary(BaseModel):
    page_title: str
    content_matches: bool
    assessment: str


def print_viewer_url(session, label: str = "Session") -> None:
    viewer_url = getattr(session, "viewer_url", None)
    if not viewer_url:
        viewer_url = getattr(session.status(), "viewer_url", None)
    if viewer_url:
        print(f"[{label}] Live View: {viewer_url}")


def deduplicate_links(links: list[ExtractedLink]) -> list[ExtractedLink]:
    seen_urls: set[str] = set()
    unique_links: list[ExtractedLink] = []

    for link in links:
        if link.url in seen_urls:
            continue
        seen_urls.add(link.url)
        unique_links.append(link)

    return unique_links


def collect_links_from_homepage(client: NotteClient) -> list[ExtractedLink]:
    print("Collecting links from homepage...")

    with client.Session(open_viewer=True, idle_timeout_minutes=2) as session:
        print_viewer_url(session, "Collect")
        page = session.page

        print(f"Navigating to {URL}...")
        page.goto(URL, wait_until="domcontentloaded", timeout=30000)

        raw_links = page.evaluate(
            """
            () => Array.from(document.querySelectorAll("a[href]"))
              .map((anchor) => ({
                url: new URL(anchor.getAttribute("href"), document.baseURI).href,
                link_text: anchor.textContent.trim().replace(/\\s+/g, " ") || anchor.getAttribute("aria-label") || "Untitled link"
              }))
              .filter((link) => link.url.startsWith("http"))
            """
        )

    unique_links = deduplicate_links([ExtractedLink.model_validate(link) for link in raw_links])
    limited_links = unique_links[:MAX_LINKS]

    print(f"Collected {len(unique_links)} unique links; verifying {len(limited_links)}")
    print(json.dumps({"links": [link.model_dump() for link in limited_links]}, indent=2))
    return limited_links


def verify_single_link(client: NotteClient, link: ExtractedLink) -> LinkVerificationResult:
    print(f"\nChecking: {link.link_text} ({link.url})")

    try:
        with client.Session(open_viewer=True, idle_timeout_minutes=2) as session:
            print_viewer_url(session, link.link_text[:30])
            page = session.page
            is_social_link = any(domain in link.url for domain in SOCIAL_DOMAINS)

            page.goto(link.url, wait_until="domcontentloaded", timeout=30000)
            if not page.url or page.url == "about:blank":
                raise RuntimeError("Page failed to load - invalid URL detected")

            print(f"Link opened successfully: {link.link_text}")

            if is_social_link:
                return LinkVerificationResult(
                    link_text=link.link_text,
                    url=link.url,
                    success=True,
                    page_title="Social Media Link",
                    content_matches=True,
                    assessment="Loaded; detailed verification skipped",
                )

            verification = session.scrape(
                instructions=(
                    f'Does this page content match what the link text "{link.link_text}" suggests? '
                    "Extract the page title and provide a brief assessment."
                ),
                response_format=PageVerificationSummary,
            )

            print(f"[{link.link_text}] Page Title: {verification.page_title}")
            print(f"[{link.link_text}] Content Matches: {verification.content_matches}")
            print(f"[{link.link_text}] Assessment: {verification.assessment}")

            return LinkVerificationResult(
                link_text=link.link_text,
                url=link.url,
                success=True,
                page_title=verification.page_title,
                content_matches=verification.content_matches,
                assessment=verification.assessment,
            )
    except Exception as error:
        error_message = str(error)
        print(f'Failed to verify link "{link.link_text}": {error_message}')
        return LinkVerificationResult(
            link_text=link.link_text,
            url=link.url,
            success=False,
            error=error_message,
        )


def output_results(results: list[LinkVerificationResult], label: str = "FINAL RESULTS") -> None:
    print("\n" + "=" * 80)
    print(label)
    print("=" * 80)

    final_report = {
        "total_links": len(results),
        "successful": len([result for result in results if result.success]),
        "failed": len([result for result in results if not result.success]),
        "results": [result.model_dump() for result in results],
    }

    print(json.dumps(final_report, indent=2))
    print("\n" + "=" * 80)


def main() -> None:
    print("Starting Website Link Tester...")

    api_key = os.environ.get("NOTTE_API_KEY")
    if not api_key:
        raise RuntimeError("Missing NOTTE_API_KEY. Set it in your environment or .env file.")

    client = NotteClient(api_key=api_key)
    links = collect_links_from_homepage(client)
    results = [verify_single_link(client, link) for link in links]

    output_results(results)
    print("Script completed successfully")


if __name__ == "__main__":
    try:
        main()
    except Exception as err:
        print("Application error:", err)
        print("Common issues:")
        print("  - Check .env has NOTTE_API_KEY")
        print("  - Ensure TARGET_URL is reachable")
        print("Docs: https://docs.notte.cc/")
        raise SystemExit(1)
