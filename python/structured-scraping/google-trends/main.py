# Notte: Google Trends Regional Briefing - See README.md for full documentation
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "notte-sdk",
#     "pydantic",
#     "python-dotenv",
# ]
# ///

import json
import os
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from notte_sdk import NotteClient
from pydantic import BaseModel, Field


class TrendStory(BaseModel):
    """Schema for a compact story brief from Google Trends."""

    topic: str = Field(description="Main trend topic or story cluster")
    search_volume: str | None = Field(
        default=None,
        description="Visible search volume for the trend, such as 200K+",
    )
    started: str | None = Field(
        default=None,
        description="Visible start time or freshness label for the trend",
    )
    related_queries: list[str] = Field(
        default_factory=list,
        description="Related queries, breakdown terms, or variants shown with this trend",
    )
    news_headlines: list[str] = Field(
        default_factory=list,
        description="Visible news headlines connected to this trend",
    )


class RegionalBriefing(BaseModel):
    """Schema for an editorial-style regional trends briefing."""

    stories: list[TrendStory] = Field(
        description="Brief story clusters extracted from Google Trends"
    )


# Load environment variables from this template directory.
load_dotenv(Path(__file__).with_name(".env"))

# Configuration variables
country_codes = ["US", "GB"]  # Two-letter ISO codes to compare
stories_per_region = 5  # Max story clusters per region
language = "en-US"  # Language code for results


def scrape_region(session, country_code: str) -> RegionalBriefing:
    trends_url = f"https://trends.google.com/trending?geo={country_code.upper()}&hl={language}"
    print(f"Navigating to: {trends_url}")
    session.execute(type="goto", url=trends_url)
    session.execute(type="wait", time_ms=2500)

    try:
        print("Checking for consent dialogs...")
        session.execute(
            type="click",
            selector='button:has-text("Got it")',
            timeout=5000,
            raise_on_failure=False,
        )
        session.execute(type="wait", time_ms=1500)
    except Exception:
        print("No consent dialog found, continuing...")

    print(f"Building briefing for {country_code.upper()}...")
    return session.scrape(
        instructions=(
            "Create a compact editorial briefing from the visible Google Trends page. "
            "Do not transcribe the full trending table. Instead, group the most prominent "
            f"visible trends into up to {stories_per_region} story clusters. For each "
            "cluster, capture the main topic, visible search volume, visible start time, "
            "related queries or breakdown terms if shown, and any visible connected news "
            "headlines. Leave fields empty or null when the page does not show them."
        ),
        response_format=RegionalBriefing,
    )


def compare_topics(regional_results: dict[str, RegionalBriefing]) -> dict[str, list[str]]:
    topics_by_country = {
        country: {story.topic.strip().lower() for story in briefing.stories if story.topic}
        for country, briefing in regional_results.items()
    }
    if len(topics_by_country) < 2:
        return {"shared_topics": []}

    country_sets = list(topics_by_country.values())
    shared_topics = sorted(set.intersection(*country_sets))
    return {"shared_topics": shared_topics}


def main():
    """
    Builds a structured regional briefing from Google Trends and compares regions.
    Uses Notte structured scraping with Pydantic for type-safe data.
    """
    print("Starting Google Trends Regional Briefing...")
    print(f"Country Codes: {', '.join(country_codes)}")
    print(f"Language: {language}")
    print(f"Stories per region: {stories_per_region}")

    api_key = os.environ.get("NOTTE_API_KEY")
    if not api_key:
        raise RuntimeError("Missing NOTTE_API_KEY. Set it in your environment or .env file.")

    client = NotteClient(api_key=api_key)

    try:
        with client.Session(
            open_viewer=True,
            idle_timeout_minutes=2,
            max_duration_minutes=15,
            solve_captchas=True,
        ) as session:
            print("Notte session started")
            print(f"Session ID: {session.session_id}")
            viewer_url = getattr(session, "viewer_url", None)
            if not viewer_url:
                viewer_url = getattr(session.status(), "viewer_url", None)
            if viewer_url:
                print(f"Watch live: {viewer_url}")

            regional_results = {
                country_code.upper(): scrape_region(session, country_code)
                for country_code in country_codes
            }
            comparison = compare_topics(regional_results)

            result = {
                "country_codes": [country_code.upper() for country_code in country_codes],
                "language": language,
                "extracted_at": datetime.now().isoformat(),
                "regional_briefings": {
                    country_code: briefing.model_dump()
                    for country_code, briefing in regional_results.items()
                },
                "comparison": comparison,
            }

            print("\n=== Results ===")
            print(json.dumps(result, indent=2))
            print("\nBriefing complete.")

        print("Session closed successfully")

    except Exception as error:
        print(f"Error building Google Trends briefing: {error}")
        print("\nCommon issues:")
        print("1. Check .env has NOTTE_API_KEY")
        print("2. Ensure country codes are valid 2-letter ISO codes (US, GB, IN, etc.)")
        print("3. Check if Google Trends page structure has changed")
        raise


if __name__ == "__main__":
    try:
        main()
    except Exception as err:
        print(f"Application error: {err}")
        print("Common issues:")
        print("  - Check .env has NOTTE_API_KEY")
        print("Docs: https://docs.notte.cc/")
        exit(1)
