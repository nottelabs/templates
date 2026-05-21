# Notte: Data.gov Dataset Finder - See README.md for full documentation
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "notte-sdk",
#     "pydantic",
#     "python-dotenv",
# ]
# ///

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from urllib.parse import quote_plus, urljoin

from dotenv import load_dotenv
from notte_sdk import NotteClient
from pydantic import BaseModel, Field

load_dotenv(Path(__file__).with_name(".env"))

DEFAULT_QUERY = os.environ.get("DATA_GOV_QUERY", "climate")
DEFAULT_RESULT_LIMIT = int(os.environ.get("DATA_GOV_RESULT_LIMIT", "5"))
DATA_GOV_BASE_URL = "https://catalog.data.gov"


class DatasetSearchResult(BaseModel):
    rank: int | None = Field(None, description="Visible rank on the search results page.")
    title: str | None = Field(None, description="Dataset title.")
    url: str | None = Field(None, description="Dataset detail URL, absolute or relative.")
    organization: str | None = Field(None, description="Publishing organization.")
    last_updated_date: str | None = Field(None, description="Visible last updated date.")
    description_summary: str | None = Field(None, description="Short result-card description.")
    formats: list[str] = Field(default_factory=list, description="Visible file/API formats.")
    relevance_text: str | None = Field(None, description="Visible search relevance score.")
    views_text: str | None = Field(None, description="Visible monthly views count.")


class SearchResults(BaseModel):
    search_query: str | None = None
    result_count_text: str | None = None
    current_url: str | None = None
    sort_option: str | None = None
    datasets: list[DatasetSearchResult] = Field(default_factory=list)


class DatasetResource(BaseModel):
    name: str | None = None
    format: str | None = None
    url: str | None = None


class DatasetDetail(BaseModel):
    title: str | None = None
    organization: str | None = None
    description: str | None = None
    last_updated: str | None = None
    homepage_source_link: str | None = None
    license: str | None = None
    metadata_fields: dict[str, object] | None = None
    resources: list[DatasetResource] | None = None


class DatasetFinding(BaseModel):
    search_result: DatasetSearchResult
    detail: DatasetDetail | None = None
    detail_error: str | None = None


class DatasetFinderReport(BaseModel):
    query: str
    limit: int
    search_url: str
    result_count_text: str | None = None
    sort_option: str | None = None
    findings: list[DatasetFinding] = Field(default_factory=list)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Find public datasets on Data.gov with Notte.")
    parser.add_argument(
        "--query",
        default=DEFAULT_QUERY,
        help=f"Search query to run on Data.gov (default: {DEFAULT_QUERY!r}).",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=DEFAULT_RESULT_LIMIT,
        help=f"Number of top results to enrich with detail pages (default: {DEFAULT_RESULT_LIMIT}).",
    )
    return parser.parse_args()


def data_gov_search_url(query: str) -> str:
    clean_query = query.strip()
    if not clean_query:
        raise ValueError("Search query cannot be empty.")
    return f"{DATA_GOV_BASE_URL}/?q={quote_plus(clean_query)}"


def absolute_data_gov_url(url: str | None) -> str | None:
    if not url:
        return None
    return urljoin(DATA_GOV_BASE_URL, url)


def print_viewer_url(session) -> None:
    viewer_url = getattr(session, "viewer_url", None)
    if not viewer_url:
        viewer_url = getattr(session.status(), "viewer_url", None)
    if viewer_url:
        print(f"Live View: {viewer_url}")


def scrape_search_results(session, query: str, limit: int) -> SearchResults:
    search_url = data_gov_search_url(query)
    print(f"Opening Data.gov search: {search_url}")
    session.execute(type="goto", url=search_url)
    session.execute(type="wait", time_ms=1500)

    return session.scrape(
        instructions=(
            f"Extract the top {limit} Data.gov dataset search results for query {query!r}. "
            "Return search_query, result_count_text, current_url, sort_option, and datasets. "
            "For each dataset include rank, title, URL, organization, last updated date, "
            "description summary, visible formats, search relevance, and views last month. "
            f"Return no more than {limit} datasets."
        ),
        only_main_content=True,
        only_images=False,
        scrape_links=True,
        scrape_images=False,
        response_format=SearchResults,
    )


def scrape_dataset_detail(session, dataset_url: str) -> DatasetDetail:
    print(f"Opening dataset detail: {dataset_url}")
    session.execute(type="goto", url=dataset_url)
    session.execute(type="wait", time_ms=1000)

    return session.scrape(
        instructions=(
            "Extract this Data.gov dataset detail page as JSON. Include title, organization, "
            "description, last updated date, homepage/source link, license, any visible metadata "
            "fields, and available resources/distributions with name, format, and URL."
        ),
        only_main_content=True,
        only_images=False,
        scrape_links=True,
        scrape_images=False,
        response_format=DatasetDetail,
    )


def find_datasets(query: str, limit: int) -> DatasetFinderReport:
    if limit < 1:
        raise ValueError("Limit must be at least 1.")
    limit = min(limit, 20)

    api_key = os.environ.get("NOTTE_API_KEY")
    if not api_key:
        raise RuntimeError("Missing NOTTE_API_KEY. Set it in your environment or .env file.")

    client = NotteClient(api_key=api_key)
    search_url = data_gov_search_url(query)

    with client.Session(open_viewer=True, idle_timeout_minutes=5, use_file_storage=True) as session:
        print(f"Session ID: {session.session_id}")
        print_viewer_url(session)

        search_results = scrape_search_results(session, query, limit)
        findings: list[DatasetFinding] = []

        for result in search_results.datasets[:limit]:
            detail_url = absolute_data_gov_url(result.url)
            result.url = detail_url
            detail = None
            detail_error = None
            if detail_url:
                try:
                    detail = scrape_dataset_detail(session, detail_url)
                except Exception as error:
                    detail_error = str(error)
                    print(f"Skipping detail extraction for {detail_url}: {error}")
            findings.append(DatasetFinding(search_result=result, detail=detail, detail_error=detail_error))

    return DatasetFinderReport(
        query=query,
        limit=limit,
        search_url=search_url,
        result_count_text=search_results.result_count_text,
        sort_option=search_results.sort_option,
        findings=findings,
    )


def main() -> None:
    args = parse_args()
    report = find_datasets(query=args.query, limit=args.limit)
    print(json.dumps(report.model_dump(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except Exception as err:
        print(f"Error finding Data.gov datasets: {err}")
        print("Common fixes:")
        print("  - Set NOTTE_API_KEY in your environment or .env file")
        print("  - Try a simpler query, for example: uv run main.py --query climate --limit 3")
        print("  - Keep --limit small if you only need the top matches")
        raise SystemExit(1)
