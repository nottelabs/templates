# Notte: Open Library Book Finder
# See README.md for full documentation
#
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "notte-sdk",
#     "pydantic",
#     "python-dotenv",
# ]
# ///

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote_plus, urljoin

from dotenv import load_dotenv
from notte_sdk import NotteClient
from pydantic import BaseModel, Field, field_validator

load_dotenv(Path(__file__).with_name(".env"))

OPENLIBRARY_HOME_URL = "https://openlibrary.org/"
DEFAULT_QUERY = os.environ.get("OPENLIBRARY_QUERY", "the hobbit")
DEFAULT_MAX_RESULTS = int(os.environ.get("OPENLIBRARY_MAX_RESULTS", "5"))

SEARCH_INPUT_SELECTOR = {
    "css_selector": (
        'html > body > header:nth-of-type(1) > div:nth-of-type(2) > div > div:nth-of-type(1) '
        '> form > input:nth-of-type(1)[type="text"][name="q"][placeholder="Search"]'
        '[aria-label="Search"][autocomplete="off"]'
    ),
    "xpath_selector": "html/body/header[1]/div[2]/div/div[1]/form/input[1]",
    "playwright_selector": 'internal:role=textbox[name="Search"i]',
}

SEARCH_SUBMIT_SELECTOR = {
    "css_selector": (
        'html > body > header:nth-of-type(1) > div:nth-of-type(2) > div > div:nth-of-type(1) '
        '> form > input:nth-of-type(3).search-bar-submit[type="submit"][aria-label="Search submit"]'
    ),
    "xpath_selector": "html/body/header[1]/div[2]/div/div[1]/form/input[3]",
    "playwright_selector": 'internal:role=button[name="Search submit"i]',
}


class BookResult(BaseModel):
    title: str | None = Field(None, description="Visible work title")
    authors: list[str] = Field(default_factory=list, description="Visible author names")
    first_published_year: int | None = Field(None, description="First published year")
    editions_count: int | None = Field(None, description="Number of editions shown")
    ebook_count: int | None = Field(None, description="Number of ebooks shown")
    availability_text: str | None = Field(None, description="Borrow, Preview Only, Locate, or similar")
    rating_text: str | None = Field(None, description="Visible rating summary")
    want_to_read_text: str | None = Field(None, description="Want-to-read count text")
    work_url: str | None = Field(None, description="Open Library work URL")

    @field_validator("authors", mode="before")
    @classmethod
    def coerce_authors(cls, value):
        if value is None:
            return []
        if isinstance(value, str):
            names = value.replace(" and ", ", ").split(",")
            return [name.strip() for name in names if name.strip()]
        return [name for name in value if name]


class SearchResults(BaseModel):
    search_query: str | None = None
    total_hit_count: int | None = None
    results: list[BookResult] = Field(default_factory=list)


def print_viewer_url(session) -> None:
    viewer_url = getattr(session, "viewer_url", None)
    if not viewer_url:
        viewer_url = getattr(session.status(), "viewer_url", None)
    if viewer_url:
        print(f"Live View: {viewer_url}")


def normalize_results(results: SearchResults, query: str, max_results: int) -> dict[str, Any]:
    books = []
    for result in results.results[:max_results]:
        item = result.model_dump()
        if item.get("work_url"):
            item["work_url"] = urljoin(OPENLIBRARY_HOME_URL, item["work_url"])
        books.append(item)

    return {
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "search_query": results.search_query or query,
        "search_url": f"{OPENLIBRARY_HOME_URL}search?q={quote_plus(query)}",
        "total_hit_count": results.total_hit_count,
        "returned_count": len(books),
        "books": books,
    }


def scrape_visible_results(session, query: str, max_results: int) -> SearchResults:
    return session.scrape(
        instructions=(
            "Extract the visible Open Library book search results as structured JSON. "
            f"Use the search query {query!r}. Include the total hit count and the first "
            f"{max_results} results. For each result include title, authors as a list, "
            "first published year, editions count, ebook count, availability text such as "
            "Borrow or Preview Only or Locate, rating text, want_to_read text, and work URL."
        ),
        only_main_content=False,
        only_images=False,
        scrape_links=True,
        scrape_images=False,
        response_format=SearchResults,
    )


def run(query: str = DEFAULT_QUERY, max_results: int = DEFAULT_MAX_RESULTS) -> dict[str, Any]:
    api_key = os.environ.get("NOTTE_API_KEY")
    client = NotteClient(api_key=api_key) if api_key else NotteClient()

    with client.Session(browser_type="chrome", open_viewer=True, idle_timeout_minutes=3) as session:
        print(f"Session ID: {session.session_id}")
        print_viewer_url(session)

        print(f"Searching Open Library for: {query}")
        session.execute(type="goto", url=OPENLIBRARY_HOME_URL)
        session.execute(
            type="fill",
            selector=SEARCH_INPUT_SELECTOR,
            value=query,
            clear_before_fill=True,
        )
        session.execute(type="click", selector=SEARCH_SUBMIT_SELECTOR)
        session.execute(type="wait", time_ms=1500)

        results = scrape_visible_results(session, query, max_results)

    return normalize_results(results, query, max_results)


def main() -> None:
    query = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_QUERY
    max_results = int(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_MAX_RESULTS
    report = run(query=query, max_results=max_results)

    output_path = os.environ.get("OPENLIBRARY_OUTPUT_PATH")
    if output_path:
        Path(output_path).write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    try:
        main()
    except Exception as err:
        print(f"Error: {err}")
        print("\nTroubleshooting:")
        print("  - Set NOTTE_API_KEY in your environment or .env file")
        print("  - Try a simpler query, for example: uv run main.py hobbit")
        print("  - If the first navigation is flaky, rerun with the default Chrome session")
        raise SystemExit(1)
