# Notte: Weather Proxy Demo - See README.md for full documentation
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "notte-sdk",
#     "pydantic",
#     "python-dotenv",
# ]
# ///

import os
from pathlib import Path

from dotenv import load_dotenv
from notte_sdk import NotteClient
from pydantic import BaseModel, Field

load_dotenv(Path(__file__).with_name(".env"))


class LocationConfig(BaseModel):
    """Configuration for country proxy settings."""

    label: str
    proxy_country: str


class WeatherResult(BaseModel):
    """Result structure for weather data extraction."""

    label: str
    proxy_country: str
    location: str | None = None
    region: str | None = None
    country: str | None = None
    temperature: float | None = None
    unit: str | None = None
    condition: str | None = None
    humidity: int | None = None
    error: str | None = None


class TemperatureData(BaseModel):
    """Schema for weather extraction."""

    location: str | None = Field(
        None, description="The nearest area name from the weather response"
    )
    region: str | None = Field(None, description="The region or state from the weather response")
    country: str | None = Field(None, description="The country from the weather response")
    temperature: float | None = Field(None, description="The current temperature value in Celsius")
    unit: str | None = Field(None, description="The temperature unit, usually C")
    condition: str | None = Field(None, description="The current weather description")
    humidity: int | None = Field(None, description="The current humidity percentage")


def print_viewer_url(session) -> None:
    viewer_url = getattr(session, "viewer_url", None)
    if not viewer_url:
        viewer_url = getattr(session.status(), "viewer_url", None)
    if viewer_url:
        print(f"Session URL: {viewer_url}")


def get_weather_for_location(client: NotteClient, location: LocationConfig) -> WeatherResult:
    print(f"\n=== Getting weather through {location.label} proxy ===")

    try:
        with client.Session(
            open_viewer=True,
            idle_timeout_minutes=2,
            proxies=location.proxy_country,
            viewport_width=1080,
            viewport_height=720,
        ) as session:
            print(f"Session ID: {session.session_id}")
            print_viewer_url(session)

            print("Navigating to wttr.in weather service...")
            session.execute(type="goto", url="https://wttr.in/")
            session.execute(type="wait", time_ms=1000)

            print("Extracting temperature data...")
            weather = session.scrape(
                instructions=(
                    "Extract the location shown in the weather report, the region or state if visible, "
                    "the country if visible, the current temperature in Celsius as temperature, "
                    "C as unit, the current weather condition, and humidity from the wttr.in page."
                ),
                response_format=TemperatureData,
            )

            print(
                "Extracted weather data: "
                f"{weather.location}, {weather.region}, {weather.country} - "
                f"{weather.temperature} {weather.unit}, {weather.condition}"
            )
            return WeatherResult(
                label=location.label,
                proxy_country=location.proxy_country,
                location=weather.location,
                region=weather.region,
                country=weather.country,
                temperature=weather.temperature,
                unit=weather.unit,
                condition=weather.condition,
                humidity=weather.humidity,
            )
    except Exception as error:
        print(f"Error getting weather through {location.label}: {error}")
        return WeatherResult(
            label=location.label,
            proxy_country=location.proxy_country,
            error=str(error),
        )


def display_results(results: list[WeatherResult]) -> None:
    print("\n=== Weather Results ===")
    for result in results:
        if result.error:
            print(f"{result.label} ({result.proxy_country}): Error - {result.error}")
        else:
            print(
                f"{result.label} ({result.proxy_country}): "
                f"{result.location}, {result.region}, {result.country} - "
                f"{result.temperature} {result.unit}, {result.condition}, "
                f"humidity {result.humidity}%"
            )


def main() -> None:
    api_key = os.environ.get("NOTTE_API_KEY")
    if not api_key:
        raise RuntimeError("Missing NOTTE_API_KEY. Set it in your environment or .env file.")

    locations = [
        LocationConfig(label="United States", proxy_country="us"),
        LocationConfig(label="United Kingdom", proxy_country="gb"),
        LocationConfig(label="Japan", proxy_country="jp"),
        LocationConfig(label="Brazil", proxy_country="br"),
    ]

    client = NotteClient(api_key=api_key)

    print("=== Weather Proxy Demo - Running Sequentially ===\n")
    print(f"Processing {len(locations)} locations with country proxies...\n")

    results = [get_weather_for_location(client, location) for location in locations]
    display_results(results)
    print("\n=== All locations completed ===")


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
