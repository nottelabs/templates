# Playwright + Notte: Quickstart
# See README.md for full documentation
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
from pydantic import BaseModel, Field

load_dotenv(Path(__file__).with_name(".env"))


class ArticleSnapshot(BaseModel):
    title: str | None = Field(None, description="The article title.")
    url: str | None = Field(None, description="The article URL.")
    description: str | None = Field(None, description="A concise description of the subject.")
    lead_paragraph: str | None = Field(None, description="The first substantial paragraph.")
    sections: list[str] = Field(default_factory=list, description="Visible article section headings.")
    notable_facts: list[str] = Field(default_factory=list, description="A few notable facts from the article.")


def print_viewer_url(session) -> None:
    viewer_url = getattr(session, "viewer_url", None)
    if not viewer_url:
        viewer_url = getattr(session.status(), "viewer_url", None)
    if viewer_url:
        print(f"Live debug URL: {viewer_url}")


def run() -> None:
    api_key = os.environ.get("NOTTE_API_KEY")
    if not api_key:
        raise RuntimeError("Missing NOTTE_API_KEY. Set it in your environment or .env file.")

    client = NotteClient(api_key=api_key)

    with client.Session(open_viewer=True, idle_timeout_minutes=2) as session:
        print(f"Session created, id: {session.session_id}")
        print_viewer_url(session)

        page = session.page
        wait_timeout = 10_000

        # Use Notte actions to open Wikipedia and jump to a random article.
        session.execute(type="goto", url="https://en.wikipedia.org/wiki/Main_Page")
        session.execute(type="check", selector='internal:role=button[name="Main menu"i]', value=True)
        session.execute(type="click", selector='internal:role=link[name="Random article"i]')
        page.wait_for_load_state("domcontentloaded", timeout=wait_timeout)
        print(f"Random article URL: {page.url} | Title: {page.title()}")

        # Verify the article loaded, then ask Notte for a generic structured scrape.
        heading = page.locator("#firstHeading")
        heading.wait_for(state="visible", timeout=wait_timeout)
        print(f"Heading: {heading.text_content()}")

        article = session.scrape(
            instructions=(
                "Extract a compact summary of the current Wikipedia article. Include the title, "
                "current URL, short description, first substantial paragraph, visible section "
                "headings, and 3 to 5 notable facts. Ignore references, navigation, and page chrome."
            ),
            only_main_content=True,
            scrape_links=False,
            scrape_images=False,
            response_format=ArticleSnapshot,
        )
        if article.url is None:
            article.url = page.url
        print(json.dumps(article.model_dump(), indent=2, ensure_ascii=False))

    print("Session complete")


if __name__ == "__main__":
    try:
        run()
    except Exception as err:
        print(f"Error: {err}")
        print("\nTroubleshooting:")
        print("  1. Check your .env file has NOTTE_API_KEY")
        print("  2. Verify the target site is reachable")
        print("Docs: https://docs.notte.cc/")
        exit(1)
