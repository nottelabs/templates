# Notte: Webscraper.io Ecommerce Demo
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

import argparse
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse, urlunparse

from dotenv import load_dotenv
from notte_sdk import NotteClient

load_dotenv(Path(__file__).with_name(".env"))

DEFAULT_CATEGORY_URL = os.environ.get(
    "WEBSCRAPER_CATEGORY_URL",
    "http://webscraper.io/test-sites/e-commerce/static/computers/laptops",
)
DEFAULT_RESULT_LIMIT = int(os.environ.get("WEBSCRAPER_RESULT_LIMIT", "12"))
MAX_RESULT_LIMIT = 120


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scrape product cards from the Webscraper.io ecommerce demo with Notte."
    )
    parser.add_argument(
        "--category-url",
        default=DEFAULT_CATEGORY_URL,
        help=f"Webscraper.io category URL to scrape (default: {DEFAULT_CATEGORY_URL!r}).",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=DEFAULT_RESULT_LIMIT,
        help=f"Maximum number of products to return (default: {DEFAULT_RESULT_LIMIT}).",
    )
    return parser.parse_args()


def webscraper_browser_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.netloc == "webscraper.io" and parsed.scheme == "https":
        parsed = parsed._replace(scheme="http")
    return urlunparse(parsed)


def current_page_number(url: str) -> int:
    value = parse_qs(urlparse(url).query).get("page", ["1"])[0]
    return int(value) if value.isdigit() else 1


def parse_price(value: str | None) -> float | None:
    if not value:
        return None
    match = re.search(r"[\d.]+", value)
    return float(match.group(0)) if match else None


def parse_review_count(value: str | None) -> int | None:
    if not value:
        return None
    match = re.search(r"\d+", value)
    return int(match.group(0)) if match else None


def print_viewer_url(session) -> None:
    viewer_url = getattr(session, "viewer_url", None)
    if not viewer_url:
        viewer_url = getattr(session.status(), "viewer_url", None)
    if viewer_url:
        print(f"Live View: {viewer_url}")


def accept_cookie_banner(page) -> None:
    button = page.get_by_role("button", name=re.compile("accept", re.IGNORECASE))
    try:
        if button.count() > 0:
            button.first.click(timeout=2500)
    except Exception:
        pass


def extract_listing_metadata(page) -> dict[str, Any]:
    return page.evaluate(
        """() => {
            const text = document.body.innerText || "";
            const category = Array.from(document.querySelectorAll("h1, h2, .page-header"))
                .map(el => el.textContent.trim())
                .find(value => value.includes("/") || value.includes("Laptops") || value.includes("Tablets") || value.includes("Phones"));
            const total = text.match(/\\b\\d+\\s+items\\b/i)?.[0] || null;
            return { category_title: category || null, total_item_count_text: total };
        }"""
    )


def extract_product_cards(page, page_number: int, max_items: int) -> list[dict[str, Any]]:
    raw_products = page.evaluate(
        """(maxItems) => Array.from(document.querySelectorAll(".thumbnail")).slice(0, maxItems).map((card, index) => {
            const link = card.querySelector("a.title");
            const reviewText = Array.from(card.querySelectorAll("p"))
                .map(p => p.textContent.trim())
                .find(text => /reviews?/i.test(text)) || null;
            return {
                page_position: index + 1,
                title: link?.textContent?.trim() || null,
                detail_url: link?.href || null,
                price_text: card.querySelector(".price")?.textContent?.trim() || null,
                description: card.querySelector(".description")?.textContent?.trim() || null,
                reviews_text: reviewText,
                image_url: card.querySelector("img")?.src || null
            };
        })""",
        max_items,
    )

    products: list[dict[str, Any]] = []
    for product in raw_products:
        product["listing_page"] = page_number
        product["price"] = parse_price(product.get("price_text"))
        product["review_count"] = parse_review_count(product.get("reviews_text"))
        products.append(product)
    return products


def scrape_category(category_url: str, result_limit: int) -> dict[str, Any]:
    if result_limit < 1:
        raise ValueError("Limit must be at least 1.")
    result_limit = min(result_limit, MAX_RESULT_LIMIT)

    requested_url = category_url
    browser_url = webscraper_browser_url(category_url)
    api_key = os.environ.get("NOTTE_API_KEY")
    client = NotteClient(api_key=api_key) if api_key else NotteClient()

    products: list[dict[str, Any]] = []
    metadata: dict[str, Any] = {}

    with client.Session(open_viewer=True, idle_timeout_minutes=5, use_file_storage=True) as session:
        print(f"Session ID: {session.session_id}")
        print_viewer_url(session)

        page = session.page
        next_url = browser_url

        while next_url and len(products) < result_limit:
            page_number = current_page_number(next_url)
            print(f"Scraping page {page_number}: {next_url}")
            page.goto(next_url, wait_until="domcontentloaded", timeout=30000)
            accept_cookie_banner(page)
            page.wait_for_selector(".thumbnail", timeout=10000)

            if not metadata:
                metadata = extract_listing_metadata(page)

            remaining = result_limit - len(products)
            products.extend(extract_product_cards(page, page_number, remaining))

            if len(products) >= result_limit:
                break

            following_page = page.evaluate(
                """() => {
                    const next = Array.from(document.querySelectorAll("ul.pagination a"))
                        .find(link => link.textContent.trim() === ">");
                    const unicodeNext = Array.from(document.querySelectorAll("ul.pagination a"))
                        .find(link => link.textContent.trim() === "›");
                    return (next || unicodeNext)?.href || null;
                }"""
            )

            if not following_page:
                next_url = None
            else:
                parsed_next = urlparse(following_page)
                next_url = webscraper_browser_url(urlunparse(parsed_next))

    return {
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "requested_category_url": requested_url,
        "browser_category_url": browser_url,
        "category_title": metadata.get("category_title"),
        "total_item_count_text": metadata.get("total_item_count_text"),
        "result_limit": result_limit,
        "products_returned": len(products),
        "products": products,
    }


def main() -> None:
    args = parse_args()
    report = scrape_category(category_url=args.category_url, result_limit=args.limit)
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except Exception as err:
        print(f"Error scraping Webscraper.io ecommerce demo: {err}")
        print("Common fixes:")
        print("  - Set NOTTE_API_KEY in your environment or .env file")
        print("  - Use a Webscraper.io static category URL")
        print("  - Keep --limit small while testing, for example: uv run main.py --limit 6")
        raise SystemExit(1)
