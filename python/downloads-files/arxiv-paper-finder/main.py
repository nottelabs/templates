# Notte: arXiv Paper Finder - See README.md for full documentation
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
import re
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from notte_sdk import NotteClient
from pydantic import BaseModel, Field

load_dotenv(Path(__file__).with_name(".env"))

ARXIV_HOME_URL = "https://arxiv.org/"
DEFAULT_SEARCH_QUERY = os.environ.get("SEARCH_QUERY", "openai")
DEFAULT_RESULT_LIMIT = int(os.environ.get("RESULT_LIMIT", "5"))
DEFAULT_RESULT_INDEX = int(os.environ.get("RESULT_INDEX", "1"))
DEFAULT_DOWNLOAD_DIR = os.environ.get("DOWNLOAD_DIR", "./downloads/arxiv")
USE_PROXY = os.environ.get("USE_PROXY", "false").lower() in {"1", "true", "yes"}
FORCE_DOWNLOAD = os.environ.get("FORCE_DOWNLOAD", "true").lower() in {"1", "true", "yes"}

SEARCH_RESULT_JS = """
(resultIndex) => {
  const resultItems = Array.from(document.querySelectorAll("li.arxiv-result"));
  const absLinks = Array.from(document.querySelectorAll("a[href*='/abs/']"));
  const item = resultItems[resultIndex] || absLinks[resultIndex]?.closest("li.arxiv-result");
  const abs = item?.querySelector("p.list-title a[href*='/abs/'], a[href*='/abs/']");
  if (!abs || !item) {
    return {
      url: location.href,
      error: "selected result not found",
      available_results: resultItems.length || absLinks.length
    };
  }

  const pdf = item.querySelector("a[href*='/pdf/']");
  const abstractUrl = new URL(abs.getAttribute("href"), location.href).href;
  const arxivId =
    abstractUrl.match(/\\/abs\\/([^?#]+)/)?.[1] ||
    abs.textContent.replace(/^\\s*arXiv:\\s*/i, "").trim() ||
    null;
  const title = item.querySelector("p.title")?.textContent?.replace(/\\s+/g, " ").trim() || null;
  const abstractSnippet = item.querySelector("span.abstract-full")?.textContent
    ?.replace(/\\s*△ Less\\s*$/, "")
    ?.replace(/\\s+/g, " ")
    ?.trim() || null;

  return {
    url: location.href,
    available_results: resultItems.length || absLinks.length,
    result_count_text: document.querySelector("h1.title")?.textContent.replace(/\\s+/g, " ").trim() || null,
    title,
    authors: Array.from(item.querySelectorAll("p.authors a")).map((a) => a.textContent.trim()),
    arxiv_id: arxivId,
    abstract_url: abstractUrl,
    pdf_url: pdf ? new URL(pdf.getAttribute("href"), location.href).href : abstractUrl.replace("/abs/", "/pdf/"),
    submitted_date: item.querySelector("p.is-size-7")?.textContent?.replace(/\\s+/g, " ").trim() || null,
    subjects: Array.from(item.querySelectorAll(".tag")).map((tag) => tag.textContent.trim()),
    abstract_snippet: abstractSnippet
  };
}
"""

ARTICLE_DETAILS_JS = """
() => {
  const pdf = document.querySelector("a[href*='/pdf/']");
  const abstract = document.querySelector("blockquote.abstract")?.textContent
    ?.replace(/^\\s*Abstract:\\s*/, "")
    ?.replace(/\\s+/g, " ")
    ?.trim() || null;

  return {
    url: location.href,
    title: document.querySelector("h1.title")?.textContent
      ?.replace(/^\\s*Title:\\s*/, "")
      ?.replace(/\\s+/g, " ")
      ?.trim() || null,
    authors: Array.from(document.querySelectorAll(".authors a")).map((a) => a.textContent.trim()),
    arxiv_id: location.pathname.split("/").pop(),
    abstract_url: location.href,
    pdf_url: pdf ? new URL(pdf.getAttribute("href"), location.href).href : null,
    submitted_date: document.querySelector(".dateline")?.textContent?.replace(/\\s+/g, " ").trim() || null,
    subjects: Array.from(document.querySelectorAll(".subjects .primary-subject, .subjects a"))
      .map((subject) => subject.textContent.trim()),
    abstract
  };
}
"""


class PaperResult(BaseModel):
    title: str | None = Field(None, description="Paper title.")
    authors: list[str] = Field(default_factory=list, description="Paper authors.")
    arxiv_id: str | None = Field(None, description="arXiv identifier, for example 2605.07507.")
    abstract_url: str | None = Field(None, description="Link to the abstract page.")
    pdf_url: str | None = Field(None, description="Link to the PDF.")
    submitted_date: str | None = Field(None, description="Submission date shown in search results.")
    subjects: list[str] = Field(default_factory=list, description="arXiv subject tags.")
    abstract_snippet: str | None = Field(None, description="Short visible abstract snippet.")


class ArxivSearchReport(BaseModel):
    query: str = Field("", description="Search query that was submitted.")
    result_limit: int = Field(0, description="Maximum number of results requested.")
    result_count_text: str | None = Field(None, description="Visible search result count text.")
    results: list[PaperResult] = Field(default_factory=list, description="Extracted paper results.")


class ArticleDetails(BaseModel):
    title: str | None = Field(None, description="Paper title from the arXiv article page.")
    authors: list[str] = Field(
        default_factory=list, description="Paper authors from the arXiv article page."
    )
    arxiv_id: str | None = Field(None, description="arXiv identifier.")
    abstract_url: str | None = Field(None, description="Current abstract page URL.")
    pdf_url: str | None = Field(None, description="PDF URL from the article page.")
    submitted_date: str | None = Field(None, description="Submission date.")
    subjects: list[str] = Field(default_factory=list, description="arXiv subject tags.")
    abstract: str | None = Field(None, description="Full visible abstract text.")


class LocalDownload(BaseModel):
    storage_name: str = Field(..., description="Filename in Notte file storage.")
    local_path: str = Field(..., description="Local path where the file was downloaded.")
    downloaded: bool = Field(..., description="Whether storage.download reported success.")


class ArxivDownloadReport(BaseModel):
    query: str = Field("", description="Search query that was submitted.")
    result_limit: int = Field(0, description="Maximum number of results requested.")
    result_index: int = Field(1, description="1-based search result index selected for download.")
    result_count_text: str | None = Field(None, description="Visible search result count text.")
    selected_result: PaperResult | None = Field(None, description="Selected search result.")
    article: ArticleDetails | None = Field(
        None, description="Metadata extracted from the article page."
    )
    downloaded_files: list[LocalDownload] = Field(
        default_factory=list,
        description="Files downloaded from Notte storage into the local download directory.",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Find an arXiv paper and download its PDF with Notte file storage."
    )
    parser.add_argument(
        "query",
        nargs="?",
        default=DEFAULT_SEARCH_QUERY,
        help="Search query. Defaults to SEARCH_QUERY or 'openai'.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=DEFAULT_RESULT_LIMIT,
        help="Number of search results to extract, from 1 to 50. Defaults to RESULT_LIMIT or 5.",
    )
    parser.add_argument(
        "--result-index",
        type=int,
        default=DEFAULT_RESULT_INDEX,
        help="1-based result index to open and download. Defaults to RESULT_INDEX or 1.",
    )
    parser.add_argument(
        "--download-dir",
        default=DEFAULT_DOWNLOAD_DIR,
        help="Local directory for files retrieved from Notte storage. Defaults to DOWNLOAD_DIR or ./downloads/arxiv.",
    )
    return parser.parse_args()


def validate_limit(limit: int) -> int:
    if limit < 1:
        raise ValueError("result limit must be at least 1")
    if limit > 50:
        raise ValueError("result limit cannot exceed the first arXiv results page size of 50")
    return limit


def validate_result_index(result_index: int, result_limit: int) -> int:
    if result_index < 1:
        raise ValueError("result index must be at least 1")
    if result_index > result_limit:
        raise ValueError("result index cannot be greater than the result limit")
    return result_index


def print_viewer_url(session) -> None:
    viewer_url = getattr(session, "viewer_url", None)
    if not viewer_url:
        viewer_url = getattr(session.status(), "viewer_url", None)
    if viewer_url:
        print(f"Live view: {viewer_url}")


def json_from_execution_result(result) -> dict[str, Any]:
    candidates: list[Any] = [getattr(result, "data", None), getattr(result, "message", None)]
    data = getattr(result, "data", None)
    if data is not None:
        candidates.extend(
            [
                getattr(data, "structured", None),
                getattr(data, "markdown", None),
            ]
        )

    for candidate in candidates:
        parsed = coerce_json_dict(candidate)
        if parsed is not None:
            return parsed

    raise RuntimeError(f"Could not parse evaluate_js result: {result}")


def coerce_json_dict(candidate: Any) -> dict[str, Any] | None:
    if candidate is None:
        return None
    if hasattr(candidate, "model_dump"):
        candidate = candidate.model_dump()
    if isinstance(candidate, str):
        parsed = parse_json_object(candidate)
        return coerce_json_dict(parsed) if parsed is not None else None
    if not isinstance(candidate, dict):
        return None

    for key in ("result", "value", "output", "data", "structured", "json", "markdown", "message"):
        nested = candidate.get(key)
        parsed = coerce_json_dict(nested)
        if parsed is not None:
            return parsed

    return candidate


def parse_json_object(text: str) -> dict[str, Any] | None:
    stripped = text.strip()
    if not stripped:
        return None
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json)?", "", stripped).removesuffix("```").strip()

    for candidate in (stripped, first_json_object(stripped)):
        if not candidate:
            continue
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            return parsed
    return None


def first_json_object(text: str) -> str | None:
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    return text[start : end + 1]


def evaluate_json(session, code: str, *args: Any) -> dict[str, Any]:
    if args:
        serialized_args = ", ".join(json.dumps(arg) for arg in args)
        code = f"({code})({serialized_args})"
    result = session.execute(type="evaluate_js", code=code)
    data = json_from_execution_result(result)
    if data.get("error"):
        raise RuntimeError(f"{data['error']} on {data.get('url')}")
    return data


def extract_search_result(session, result_index: int) -> tuple[str | None, PaperResult]:
    data = evaluate_json(session, SEARCH_RESULT_JS, result_index - 1)
    selected = PaperResult(
        title=data.get("title"),
        authors=data.get("authors") or [],
        arxiv_id=data.get("arxiv_id"),
        abstract_url=data.get("abstract_url"),
        pdf_url=data.get("pdf_url"),
        submitted_date=data.get("submitted_date"),
        subjects=data.get("subjects") or [],
        abstract_snippet=data.get("abstract_snippet"),
    )
    return data.get("result_count_text"), selected


def extract_article_details(session, selected_result: PaperResult) -> ArticleDetails:
    data = evaluate_json(session, ARTICLE_DETAILS_JS)
    return ArticleDetails(
        title=data.get("title") or selected_result.title,
        authors=data.get("authors") or selected_result.authors,
        arxiv_id=data.get("arxiv_id") or selected_result.arxiv_id,
        abstract_url=data.get("abstract_url") or selected_result.abstract_url,
        pdf_url=data.get("pdf_url") or selected_result.pdf_url,
        submitted_date=data.get("submitted_date") or selected_result.submitted_date,
        subjects=data.get("subjects") or selected_result.subjects,
        abstract=data.get("abstract") or selected_result.abstract_snippet,
    )


def storage_file_name(file_info) -> str:
    return str(getattr(file_info, "name", file_info))


def download_storage_files(storage, download_dir: str) -> list[LocalDownload]:
    local_dir = Path(download_dir)
    local_dir.mkdir(parents=True, exist_ok=True)

    local_downloads: list[LocalDownload] = []
    for file_info in storage.list_downloaded_files():
        file_name = storage_file_name(file_info)
        downloaded = storage.download(
            file_name=file_name, local_dir=str(local_dir), force=FORCE_DOWNLOAD
        )
        local_downloads.append(
            LocalDownload(
                storage_name=file_name,
                local_path=str((local_dir / file_name).resolve()),
                downloaded=downloaded,
            )
        )
    return local_downloads


def selected_abstract_url(selected_result: PaperResult) -> str:
    if selected_result.abstract_url:
        return selected_result.abstract_url
    if selected_result.arxiv_id:
        return f"https://arxiv.org/abs/{selected_result.arxiv_id}"
    raise RuntimeError("selected result did not include an abstract URL or arXiv ID")


def find_and_download_paper(
    query: str = DEFAULT_SEARCH_QUERY,
    result_limit: int = DEFAULT_RESULT_LIMIT,
    result_index: int = DEFAULT_RESULT_INDEX,
    download_dir: str = DEFAULT_DOWNLOAD_DIR,
) -> ArxivDownloadReport:
    query = query.strip()
    if not query:
        raise ValueError("search query cannot be empty")
    result_limit = validate_limit(result_limit)
    result_index = validate_result_index(result_index, result_limit)

    api_key = os.environ.get("NOTTE_API_KEY")
    client = NotteClient(api_key=api_key) if api_key else NotteClient()
    storage = client.FileStorage()
    report = ArxivDownloadReport(query=query, result_limit=result_limit, result_index=result_index)

    with client.Session(
        open_viewer=True,
        idle_timeout_minutes=3,
        proxies=USE_PROXY,
        storage=storage,
    ) as session:
        print(f"Session ID: {session.session_id}")
        print_viewer_url(session)
        print(f"Searching arXiv for: {query}")

        session.execute(type="goto", url=ARXIV_HOME_URL)
        session.execute(type="click", selector='internal:role=link[name="Advanced Search"i]')
        session.execute(
            type="fill",
            selector='internal:role=textbox[name="Search term"s]',
            value=query,
        )
        session.execute(
            type="click",
            selector='#terms-fieldset >> internal:role=button[name="Search"i]',
        )
        session.execute(type="wait", time_ms=3000)

        result_count_text, selected_result = extract_search_result(session, result_index)
        report.result_count_text = result_count_text
        report.selected_result = selected_result

        abstract_url = selected_abstract_url(selected_result)
        print(f"Opening result {result_index}: {abstract_url}")
        session.execute(type="goto", url=abstract_url)
        session.execute(type="wait", time_ms=1000)

        report.article = extract_article_details(session, selected_result)
        pdf_url = report.article.pdf_url or selected_result.pdf_url
        if not pdf_url:
            raise RuntimeError("selected article did not include a PDF URL")

        print(f"Opening PDF: {pdf_url}")
        session.execute(type="goto", url=pdf_url)
        session.execute(type="wait", time_ms=1000)

        print("Downloading the raw PDF page into Notte file storage...")
        session.execute(type="download_file", selector="html")
        session.execute(type="wait", time_ms=1000)

    report.downloaded_files = download_storage_files(storage, download_dir)
    if not report.downloaded_files:
        raise RuntimeError("No files were downloaded into Notte file storage")

    return report


def main() -> None:
    args = parse_args()
    report = find_and_download_paper(args.query, args.limit, args.result_index, args.download_dir)
    print(json.dumps(report.model_dump(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except Exception as err:
        print(f"Error downloading an arXiv paper: {err}")
        print("Common fixes:")
        print("  - Set NOTTE_API_KEY in your environment or .env file")
        print('  - Try a narrower query, for example: uv run main.py "openai" --limit 5')
        print(
            "  - Use --result-index to choose a different result if the selected paper has no PDF link"
        )
        print("  - Set USE_PROXY=true if arXiv rejects direct browser traffic")
        raise SystemExit(1)
