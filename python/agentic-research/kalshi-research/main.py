# Notte: Kalshi Prediction Market Research - See README.md for full documentation
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

from dotenv import load_dotenv
from notte_sdk import NotteClient
from pydantic import BaseModel, Field

load_dotenv(Path(__file__).with_name(".env"))

SEARCH_QUERY = "lowest temperature in Los Angeles today"


class MarketData(BaseModel):
    """Market data extracted from a Kalshi prediction market."""

    marketTitle: str | None = Field(None, description="the title of the market")
    currentOdds: str | None = Field(None, description="the current odds or probability")
    yesPrice: str | None = Field(None, description="the yes price")
    noPrice: str | None = Field(None, description="the no price")
    totalVolume: str | None = Field(None, description="the total trading volume")
    priceChange: str | None = Field(None, description="the recent price change")


def print_viewer_url(session) -> None:
    viewer_url = getattr(session, "viewer_url", None)
    if not viewer_url:
        viewer_url = getattr(session.status(), "viewer_url", None)
    if viewer_url:
        print(f"Watch live: {viewer_url}")


def main() -> None:
    print("Starting Kalshi research automation...")

    api_key = os.environ.get("NOTTE_API_KEY")
    if not api_key:
        raise RuntimeError("Missing NOTTE_API_KEY. Set it in your environment or .env file.")

    client = NotteClient(api_key=api_key)

    with client.Session(
        open_viewer=True,
        idle_timeout_minutes=2,
        proxies=True,
        solve_captchas=True,
    ) as session:
        print("Notte session started successfully")
        print(f"Session ID: {session.session_id}")
        print_viewer_url(session)

        agent = client.Agent(session=session, max_steps=25)
        result = agent.run(
            url="https://kalshi.com/",
            task=(
                f'Search Kalshi for "{SEARCH_QUERY}", open the most relevant market, '
                "and extract the current market title, odds or probability, yes price, "
                "no price, total volume, and recent price change if visible."
            ),
            response_format=MarketData,
        )

        if result.answer is None:
            raise RuntimeError("Agent did not return market data")

        if isinstance(result.answer, MarketData):
            market_data = result.answer.model_dump()
        elif isinstance(result.answer, dict):
            market_data = result.answer
        else:
            market_data = {"answer": str(result.answer)}

        print("Market data extracted successfully:")
        print(json.dumps(market_data, indent=2))

    print("Session closed successfully")


if __name__ == "__main__":
    try:
        main()
    except Exception as err:
        print(f"Error in Kalshi research: {err}")
        print("Common issues:")
        print("  - Check .env has NOTTE_API_KEY")
        print("  - Ensure internet access and https://kalshi.com is accessible")
        print("  - The search query may not map to an active market")
        print("Docs: https://docs.notte.cc/")
        exit(1)
