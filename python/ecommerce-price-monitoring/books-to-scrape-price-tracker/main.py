# Notte: Books to Scrape Price Tracker
# See README.md for full documentation
#
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "notte-sdk[playwright]",
#     "python-dotenv",
# ]
# ///

from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

from dotenv import load_dotenv
from notte_sdk import NotteClient

load_dotenv(Path(__file__).with_name(".env"))

BASE_URL = "http://books.toscrape.com/"
DEFAULT_MAX_PAGES = 2
DEFAULT_MAX_BOOKS = 40
DEFAULT_PRICE_ALERT_BELOW = 20.00
RATING_CLASSES = {"One", "Two", "Three", "Four", "Five"}


def env_bool(name: str, default: bool) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def parse_price(value: str | None) -> float | None:
    if not value:
        return None
    match = re.search(r"[\d.]+", value)
    return float(match.group(0)) if match else None


def parse_available_count(value: str | None) -> int | None:
    if not value:
        return None
    match = re.search(r"\((\d+) available\)", value)
    return int(match.group(1)) if match else None


def text_or_none(locator) -> str | None:
    if locator.count() == 0:
        return None
    text = locator.first.text_content()
    return text.strip() if text else None


def rating_from_classes(class_name: str | None) -> str | None:
    if not class_name:
        return None
    return next((name for name in class_name.split() if name in RATING_CLASSES), None)


def extract_listing_books(page, page_number: int, max_remaining: int) -> list[dict[str, Any]]:
    books: list[dict[str, Any]] = []
    cards = page.locator("article.product_pod")

    for index in range(min(cards.count(), max_remaining)):
        card = cards.nth(index)
        title_link = card.locator("h3 a")
        detail_href = title_link.get_attribute("href") or ""
        image_src = card.locator(".image_container img").get_attribute("src") or ""
        price_text = text_or_none(card.locator(".price_color"))
        stock_text = text_or_none(card.locator(".availability"))
        rating_class = card.locator(".star-rating").get_attribute("class")

        title = title_link.get_attribute("title") or text_or_none(title_link)
        detail_url = urljoin(page.url, detail_href)

        books.append(
            {
                "title": title,
                "price_text": price_text,
                "price": parse_price(price_text),
                "currency": "GBP",
                "stock_status": stock_text,
                "availability_count": parse_available_count(stock_text),
                "rating": rating_from_classes(rating_class),
                "detail_url": detail_url,
                "image_url": urljoin(page.url, image_src),
                "listing_page": page_number,
            }
        )

    return books


def extract_detail_fields(page, detail_url: str) -> dict[str, Any]:
    page.goto(detail_url, wait_until="domcontentloaded", timeout=30000)
    page.wait_for_selector(".product_main h1", timeout=10000)

    table_rows = page.locator("table.table.table-striped tr")
    facts: dict[str, str] = {}
    for index in range(table_rows.count()):
        row = table_rows.nth(index)
        key = text_or_none(row.locator("th"))
        value = text_or_none(row.locator("td"))
        if key and value:
            facts[key] = value

    breadcrumbs = [
        item.strip()
        for item in page.locator(".breadcrumb li a").all_text_contents()
        if item.strip() and item.strip() != "Home"
    ]
    detail_rating = page.locator(".product_main .star-rating").get_attribute("class")
    image_src = page.locator(".item.active img").get_attribute("src") or ""

    return {
        "upc": facts.get("UPC"),
        "product_type": facts.get("Product Type"),
        "price_excluding_tax_text": facts.get("Price (excl. tax)"),
        "price_including_tax_text": facts.get("Price (incl. tax)"),
        "tax_text": facts.get("Tax"),
        "availability_text": facts.get("Availability"),
        "availability_count": parse_available_count(facts.get("Availability")),
        "review_count": int(facts["Number of reviews"]) if facts.get("Number of reviews", "").isdigit() else None,
        "category_path": breadcrumbs,
        "description": text_or_none(page.locator("#product_description + p")),
        "detail_rating": rating_from_classes(detail_rating),
        "detail_image_url": urljoin(page.url, image_src),
    }


def next_page_url(page) -> str | None:
    next_link = page.locator("li.next a")
    if next_link.count() == 0:
        return None
    href = next_link.first.get_attribute("href")
    return urljoin(page.url, href) if href else None


def print_viewer_url(session) -> None:
    viewer_url = getattr(session, "viewer_url", None)
    if not viewer_url:
        viewer_url = getattr(session.status(), "viewer_url", None)
    if viewer_url:
        print(f"Live View Link: {viewer_url}")


def run(
    start_url: str = BASE_URL,
    max_pages: int = DEFAULT_MAX_PAGES,
    max_books: int = DEFAULT_MAX_BOOKS,
    price_alert_below: float = DEFAULT_PRICE_ALERT_BELOW,
    low_stock_threshold: int = 5,
    include_details: bool = True,
) -> dict[str, Any]:
    client = NotteClient(api_key=os.environ.get("NOTTE_API_KEY"))
    observed_at = datetime.now(timezone.utc).isoformat()
    books: list[dict[str, Any]] = []
    page_url = start_url

    with client.Session(open_viewer=True, idle_timeout_minutes=2) as session:
        print("Notte session initialized successfully")
        print(f"Session ID: {session.session_id}")
        print_viewer_url(session)

        page = session.page
        for page_number in range(1, max_pages + 1):
            if not page_url or len(books) >= max_books:
                break

            print(f"Scraping catalog page {page_number}: {page_url}")
            page.goto(page_url, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_selector("article.product_pod", timeout=10000)

            remaining = max_books - len(books)
            page_books = extract_listing_books(page, page_number, remaining)
            following_page = next_page_url(page)

            if include_details:
                for book in page_books:
                    print(f"  Fetching detail fields: {book['title']}")
                    book.update(extract_detail_fields(page, book["detail_url"]))

            books.extend(page_books)
            page_url = following_page

    price_alerts = [
        book for book in books if book.get("price") is not None and book["price"] <= price_alert_below
    ]
    low_stock_alerts = [
        book
        for book in books
        if book.get("availability_count") is not None and book["availability_count"] <= low_stock_threshold
    ]
    cheapest = sorted(
        (book for book in books if book.get("price") is not None),
        key=lambda item: item["price"],
    )[:5]

    return {
        "observed_at": observed_at,
        "source": start_url,
        "books_checked": len(books),
        "price_alert_below": price_alert_below,
        "low_stock_threshold": low_stock_threshold,
        "price_alerts": price_alerts,
        "low_stock_alerts": low_stock_alerts,
        "cheapest_books": cheapest,
        "books": books,
    }


def main() -> None:
    if not os.environ.get("NOTTE_API_KEY"):
        raise RuntimeError("Missing NOTTE_API_KEY. Set it in your environment or .env file.")

    result = run(
        start_url=os.environ.get("BOOKS_START_URL", BASE_URL),
        max_pages=int(os.environ.get("BOOKS_MAX_PAGES", DEFAULT_MAX_PAGES)),
        max_books=int(os.environ.get("BOOKS_MAX_BOOKS", DEFAULT_MAX_BOOKS)),
        price_alert_below=float(os.environ.get("BOOKS_PRICE_ALERT_BELOW", DEFAULT_PRICE_ALERT_BELOW)),
        low_stock_threshold=int(os.environ.get("BOOKS_LOW_STOCK_THRESHOLD", 5)),
        include_details=env_bool("BOOKS_INCLUDE_DETAILS", True),
    )

    output_path = os.environ.get("BOOKS_OUTPUT_PATH")
    if output_path:
        Path(output_path).write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(f"Wrote snapshot to {output_path}")

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    try:
        main()
    except Exception as err:
        print(f"Error in Books to Scrape price tracker: {err}")
        print("Common issues:")
        print("  - Check .env has NOTTE_API_KEY")
        print("  - Use http://books.toscrape.com/; HTTPS may fail in some browser sessions")
        print("  - Lower BOOKS_MAX_PAGES or set BOOKS_INCLUDE_DETAILS=false for a faster run")
        print("Docs: https://docs.notte.cc/")
        raise SystemExit(1)
