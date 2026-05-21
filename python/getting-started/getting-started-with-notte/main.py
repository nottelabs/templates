# Notte: Getting Started
# See README.md for full documentation
#
# Demos three common building blocks:
#   1. Search-style lookup through Wikipedia's public API
#   2. Lightweight HTTP fetch with requests
#   3. Notte session controlled via Playwright
#   4. Structured extraction with Notte scrape
#
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "notte-sdk[playwright]",
#     "pydantic",
#     "python-dotenv",
#     "requests",
# ]
# ///

import json
import os
import re
from pathlib import Path
from urllib.parse import urlparse

import requests
from dotenv import load_dotenv
from notte_sdk import NotteClient
from pydantic import BaseModel, Field

load_dotenv(Path(__file__).with_name(".env"))
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

# ============= CONFIGURATION =============
SEARCH_QUERY = "Browser automation"
INFOBOX_TOPIC_URL = os.environ.get("WIKIPEDIA_TOPIC_URL", "https://en.wikipedia.org/wiki/OpenAI")
HTTP_HEADERS = {"User-Agent": "bb-templates-notte-getting-started/1.0"}
# =========================================


class InfoboxField(BaseModel):
    label: str | None = Field(None, description="The label of the field in the infobox.")
    value: str | None = Field(None, description="The value associated with the field.")


class WikipediaInfobox(BaseModel):
    title: str | None = Field(None, description="The main title of the Wikipedia article.")
    description: str | None = Field(
        None,
        description="A brief description of the article subject, usually the first paragraph.",
    )
    fields: list[InfoboxField] = Field(
        default_factory=list,
        description="A list of key-value pairs from the right-hand infobox.",
    )


def validate_wikipedia_article_url(topic_url: str) -> str:
    parsed = urlparse(topic_url)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("WIKIPEDIA_TOPIC_URL must start with http:// or https://")
    if not parsed.netloc.endswith("wikipedia.org"):
        raise ValueError("WIKIPEDIA_TOPIC_URL must point to wikipedia.org")
    if not parsed.path.startswith("/wiki/"):
        raise ValueError("WIKIPEDIA_TOPIC_URL must point to a /wiki/ article")
    return topic_url


def print_viewer_url(session) -> None:
    viewer_url = getattr(session, "viewer_url", None)
    if not viewer_url:
        viewer_url = getattr(session.status(), "viewer_url", None)
    if viewer_url:
        print(f"Live view: {viewer_url}")


def demo_structured_infobox(client: NotteClient) -> None:
    print("\n" + "=" * 50)
    print("4. STRUCTURED INFOBOX SCRAPE")
    print("=" * 50)

    topic_url = validate_wikipedia_article_url(INFOBOX_TOPIC_URL)
    instructions = (
        "Extract the Wikipedia article title and the key/value rows from the right-hand "
        "infobox only. Return JSON with title, description, and fields where each field "
        "has label and value text. Do not include article body, references, navigation, "
        "or unrelated page chrome."
    )

    with client.Session(open_viewer=True, idle_timeout_minutes=2, use_file_storage=True) as session:
        print(f"Session ID: {session.session_id}")
        print_viewer_url(session)
        print(f"Opening {topic_url}")

        session.execute(type="goto", url=topic_url)
        session.execute(type="scroll_down")
        session.execute(type="scroll_up")

        result = session.scrape(
            instructions=instructions,
            only_main_content=False,
            only_images=False,
            scrape_links=False,
            scrape_images=False,
            response_format=WikipediaInfobox,
        )

    print("\nInfobox JSON:")
    print(json.dumps(result.model_dump(), indent=2, ensure_ascii=False))


def main() -> None:
    print("=" * 50)
    print("GETTING STARTED WITH NOTTE")
    print("=" * 50)
    print("Demos: Search lookup, HTTP fetch, browser sessions, and structured scraping\n")

    api_key = os.environ.get("NOTTE_API_KEY")
    if not api_key:
        raise RuntimeError("Missing NOTTE_API_KEY. Set it in your environment or .env file.")

    client = NotteClient(api_key=api_key)

    demo_structured_infobox(client)

    print("\n" + "=" * 50)
    print("ALL DEMOS COMPLETE!")
    print("=" * 50)


if __name__ == "__main__":
    try:
        main()
    except Exception as err:
        print(f"Error: {err}")
        print("\nTroubleshooting:")
        print("  1. Check your .env file has NOTTE_API_KEY")
        print("  2. Verify internet connectivity and that the target sites are reachable")
        print("Docs: https://docs.notte.cc/")
        exit(1)
