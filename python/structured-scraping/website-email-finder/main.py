#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "notte-sdk",
#     "python-dotenv",
# ]
# ///
"""Find email addresses on a website and its likely contact pages."""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from collections import defaultdict
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urljoin, urlsplit, urlunsplit

from dotenv import load_dotenv
from notte_sdk import NotteClient

load_dotenv(Path(__file__).with_name(".env"))

EMAIL_RE = re.compile(
    r"(?<![\w.+/@-])([a-z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-z0-9-]+(?:\.[a-z][a-z0-9-]{1,62})+)(?![\w.-])",
    re.IGNORECASE,
)
CONTACT_HINT_RE = re.compile(
    r"\b(contact(?: us)?|get in touch|reach us|email us|talk to us|support|customer service|help(?: center| desk)?)\b",
    re.IGNORECASE,
)
FALLBACK_PATHS = ("/contact", "/contact-us", "/get-in-touch", "/support")
MARKDOWN_LINK_RE = re.compile(r'\[([^\]]+)\]\(([^)\s]+)(?:\s+"[^"]*")?\)')
NON_PAGE_SUFFIXES = {
    ".avi",
    ".gif",
    ".jpeg",
    ".jpg",
    ".mov",
    ".mp3",
    ".mp4",
    ".mpeg",
    ".pdf",
    ".png",
    ".svg",
    ".webm",
    ".webp",
}


class LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[tuple[str, str]] = []
        self._href: str | None = None
        self._label_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "a":
            return
        attributes = dict(attrs)
        href = attributes.get("href")
        if href:
            self._href = href
            self._label_parts = [attributes.get("aria-label") or "", attributes.get("title") or ""]

    def handle_data(self, data: str) -> None:
        if self._href is not None:
            self._label_parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "a" and self._href is not None:
            self.links.append((self._href, " ".join(self._label_parts)))
            self._href = None
            self._label_parts = []


def normalize_url(value: str) -> str:
    if "://" not in value:
        value = f"https://{value}"
    parts = urlsplit(value)
    if parts.scheme not in {"http", "https"} or not parts.netloc:
        raise ValueError("URL must be an HTTP(S) address, for example https://example.com")
    return urlunsplit((parts.scheme, parts.netloc, parts.path or "/", parts.query, ""))


def origin(url: str) -> str:
    parts = urlsplit(url)
    return urlunsplit((parts.scheme, parts.netloc, "", "", ""))


def scrape_page(session: Any, url: str) -> tuple[str, str]:
    result = session.execute(type="goto", url=url, raise_on_failure=False)
    if not result.success:
        raise RuntimeError(str(result.exception or result.message))
    markdown = session.scrape(only_main_content=False, scrape_links=True)
    return url, markdown


def extract_emails(body: str) -> set[str]:
    # Decoding catches addresses in mailto links and common percent/HTML encoding.
    decoded = unquote(html.unescape(body))
    return {match.group(1).lower().rstrip(".,;:") for match in EMAIL_RE.finditer(decoded)}


def contact_links(body: str, page_url: str, site_origin: str) -> set[str]:
    parser = LinkParser()
    parser.feed(body)
    links: set[str] = set()
    site_netloc = urlsplit(site_origin).netloc.lower()
    parsed_links = parser.links + [(href, label) for label, href in MARKDOWN_LINK_RE.findall(body)]

    for href, label in parsed_links:
        candidate = urljoin(page_url, html.unescape(href))
        parts = urlsplit(candidate)
        searchable = " ".join((unquote(parts.path).replace("-", " ").replace("_", " "), label))
        if (
            parts.scheme in {"http", "https"}
            and parts.netloc.lower() == site_netloc
            and not any(parts.path.lower().endswith(suffix) for suffix in NON_PAGE_SUFFIXES)
            and CONTACT_HINT_RE.search(searchable)
        ):
            links.add(urlunsplit((parts.scheme, parts.netloc, parts.path, parts.query, "")))
    return links


def scrape(start_url: str, verbose: bool = False) -> tuple[dict[str, set[str]], list[str]]:
    start_url = normalize_url(start_url)
    found: dict[str, set[str]] = defaultdict(set)
    errors: list[str] = []

    client = NotteClient()
    with client.Session() as session:
        if verbose:
            print(f"Fetching {start_url}", file=sys.stderr)
        try:
            final_url, body = scrape_page(session, start_url)
        except Exception as exc:
            return {}, [f"{start_url}: {exc}"]

        for email in extract_emails(body):
            found[email].add(final_url)

        # Inspect the homepage before guessing paths. Fall back only when it does not
        # expose a link that looks relevant.
        site_origin = origin(final_url)
        links = contact_links(body, final_url, site_origin)
        candidates = sorted(links) if links else [f"{site_origin}{path}" for path in FALLBACK_PATHS]

        for url in candidates:
            if url == final_url:
                continue
            if verbose:
                print(f"Fetching {url}", file=sys.stderr)
            try:
                contact_url, contact_body = scrape_page(session, url)
            except Exception as exc:
                errors.append(f"{url}: {exc}")
                continue
            for email in extract_emails(contact_body):
                found[email].add(contact_url)

    return dict(found), errors


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Find emails on a page and its likely contact pages.")
    parser.add_argument("url", help="Website URL, e.g. https://www.vivekanandahospital.com/")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show fetched pages and skipped-page errors")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        emails, errors = scrape(args.url, verbose=args.verbose)
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.json:
        result = {email: sorted(pages) for email, pages in sorted(emails.items())}
        print(json.dumps(result, indent=2))
    elif emails:
        for email in sorted(emails):
            print(email)
    else:
        print("No email addresses found.", file=sys.stderr)

    if args.verbose:
        for error in errors:
            print(f"Skipped {error}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
