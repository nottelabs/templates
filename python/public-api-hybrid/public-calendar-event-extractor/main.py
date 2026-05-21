# Notte: Public Calendar Event Extractor - See README.md for full documentation
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "notte-sdk[playwright]",
#     "pydantic",
#     "python-dotenv",
#     "requests",
# ]
# ///

from __future__ import annotations

import argparse
import json
import os
import re
from html import unescape
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

import requests
from dotenv import load_dotenv
from notte_sdk import NotteClient
from pydantic import BaseModel, Field

load_dotenv(Path(__file__).with_name(".env"))

DEFAULT_EVENTS_URL = os.environ.get("LOC_EVENTS_URL", "https://www.loc.gov/events/")
DEFAULT_RESULT_LIMIT = int(os.environ.get("LOC_EVENT_LIMIT", "5"))
USE_PROXY = os.environ.get("USE_PROXY", "true").lower() not in {"0", "false", "no"}
HTTP_HEADERS = {
    "Accept": "application/json",
    "User-Agent": "bb-templates-public-calendar-event-extractor/1.0",
}


class CalendarEvent(BaseModel):
    title: str | None = Field(None, description="Event title.")
    url: str | None = Field(None, description="Event detail URL.")
    date: str | None = Field(None, description="Event date from the listing.")
    start_time: str | None = Field(None, description="Local event start timestamp when available.")
    end_time: str | None = Field(None, description="Local event end timestamp when available.")
    venue: str | None = Field(None, description="Building, campus, or online venue text.")
    attendance: str | None = Field(None, description="Attendance condition, for example ticket or none.")
    status: str | None = Field(None, description="Event status.")
    categories: list[str] = Field(default_factory=list, description="LOC event categories.")
    description: str | None = Field(None, description="Short event description.")


class EventExtractionReport(BaseModel):
    listing_url: str
    api_url: str
    limit: int
    pagination: str | None = None
    result_count: int
    browser_status: str
    events: list[CalendarEvent] = Field(default_factory=list)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract public events from a Library of Congress event listing.")
    parser.add_argument(
        "--url",
        default=DEFAULT_EVENTS_URL,
        help=f"Event listing URL to extract. Defaults to LOC_EVENTS_URL or {DEFAULT_EVENTS_URL!r}.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=DEFAULT_RESULT_LIMIT,
        help=f"Maximum number of events to return. Defaults to LOC_EVENT_LIMIT or {DEFAULT_RESULT_LIMIT}.",
    )
    return parser.parse_args()


def validate_limit(limit: int) -> int:
    if limit < 1:
        raise ValueError("Limit must be at least 1.")
    return min(limit, 50)


def loc_json_url(listing_url: str, limit: int) -> str:
    parsed = urlparse(listing_url.strip())
    if not parsed.scheme or not parsed.netloc:
        raise ValueError("Listing URL must be absolute, for example https://www.loc.gov/events/.")
    if not parsed.netloc.endswith("loc.gov"):
        raise ValueError("This template only accepts loc.gov event listing URLs.")

    query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    query["fo"] = "json"
    query["c"] = str(limit)
    return urlunparse(parsed._replace(query=urlencode(query)))


def clean_text(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, list):
        value = " ".join(str(part) for part in value if part)
    text = re.sub(r"<[^>]+>", " ", str(value))
    text = unescape(re.sub(r"\s+", " ", text)).strip()
    return text or None


def venue_from_item(item: dict[str, Any]) -> str | None:
    parts = [
        item.get("location_label"),
        item.get("location"),
        item.get("building"),
        item.get("campus"),
    ]
    if item.get("online"):
        parts.insert(0, "Online")
    seen: set[str] = set()
    clean_parts = []
    for part in parts:
        text = clean_text(part)
        if text and text not in seen:
            seen.add(text)
            clean_parts.append(text)
    return ", ".join(clean_parts) if clean_parts else None


def normalize_event(raw_event: dict[str, Any]) -> CalendarEvent:
    item = raw_event.get("item") or {}
    description = clean_text(raw_event.get("description") or item.get("description") or item.get("article"))

    return CalendarEvent(
        title=clean_text(raw_event.get("title") or item.get("title")),
        url=raw_event.get("url") or raw_event.get("id"),
        date=raw_event.get("date"),
        start_time=item.get("event_start") or item.get("event_start_date_local"),
        end_time=item.get("event_end") or item.get("event_end_date_local"),
        venue=venue_from_item(item),
        attendance=item.get("attendance_conditions"),
        status=item.get("event_status"),
        categories=[str(category) for category in item.get("categories", []) if category],
        description=description,
    )


def print_viewer_url(session) -> None:
    viewer_url = getattr(session, "viewer_url", None)
    if not viewer_url:
        viewer_url = getattr(session.status(), "viewer_url", None)
    if viewer_url:
        print(f"Live View: {viewer_url}")


def browser_probe(client: NotteClient, listing_url: str) -> str:
    try:
        with client.Session(
            open_viewer=True,
            idle_timeout_minutes=3,
            proxies=USE_PROXY,
            use_file_storage=True,
        ) as session:
            print(f"Session ID: {session.session_id}")
            print_viewer_url(session)
            print(f"Opening LOC events listing for browser trace: {listing_url}")
            page = session.page
            page.goto(listing_url, wait_until="domcontentloaded", timeout=15000)
            title = page.title()
            return f"browser visit succeeded: {title}"
    except Exception as err:
        return f"browser visit failed; continued with LOC JSON endpoint: {err}"


def fetch_events(api_url: str, limit: int) -> tuple[str | None, list[CalendarEvent]]:
    response = requests.get(api_url, headers=HTTP_HEADERS, timeout=30)
    response.raise_for_status()
    payload = response.json()
    content = payload.get("content") or {}
    raw_events = content.get("results") or []
    events = [normalize_event(raw_event) for raw_event in raw_events[:limit]]
    return content.get("pagination"), events


def extract_events(listing_url: str, limit: int) -> EventExtractionReport:
    limit = validate_limit(limit)
    api_url = loc_json_url(listing_url, limit)

    api_key = os.environ.get("NOTTE_API_KEY")
    if api_key:
        client = NotteClient(api_key=api_key)
        browser_status = browser_probe(client, listing_url)
    else:
        browser_status = "browser probe skipped: NOTTE_API_KEY is not set"
    print(browser_status)

    print(f"Fetching LOC events JSON: {api_url}")
    pagination, events = fetch_events(api_url, limit)

    return EventExtractionReport(
        listing_url=listing_url,
        api_url=api_url,
        limit=limit,
        pagination=pagination,
        result_count=len(events),
        browser_status=browser_status,
        events=events,
    )


def main() -> None:
    args = parse_args()
    report = extract_events(args.url, args.limit)
    print(json.dumps(report.model_dump(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except Exception as err:
        print(f"Error extracting public calendar events: {err}")
        print("Common fixes:")
        print("  - Set NOTTE_API_KEY in your environment or .env file to enable the Notte browser probe")
        print("  - Use a Library of Congress events URL, for example: uv run main.py --url https://www.loc.gov/events/ --limit 5")
        print("  - Set USE_PROXY=false if your Notte browser session has proxy issues")
        raise SystemExit(1)
