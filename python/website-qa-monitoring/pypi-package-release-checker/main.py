# Notte: PyPI Package Release Checker - See README.md for full documentation
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "notte-sdk[playwright]",
#     "packaging",
#     "pydantic",
#     "python-dotenv",
# ]
# ///

import argparse
import json
import os
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import quote

from dotenv import load_dotenv
from notte_sdk import NotteClient
from packaging.version import InvalidVersion, Version
from pydantic import BaseModel, Field

load_dotenv(Path(__file__).with_name(".env"))

DEFAULT_PACKAGE_NAME = os.environ.get("PACKAGE_NAME", "requests")
KNOWN_VERSION = os.environ.get("KNOWN_VERSION")
USE_PROXY = os.environ.get("USE_PROXY", "true").lower() not in {"0", "false", "no"}


class ReleaseFile(BaseModel):
    filename: str
    package_type: str | None = None
    python_version: str | None = None
    size: int | None = None
    upload_time_iso_8601: str | None = None
    requires_python: str | None = None


class PackageReleaseReport(BaseModel):
    package_name: str
    project_url: str
    api_url: str
    summary: str | None = None
    latest_version: str
    latest_release_date: str | None = None
    requires_python: str | None = None
    license: str | None = None
    project_urls: dict[str, str] = Field(default_factory=dict)
    release_files: list[ReleaseFile] = Field(default_factory=list)
    known_version: str | None = None
    is_newer_than_known: bool | None = None


def print_viewer_url(session) -> None:
    viewer_url = getattr(session, "viewer_url", None)
    if not viewer_url:
        viewer_url = getattr(session.status(), "viewer_url", None)
    if viewer_url:
        print(f"Live View Link: {viewer_url}")


def normalized_package_path(package_name: str) -> str:
    package_name = package_name.strip()
    if not package_name:
        raise ValueError("Package name cannot be empty")
    return quote(package_name, safe="")


def wait_for_project_page(session) -> None:
    page = getattr(session, "page", None)
    if page is None:
        session.execute(type="wait", time_ms=1000)
        return

    page.wait_for_load_state("domcontentloaded", timeout=30000)
    page.wait_for_selector("h1", state="visible", timeout=15000)


def fetch_package_json_in_browser(session, api_url: str) -> dict:
    page = getattr(session, "page", None)
    if page is None:
        raise RuntimeError("PyPI release checker requires session.page")

    return page.evaluate(
        """async url => {
            const response = await fetch(url, {
              headers: { "Accept": "application/json" }
            });
            if (!response.ok) {
              throw new Error(`PyPI JSON request failed with ${response.status}`);
            }
            return await response.json();
        }""",
        api_url,
    )


def release_datetime(files: list[dict]) -> str | None:
    timestamps = [
        file.get("upload_time_iso_8601")
        for file in files
        if file.get("upload_time_iso_8601")
    ]
    if not timestamps:
        return None
    return min(timestamps)


def is_newer_version(latest_version: str, known_version: str | None) -> bool | None:
    if not known_version:
        return None
    try:
        return Version(latest_version) > Version(known_version)
    except InvalidVersion:
        return latest_version != known_version


def build_report(payload: dict, package_name: str, project_url: str, api_url: str) -> PackageReleaseReport:
    info = payload["info"]
    latest_version = info["version"]
    latest_files = payload.get("releases", {}).get(latest_version) or payload.get("urls", [])
    release_files = [ReleaseFile.model_validate(file) for file in latest_files]

    return PackageReleaseReport(
        package_name=info.get("name") or package_name,
        project_url=project_url,
        api_url=api_url,
        summary=info.get("summary"),
        latest_version=latest_version,
        latest_release_date=release_datetime(latest_files),
        requires_python=info.get("requires_python") or next(
            (file.requires_python for file in release_files if file.requires_python),
            None,
        ),
        license=info.get("license") or None,
        project_urls=info.get("project_urls") or {},
        release_files=release_files,
        known_version=KNOWN_VERSION,
        is_newer_than_known=is_newer_version(latest_version, KNOWN_VERSION),
    )


def check_package_release(package_name: str) -> PackageReleaseReport:
    package_path = normalized_package_path(package_name)
    project_url = f"https://pypi.org/project/{package_path}/"
    api_url = f"https://pypi.org/pypi/{package_path}/json"

    api_key = os.environ.get("NOTTE_API_KEY")
    if not api_key:
        raise RuntimeError("Missing NOTTE_API_KEY. Set it in your environment or .env file.")

    client = NotteClient(api_key=api_key)

    with client.Session(
        open_viewer=True,
        idle_timeout_minutes=2,
        proxies=USE_PROXY,
        use_file_storage=True,
    ) as session:
        print("Notte session initialized successfully")
        print(f"Session ID: {session.session_id}")
        print_viewer_url(session)

        print(f"Opening PyPI project page: {project_url}")
        session.execute(type="goto", url=project_url)
        wait_for_project_page(session)

        print(f"Fetching release metadata in the browser context: {api_url}")
        payload = fetch_package_json_in_browser(session, api_url)

    return build_report(payload, package_name, project_url, api_url)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check the latest release for a PyPI package with Notte.")
    parser.add_argument(
        "package",
        nargs="?",
        default=DEFAULT_PACKAGE_NAME,
        help=f"PyPI package name to check (default: {DEFAULT_PACKAGE_NAME})",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    started_at = datetime.now(UTC).isoformat()
    print(f"Starting PyPI release check at {started_at}")

    report = check_package_release(args.package)

    print("\nLatest release:")
    print(json.dumps(report.model_dump(), indent=2))

    if report.known_version:
        status = "new release available" if report.is_newer_than_known else "no newer release found"
        print(f"\nCompared with KNOWN_VERSION={report.known_version}: {status}")


if __name__ == "__main__":
    try:
        main()
    except Exception as err:
        print(f"Error in PyPI release checker: {err}")
        print("Common issues:")
        print("  - Check .env has NOTTE_API_KEY")
        print("  - Verify PACKAGE_NAME exists on PyPI")
        print("  - Keep USE_PROXY=true if PyPI blocks direct browser traffic")
        print("Docs: https://docs.notte.cc/")
        raise SystemExit(1)
