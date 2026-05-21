# Notte: Daily Release Monitor Function - See README.md for full documentation
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "notte-sdk",
#     "pydantic",
#     "python-dotenv",
# ]
# ///

from __future__ import annotations

import json
import os
from pathlib import Path
from urllib.parse import quote, urlparse

from dotenv import load_dotenv
from notte_sdk import NotteClient
from pydantic import BaseModel, Field

load_dotenv(Path(__file__).with_name(".env"))

DEFAULT_TARGET = "https://github.com/nottelabs/notte"


class ReleaseInfo(BaseModel):
    name: str | None = Field(None, description="Project, repo, or package name")
    version: str | None = Field(None, description="Latest visible release, tag, or package version")
    published_at: str | None = Field(None, description="Visible publish or release date")
    url: str | None = Field(None, description="URL for the release or package page")
    summary: str | None = Field(None, description="Short release summary")
    notes: list[str] = Field(default_factory=list, description="Important release notes or visible changes")


class MonitorResult(BaseModel):
    target: str
    target_type: str
    latest: ReleaseInfo
    previous_version: str | None = None
    has_new_release: bool | None = None


def normalize_github_repo(target: str) -> str:
    parsed = urlparse(target.strip())
    if parsed.netloc != "github.com":
        raise ValueError("GitHub targets must point to github.com.")

    parts = [part for part in parsed.path.split("/") if part]
    if len(parts) < 2:
        raise ValueError("GitHub targets must include an owner and repository name.")

    return f"https://github.com/{parts[0]}/{parts[1]}"


def normalize_npm_package(target: str) -> tuple[str, str]:
    target = target.strip()
    if target.startswith("npm:"):
        package_name = target.removeprefix("npm:").strip()
    else:
        parsed = urlparse(target)
        if parsed.netloc == "www.npmjs.com":
            package_name = parsed.path.removeprefix("/package/").strip("/")
        else:
            package_name = target

    if not package_name:
        raise ValueError("npm target must include a package name.")

    package_url = f"https://www.npmjs.com/package/{quote(package_name, safe='@/')}"
    return package_name, package_url


def detect_target_type(target: str) -> str:
    parsed = urlparse(target.strip())
    if target.startswith("npm:") or parsed.netloc == "www.npmjs.com":
        return "npm"
    if parsed.netloc == "github.com":
        return "github"
    if "/" not in target and "." not in target:
        return "npm"
    raise ValueError("Target must be a GitHub repository URL, npm package URL, or npm:<package>.")


def scrape_github_release(session, repo_url: str) -> ReleaseInfo:
    releases_url = f"{repo_url}/releases"
    session.execute(type="goto", url=releases_url)
    session.execute(type="wait", time_ms=1000)
    session.execute(type="scroll_down")
    session.execute(type="scroll_up")
    return session.scrape(
        instructions=(
            "Extract the latest GitHub release. Return the repository name, latest release tag "
            "or version, publish date, release URL, a short summary, and up to 8 important "
            "visible release note bullets."
        ),
        response_format=ReleaseInfo,
    )


def scrape_npm_release(session, package_name: str, package_url: str) -> ReleaseInfo:
    session.execute(type="goto", url=package_url)
    session.execute(type="wait", time_ms=1000)
    release = session.scrape(
        instructions=(
            f"Extract the latest npm package release information for {package_name}. Return the "
            "package name, current version, last publish date or relative publish text, package URL, "
            "a short summary, and any visible publish or health notes."
        ),
        response_format=ReleaseInfo,
    )
    if release.url is None:
        release.url = package_url
    if release.name is None:
        release.name = package_name
    return release


def run(target: str = DEFAULT_TARGET, previous_version: str | None = None) -> dict:
    """
    Monitor a GitHub repository or npm package for the latest visible release.

    Args:
        target: GitHub repo URL, npm package URL, or npm:<package>.
        previous_version: Optional version/tag to compare against.
    """
    client = NotteClient()
    target_type = detect_target_type(target)

    with client.Session(headless=True, idle_timeout_minutes=2, max_duration_minutes=10, open_viewer=True) as session:
        if target_type == "github":
            normalized_target = normalize_github_repo(target)
            latest = scrape_github_release(session, normalized_target)
        else:
            package_name, normalized_target = normalize_npm_package(target)
            latest = scrape_npm_release(session, package_name, normalized_target)

    has_new_release = None
    if previous_version:
        has_new_release = latest.version != previous_version

    return MonitorResult(
        target=normalized_target,
        target_type=target_type,
        latest=latest,
        previous_version=previous_version,
        has_new_release=has_new_release,
    ).model_dump()


def main() -> None:
    target = os.environ.get("RELEASE_MONITOR_TARGET", DEFAULT_TARGET)
    previous_version = os.environ.get("PREVIOUS_RELEASE_VERSION")
    print(json.dumps(run(target=target, previous_version=previous_version), indent=2))


if __name__ == "__main__":
    try:
        main()
    except Exception as err:
        print(f"Error: {err}")
        print("\nCommon fixes:")
        print("  - Set NOTTE_API_KEY in your environment or .env file")
        print("  - Use a GitHub repo URL, npm package URL, or npm:<package>")
        print("  - For Functions, deploy with: notte functions create --file main.py")
        raise SystemExit(1)
