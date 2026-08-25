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
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from notte_sdk import NotteClient
from pydantic import BaseModel, Field

load_dotenv(Path(__file__).with_name(".env"))

ARXIV_HOME_URL = "https://arxiv.org/"
ARXIV_AI_LINK_SELECTOR = 'internal:role=link[name="Computing Research Repository Artificial Intelligence"i]'
DEFAULT_CATEGORY = "cs.AI"
DEFAULT_RESULT_INDEX = int(os.environ.get("RESULT_INDEX", "1"))
DEFAULT_DOWNLOAD_DIR = os.environ.get("DOWNLOAD_DIR", "./downloads/arxiv")
FORCE_DOWNLOAD = os.environ.get("FORCE_DOWNLOAD", "true").lower() in {"1", "true", "yes"}

RECENT_LIST_RESULT_JS = """
(resultIndex) => {
  const terms = Array.from(document.querySelectorAll("dl dt"));
  const term = terms[resultIndex];
  const details = term?.nextElementSibling?.matches("dd") ? term.nextElementSibling : null;
  const abs = term?.querySelector("a[href*='/abs/']");
  if (!abs || !term || !details) {
    return {
      url: location.href,
      error: "selected result not found",
      available_results: terms.length
    };
  }

  const pdf = term.querySelector("a[href*='/pdf/']");
  const abstractUrl = new URL(abs.getAttribute("href"), location.href).href;
  const arxivId =
    abstractUrl.match(/\\/abs\\/([^?#]+)/)?.[1] ||
    abs.textContent.replace(/^\\s*arXiv:\\s*/i, "").trim() ||
    null;
  const cleanPrefixed = (selector, prefixPattern) => details.querySelector(selector)?.textContent
    ?.replace(prefixPattern, "")
    ?.replace(/\\s+/g, " ")
    ?.trim() || null;

  return {
    url: location.href,
    available_results: terms.length,
    result_count_text: document.querySelector("h3")?.textContent.replace(/\\s+/g, " ").trim() || null,
    title: cleanPrefixed(".list-title", /^\\s*Title:\\s*/i),
    authors: Array.from(details.querySelectorAll(".list-authors a")).map((a) => a.textContent.trim()),
    arxiv_id: arxivId,
    abstract_url: abstractUrl,
    pdf_url: pdf ? new URL(pdf.getAttribute("href"), location.href).href : abstractUrl.replace("/abs/", "/pdf/"),
    submitted_date: document.querySelector("h3")?.textContent.replace(/\\s+/g, " ").trim() || null,
    subjects: (cleanPrefixed(".list-subjects", /^\\s*Subjects?:\\s*/i) || "")
      .split(";")
      .map((subject) => subject.trim())
      .filter(Boolean),
    abstract_snippet: cleanPrefixed(".list-comments", /^\\s*Comments?:\\s*/i)
  };
}
"""

OPEN_RECENT_ARTICLE_JS = """
(resultIndex) => {
  const links = Array.from(document.querySelectorAll("a[href*='/abs/']"));
  const first = links[resultIndex];
  if (!first) {
    return {
      ok: false,
      url: location.href,
      error: "No abstract links found",
      available_results: links.length
    };
  }

  const href = new URL(first.getAttribute("href"), location.href).href;
  first.click();
  return { ok: true, href, text: first.textContent.trim() };
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
    submitted_date: str | None = Field(None, description="Submission date shown in recent results.")
    subjects: list[str] = Field(default_factory=list, description="arXiv subject tags.")
    abstract_snippet: str | None = Field(None, description="Short visible abstract snippet.")


class ArxivSearchReport(BaseModel):
    category: str = Field(DEFAULT_CATEGORY, description="arXiv category that was opened.")
    result_count_text: str | None = Field(None, description="Visible recent-submissions count text.")
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
    category: str = Field(DEFAULT_CATEGORY, description="arXiv category that was opened.")
    result_index: int = Field(1, description="1-based recent article index selected for download.")
    result_count_text: str | None = Field(None, description="Visible recent-submissions count text.")
    selected_result: PaperResult | None = Field(None, description="Selected recent result.")
    article: ArticleDetails | None = Field(
        None, description="Metadata extracted from the article page."
    )
    downloaded_files: list[LocalDownload] = Field(
        default_factory=list,
        description="Files downloaded from Notte storage into the local download directory.",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Open arXiv's AI recent submissions and download a selected paper PDF."
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


def validate_result_index(result_index: int) -> int:
    if result_index < 1:
        raise ValueError("result index must be at least 1")
    return result_index


def print_viewer_url(session) -> None:
    viewer_url = getattr(session, "viewer_url", None)
    if not viewer_url:
        viewer_url = getattr(session.status(), "viewer_url", None)
    if viewer_url:
        print(f"Live view: {viewer_url}")


def evaluate_json(session, code: str, *args: Any) -> dict[str, Any]:
    if args:
        serialized_args = ", ".join(json.dumps(arg) for arg in args)
        code = f"({code})({serialized_args})"
    # evaluate_js returns the evaluated value as a string, objects as JSON
    raw = session.evaluate_js(code)
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"evaluate_js did not return JSON: {raw[:200]}") from exc
    if not isinstance(data, dict):
        raise RuntimeError(f"evaluate_js returned {type(data).__name__}, expected an object: {raw[:200]}")
    if data.get("error"):
        raise RuntimeError(f"{data['error']} on {data.get('url')}")
    return data


def extract_recent_list_result(session, result_index: int) -> tuple[str | None, PaperResult]:
    data = evaluate_json(session, RECENT_LIST_RESULT_JS, result_index - 1)
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


def open_recent_article(session, result_index: int) -> None:
    data = evaluate_json(session, OPEN_RECENT_ARTICLE_JS, result_index - 1)
    if not data.get("ok"):
        raise RuntimeError(f"{data.get('error', 'could not open recent article')} on {data.get('url')}")


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
    result_index: int = DEFAULT_RESULT_INDEX,
    download_dir: str = DEFAULT_DOWNLOAD_DIR,
) -> ArxivDownloadReport:
    result_index = validate_result_index(result_index)

    api_key = os.environ.get("NOTTE_API_KEY")
    client = NotteClient(api_key=api_key) if api_key else NotteClient()
    storage = client.FileStorage()
    report = ArxivDownloadReport(result_index=result_index)

    with client.Session(
        open_viewer=True,
        idle_timeout_minutes=3,
        proxies=True,
        storage=storage,
    ) as session:
        print(f"Session ID: {session.session_id}")
        print_viewer_url(session)
        print("Opening arXiv Computing Research Repository Artificial Intelligence...")

        session.execute(type="goto", url=ARXIV_HOME_URL)
        session.execute(type="click", selector=ARXIV_AI_LINK_SELECTOR)
        session.execute(type="wait", time_ms=1000)

        result_count_text, selected_result = extract_recent_list_result(session, result_index)
        report.result_count_text = result_count_text
        report.selected_result = selected_result

        print(f"Opening recent article {result_index}: {selected_abstract_url(selected_result)}")
        open_recent_article(session, result_index)
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
    report = find_and_download_paper(args.result_index, args.download_dir)
    print(json.dumps(report.model_dump(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except Exception as err:
        print(f"Error downloading an arXiv paper: {err}")
        print("Common fixes:")
        print("  - Set NOTTE_API_KEY in your environment or .env file")
        print(
            "  - Use --result-index to choose a different recent article if the selected paper has no PDF link"
        )
        print("  - Set USE_PROXY=true if arXiv rejects direct browser traffic")
        raise SystemExit(1)
