# Notte Proxy Testing Script - See README.md for full documentation
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


class GeoInfo(BaseModel):
    """Schema for IP information and geolocation data."""

    ip: str | None = Field(None, description="The detected public IPv4 or IPv6 address")
    city: str | None = Field(None, description="The city name")
    state: str | None = Field(None, description="The state or region")
    country: str | None = Field(None, description="The country code if available")
    country_name: str | None = Field(None, description="The country name")
    latitude: float | None = Field(None, description="The latitude coordinate")
    longitude: float | None = Field(None, description="The longitude coordinate")
    postal: str | None = Field(None, description="The postal code")


def print_viewer_url(session) -> None:
    viewer_url = getattr(session, "viewer_url", None)
    if not viewer_url:
        viewer_url = getattr(session.status(), "viewer_url", None)
    if viewer_url:
        print(f"Session URL: {viewer_url}")


def test_session(client: NotteClient, session_name: str, proxies: bool | str) -> None:
    print(f"\n=== Testing {session_name} ===")

    with client.Session(open_viewer=True, idle_timeout_minutes=2, proxies=proxies) as session:
        print(f"Session ID: {session.session_id}")
        print_viewer_url(session)

        session.execute(type="goto", url="https://browserleaks.com/ip")
        session.execute(type="wait", time_ms=1500)
        session.execute(type="scroll_down")
        session.execute(type="scroll_up")
        geo_info = session.scrape(
            instructions=(
                "Extract the detected public IP address, city, state or region, country code if shown, "
                "country name, latitude, longitude, and postal code from the BrowserLeaks IP page. "
                "Use the IP address and geolocation tables on the page."
            ),
            response_format=GeoInfo,
        )

        print("Geo Info:", json.dumps(geo_info.model_dump(), indent=2))

    print(f"{session_name} test completed")


def main() -> None:
    api_key = os.environ.get("NOTTE_API_KEY")
    if not api_key:
        raise RuntimeError("Missing NOTTE_API_KEY. Set it in your environment or .env file.")

    client = NotteClient(api_key=api_key)

    # Test 1: Built-in proxies - verify default proxy rotation works.
    test_session(client, "Built-in Proxies", True)

    # Test 2: Country proxy - route traffic through the United States.
    test_session(client, "Country Proxy (United States)", "us")

    # Custom external proxies can be configured with Notte proxy settings when needed.
    print("\n=== All tests completed ===")


if __name__ == "__main__":
    try:
        main()
    except Exception as err:
        print(f"Application error: {err}")
        print("Common issues:")
        print("  - Check .env has NOTTE_API_KEY")
        print("  - Verify proxy access is enabled for your Notte account")
        print("Docs: https://docs.notte.cc/")
        exit(1)
