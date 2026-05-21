# Notte: Amazon Global Price Comparison - See README.md for full documentation
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "notte-sdk",
#     "python-dotenv",
#     "pydantic",
# ]
# ///

import asyncio
import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv
from notte_sdk import NotteClient
from pydantic import BaseModel, Field

load_dotenv(Path(__file__).with_name(".env"))
logging.disable(logging.CRITICAL)

DEFAULT_OUTPUT_PATH = Path("output/amazon-global-price-comparison/results.json")


class Offer(BaseModel):
    """Schema for extracted offer data from Amazon search results."""

    title: str = Field(..., description="The full product title shown in search results")
    local_price: str = Field(default="N/A", description="The visible local price including currency symbol")
    availability: str = Field(default="N/A", description="Availability or stock message shown on the listing")
    delivery_estimate: str = Field(default="N/A", description="Delivery date, Prime, or shipping promise")
    seller_or_fulfillment: str = Field(default="N/A", description="Seller, fulfillment, or marketplace badge text")
    deal_note: str = Field(default="N/A", description="Coupon, discount, or savings note if visible")
    product_url: str = Field(default="N/A", description="The product detail URL")


class OffersResult(BaseModel):
    offers: list[Offer] = Field(default_factory=list)


@dataclass
class CountryConfig:
    name: str
    code: str
    currency: str


COUNTRIES: list[CountryConfig] = [
    CountryConfig(name="United States", code="us", currency="USD"),
    CountryConfig(name="Canada", code="ca", currency="CAD"),
    CountryConfig(name="United Kingdom", code="gb", currency="GBP"),
    CountryConfig(name="Australia", code="au", currency="AUD"),
    CountryConfig(name="Japan", code="jp", currency="JPY"),
]


@dataclass
class CountryResult:
    country: str
    country_code: str
    currency: str
    offers: list[dict]
    error: str | None = None
    session_id: str | None = None


def create_client() -> NotteClient:
    api_key = os.environ.get("NOTTE_API_KEY")
    if not api_key:
        raise RuntimeError("Missing NOTTE_API_KEY. Set it in your environment or .env file.")
    return NotteClient(api_key=api_key)


def quoted_instruction_value(instruction: str) -> str | None:
    for quote in ('"', "'"):
        parts = instruction.split(quote, 2)
        if len(parts) == 3 and parts[1]:
            return parts[1]
    return None


def act(session, instruction: str) -> None:
    actions = session.observe(instructions=instruction)
    if not actions:
        raise RuntimeError(f"No action found for instruction: {instruction}")
    action = actions[0]
    if getattr(action, "type", None) == "fill":
        value = quoted_instruction_value(instruction)
        if value:
            action.value = value
    session.execute(action=action)


def wait_for_page_after_navigation(session) -> None:
    page = getattr(session, "page", None)
    if page is None:
        session.execute(type="wait", time_ms=5000)
        return

    try:
        page.wait_for_load_state("domcontentloaded", timeout=15000)
        page.wait_for_load_state("networkidle", timeout=15000)
    except Exception:
        session.execute(type="wait", time_ms=5000)


def clean_offers(offers: list[Offer], results_count: int) -> list[dict]:
    cleaned_offers = []
    for offer in offers:
        product_url = offer.product_url or "N/A"
        if product_url.startswith("/"):
            product_url = f"https://www.amazon.com{product_url}"

        cleaned_offers.append(
            {
                "title": offer.title or "Unknown",
                "local_price": offer.local_price or "N/A",
                "availability": offer.availability or "N/A",
                "delivery_estimate": offer.delivery_estimate or "N/A",
                "seller_or_fulfillment": offer.seller_or_fulfillment or "N/A",
                "deal_note": offer.deal_note or "N/A",
                "product_url": product_url,
            }
        )
    return cleaned_offers[:results_count]


def get_offers_for_country_sync(
    client: NotteClient,
    search_query: str,
    country: CountryConfig,
    results_count: int = 2,
) -> CountryResult:
    try:
        with client.Session(
            open_viewer=False,
            idle_timeout_minutes=2,
            proxies=country.code,
            solve_captchas=True,
        ) as session:
            session_id = getattr(session, "session_id", None) or getattr(session, "id", None)
            session.execute(type="goto", url="https://www.amazon.com")

            session.execute(type="wait", time_ms=4000)

            act(session, f'Type "{search_query}" into the search bar')
            session.execute(type="press_key", key="Enter")
            wait_for_page_after_navigation(session)

            result = session.scrape(
                instructions=(
                    f"Extract up to {results_count} organic offers from this Amazon search results page. "
                    "For each offer, extract the title, visible local price with currency symbol, "
                    "availability or stock message, delivery date or shipping promise, seller or fulfillment "
                    "badge, deal/coupon/savings note if visible, and product URL. Ignore ratings, review "
                    "counts, sponsored placements, banners, filters, and navigation."
                ),
                response_format=OffersResult,
            )

            offers = clean_offers(result.offers, results_count)

            return CountryResult(
                country=country.name,
                country_code=country.code.upper(),
                currency=country.currency,
                offers=offers,
                session_id=session_id,
            )

    except Exception as error:
        return CountryResult(
            country=country.name,
            country_code=country.code.upper(),
            currency=country.currency,
            offers=[],
            error=str(error),
            session_id=locals().get("session_id"),
        )


async def get_offers_for_country(
    client: NotteClient,
    search_query: str,
    country: CountryConfig,
    results_count: int = 2,
) -> CountryResult:
    return await asyncio.to_thread(
        get_offers_for_country_sync,
        client,
        search_query,
        country,
        results_count,
    )


def display_comparison_table(results: list[CountryResult]) -> None:
    print("\n" + "=" * 100)
    print("GLOBAL OFFER AVAILABILITY SNAPSHOT")
    print("=" * 100)

    successful_result = next((r for r in results if r.offers), None)
    if not successful_result:
        print("No offers found in any country.")
        return

    max_offers = max(len(r.offers) for r in results)
    for i in range(max_offers):
        print(f"\n--- Offer {i + 1} ---")

        offer_title = next((r.offers[i].get("title") for r in results if i < len(r.offers)), None)
        if offer_title:
            truncated_title = offer_title[:77] + "..." if len(offer_title) > 80 else offer_title
            print(f"Offer: {truncated_title}")

        print("\nAvailability by Country:")
        print("-" * 70)

        for result in results:
            country_pad = result.country.ljust(20)
            if result.error:
                session_suffix = f" [{result.session_id}]" if result.session_id else ""
                print(f"  {country_pad} | Error{session_suffix}: {result.error}")
            elif i < len(result.offers):
                offer = result.offers[i]
                price_pad = offer.get("local_price", "N/A").ljust(18)
                availability = offer.get("availability", "N/A")
                delivery = offer.get("delivery_estimate", "N/A")
                deal = offer.get("deal_note", "N/A")
                print(f"  {country_pad} | {price_pad} | {availability} | {delivery} | {deal}")
            else:
                print(f"  {country_pad} | No comparable offer found")

    print("\n" + "=" * 100)


def save_results(results: list[CountryResult]) -> None:
    output_path = Path(os.environ.get("OUTPUT_PATH", DEFAULT_OUTPUT_PATH))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    json_results = [
        {
            "country": result.country,
            "countryCode": result.country_code,
            "currency": result.currency,
            "offers": result.offers,
            "error": result.error,
            "sessionId": result.session_id,
        }
        for result in results
    ]
    output_path.write_text(json.dumps(json_results, indent=2), encoding="utf-8")


async def main() -> None:
    search_query = os.environ.get("SEARCH_QUERY", "65W GaN travel charger international adapters")
    results_count = int(os.environ.get("RESULTS_COUNT", "2"))

    client = create_client()
    results = await asyncio.gather(
        *[get_offers_for_country(client, search_query, country, results_count) for country in COUNTRIES]
    )

    results_list = list(results)
    display_comparison_table(results_list)
    save_results(results_list)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as err:
        print(f"Application error: {err}")
        print("\nCommon issues:")
        print("  - Check .env file has NOTTE_API_KEY")
        print("  - Verify proxy countries are supported")
        print("  - Amazon may block or vary content by region")
        print("Docs: https://docs.notte.cc/")
        raise SystemExit(1)
