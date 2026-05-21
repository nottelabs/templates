# Notte: Quotes Author Scraper - See README.md for full documentation
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "notte-sdk[playwright]",
#     "pydantic",
#     "python-dotenv",
# ]
# ///

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

from dotenv import load_dotenv
from notte_sdk import NotteClient
from pydantic import BaseModel, Field

load_dotenv(Path(__file__).with_name(".env"))

BASE_URL = os.environ.get("BASE_URL", "https://quotes.toscrape.com/")
MAX_PAGES = int(os.environ.get("MAX_PAGES", "2"))
MAX_AUTHORS = int(os.environ.get("MAX_AUTHORS", "10"))
INCLUDE_AUTHOR_PROFILES = os.environ.get("INCLUDE_AUTHOR_PROFILES", "true").lower() in {
    "1",
    "true",
    "yes",
}


class Quote(BaseModel):
    text: str
    author: str
    author_url: str
    tags: list[str] = Field(default_factory=list)
    source_url: str


class AuthorProfile(BaseModel):
    name: str
    born_date: str
    born_location: str
    description: str
    url: str


class ScrapeResult(BaseModel):
    base_url: str
    pages_scraped: int
    quote_count: int
    author_count: int
    quotes: list[Quote]
    authors: list[AuthorProfile]


QUOTE_PAGE_EXTRACTOR = """
() => ({
  url: location.href,
  nextPath: document.querySelector("li.next a")?.getAttribute("href") || null,
  quotes: Array.from(document.querySelectorAll(".quote")).map((quote) => ({
    text: quote.querySelector(".text")?.textContent.trim() || "",
    author: quote.querySelector(".author")?.textContent.trim() || "",
    authorPath: quote.querySelector("span a[href^='/author/']")?.getAttribute("href") || "",
    tags: Array.from(quote.querySelectorAll(".tags .tag"))
      .map((tag) => tag.textContent.trim())
      .filter(Boolean)
  }))
})
"""

AUTHOR_PAGE_EXTRACTOR = """
() => ({
  name: document.querySelector(".author-title")?.textContent.trim() || "",
  born_date: document.querySelector(".author-born-date")?.textContent.trim() || "",
  born_location: document.querySelector(".author-born-location")?.textContent.trim() || "",
  description: document.querySelector(".author-description")?.textContent.trim() || "",
  url: location.href
})
"""


def print_viewer_url(session) -> None:
    viewer_url = getattr(session, "viewer_url", None)
    if not viewer_url:
        viewer_url = getattr(session.status(), "viewer_url", None)
    if viewer_url:
        print(f"Live view: {viewer_url}")


def validate_positive_int(name: str, value: int) -> None:
    if value < 1:
        raise ValueError(f"{name} must be at least 1")


def collect_quote_pages(page, base_url: str, max_pages: int) -> tuple[list[Quote], int]:
    quotes: list[Quote] = []
    current_url = base_url

    for page_number in range(1, max_pages + 1):
        print(f"Loading quote page {page_number}: {current_url}")
        page.goto(current_url, wait_until="domcontentloaded", timeout=30000)
        page.wait_for_selector(".quote", state="visible", timeout=10000)

        page_data: dict[str, Any] = page.evaluate(QUOTE_PAGE_EXTRACTOR)
        source_url = page_data["url"]
        page_quotes = [
            Quote(
                text=item["text"],
                author=item["author"],
                author_url=urljoin(base_url, item["authorPath"]),
                tags=item["tags"],
                source_url=source_url,
            )
            for item in page_data["quotes"]
            if item["text"] and item["author"] and item["authorPath"]
        ]

        print(f"  Found {len(page_quotes)} quotes")
        quotes.extend(page_quotes)

        next_path = page_data.get("nextPath")
        if not next_path:
            return quotes, page_number
        current_url = urljoin(source_url, next_path)

    return quotes, max_pages


def collect_author_profiles(page, quotes: list[Quote], max_authors: int) -> list[AuthorProfile]:
    author_urls: dict[str, str] = {}
    for quote in quotes:
        author_urls.setdefault(quote.author, quote.author_url)

    selected_authors = list(author_urls.items())[:max_authors]
    profiles: list[AuthorProfile] = []

    for author_name, author_url in selected_authors:
        print(f"Loading author profile: {author_name}")
        page.goto(author_url, wait_until="domcontentloaded", timeout=30000)
        page.wait_for_selector(".author-title", state="visible", timeout=10000)
        profile_data: dict[str, Any] = page.evaluate(AUTHOR_PAGE_EXTRACTOR)
        profiles.append(AuthorProfile.model_validate(profile_data))

    return profiles


def scrape_quotes_and_authors(
    base_url: str = BASE_URL,
    max_pages: int = MAX_PAGES,
    include_author_profiles: bool = INCLUDE_AUTHOR_PROFILES,
    max_authors: int = MAX_AUTHORS,
) -> ScrapeResult:
    validate_positive_int("MAX_PAGES", max_pages)
    validate_positive_int("MAX_AUTHORS", max_authors)

    api_key = os.environ.get("NOTTE_API_KEY")
    if not api_key:
        raise RuntimeError("Missing NOTTE_API_KEY. Set it in your environment or .env file.")

    client = NotteClient(api_key=api_key)

    with client.Session(open_viewer=True, idle_timeout_minutes=2) as session:
        print(f"Session ID: {session.session_id}")
        print_viewer_url(session)

        page = session.page
        quotes, pages_scraped = collect_quote_pages(page, base_url, max_pages)
        authors = (
            collect_author_profiles(page, quotes, max_authors)
            if include_author_profiles
            else []
        )

    return ScrapeResult(
        base_url=base_url,
        pages_scraped=pages_scraped,
        quote_count=len(quotes),
        author_count=len(authors),
        quotes=quotes,
        authors=authors,
    )


def main() -> None:
    print("Starting Quotes Author Scraper...")
    result = scrape_quotes_and_authors()
    print("\nFINAL RESULT")
    print(json.dumps(result.model_dump(), indent=2, ensure_ascii=False))
    print("\nScript completed successfully")


if __name__ == "__main__":
    try:
        main()
    except Exception as err:
        print(f"Application error: {err}")
        print("Common issues:")
        print("  - Check .env has NOTTE_API_KEY set")
        print("  - Ensure BASE_URL points to a Quotes to Scrape-compatible site")
        print("  - Lower MAX_PAGES or MAX_AUTHORS if you only need a quick sample")
        print("Docs: https://docs.notte.cc/")
        raise SystemExit(1)
