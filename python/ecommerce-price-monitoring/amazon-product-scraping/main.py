# Notte: Amazon Product Scraping
# See README.md for full documentation
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
from pathlib import Path
from urllib.parse import quote_plus

from dotenv import load_dotenv
from notte_sdk import NotteClient
from pydantic import BaseModel, Field


class MonitorCandidate(BaseModel):
    """Schema for a product candidate worth monitoring."""

    title: str | None = Field(None, description="The full product title shown in search results")
    current_price: str | None = Field(None, description="The visible current price, including currency symbol")
    list_price: str | None = Field(None, description="The crossed-out list price or typical price, if shown")
    deal_or_coupon: str | None = Field(None, description="Any deal badge, coupon, or savings message")
    delivery_promise: str | None = Field(None, description="Prime, shipping speed, or delivery promise text")
    purchase_context: str | None = Field(None, description="Short note such as bundle, pack size, or variant info")
    product_url: str | None = Field(None, description="The URL link to the product detail page")


class MonitoringSnapshot(BaseModel):
    """Schema for extracting Amazon search results for price monitoring."""

    search_intent: str | None = Field(None, description="Brief summary of what the search results are for")
    candidates: list[MonitorCandidate] = Field(
        default_factory=list,
        description="Up to 5 non-sponsored product candidates with pricing and delivery signals",
    )


load_dotenv(Path(__file__).with_name(".env"))

SEARCH_QUERY = "portable espresso maker travel"


def print_viewer_url(session) -> None:
    viewer_url = getattr(session, "viewer_url", None)
    if not viewer_url:
        viewer_url = getattr(session.status(), "viewer_url", None)
    if viewer_url:
        print(f"Live View Link: {viewer_url}")


def main() -> None:
    print("Starting Amazon Product Scraping...")

    api_key = os.environ.get("NOTTE_API_KEY")
    if not api_key:
        raise RuntimeError("Missing NOTTE_API_KEY. Set it in your environment or .env file.")

    client = NotteClient(api_key=api_key)
    search_url = f"https://www.amazon.com/s?k={quote_plus(SEARCH_QUERY)}"

    with client.Session(
        open_viewer=True,
        idle_timeout_minutes=2,
        proxies=True,
        solve_captchas=True,
    ) as session:
        print("Notte session initialized successfully")
        print(f"Session ID: {session.session_id}")
        print_viewer_url(session)

        print(f"Navigating to: {search_url}")
        session.execute(type="goto", url=search_url)

        print("Extracting price-monitoring signals...")
        snapshot = session.scrape(
            instructions=(
                "Build a price-monitoring snapshot from the organic Amazon search results. "
                "Find up to 5 relevant non-sponsored product candidates for the search intent. "
                "For each candidate, extract the title, current price, any crossed-out list price "
                "or typical price, visible deal or coupon text, Prime/shipping/delivery promise, "
                "a short purchase-context note such as bundle, pack size, or variant, and the "
                "product page URL. Ignore ratings, review counts, sponsored placements, banners, "
                "navigation, filters, and ads."
            ),
            response_format=MonitoringSnapshot,
        )

        print("Monitoring snapshot:")
        print(json.dumps(snapshot.model_dump(), indent=2))

    print("Session closed successfully")


if __name__ == "__main__":
    try:
        main()
    except Exception as err:
        print(f"Error in Amazon product scraping: {err}")
        print("Common issues:")
        print("  - Check .env has NOTTE_API_KEY")
        print("  - Amazon may show bot checks or vary layout by region")
        print("Docs: https://docs.notte.cc/")
        exit(1)
