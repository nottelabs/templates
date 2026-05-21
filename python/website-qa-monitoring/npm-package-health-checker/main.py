# Notte: npm Package Health Checker - See README.md for full documentation
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
import sys
from pathlib import Path
from urllib.parse import quote

from dotenv import load_dotenv
from notte_sdk import NotteClient
from pydantic import BaseModel, Field

load_dotenv(Path(__file__).with_name(".env"))

PACKAGE_NAME = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("PACKAGE_NAME", "react")
NPM_PACKAGE_BASE_URL = "https://www.npmjs.com/package"
WARMUP_URL = os.environ.get("WARMUP_URL", "https://example.com")


class PackageOverview(BaseModel):
    package_name: str | None = Field(None, description="Package name shown by npm")
    current_version: str | None = Field(None, description="Current published package version")
    publish_status: str | None = Field(None, description="Public/private and published state")
    weekly_downloads: int | None = Field(None, description="Weekly download count")
    license: str | None = Field(None, description="Package license")
    repository_link: str | None = Field(None, description="Repository URL")
    homepage_link: str | None = Field(None, description="Homepage URL")
    last_publish: str | None = Field(None, description="Last publish text")
    dependency_count: int | None = Field(None, description="Dependency count visible on the tab")
    dependent_count: int | None = Field(None, description="Dependent count visible on the tab")
    version_count: int | None = Field(None, description="Version count visible on the tab")
    maintainers: list[str] = Field(default_factory=list, description="Visible maintainers or collaborators")
    health_links: list[str] = Field(default_factory=list, description="Visible health/security/tool links")


class CodeMetadata(BaseModel):
    unpacked_size: str | None = Field(None, description="Unpacked package size")
    total_files: int | None = Field(None, description="Total files in the package")
    visible_top_level_files_or_folders: list[str] = Field(
        default_factory=list,
        description="Visible top-level files and folders on npm's Code tab",
    )
    package_quality_details: dict[str, str] = Field(
        default_factory=dict,
        description="Visible links to third-party quality tools",
    )


class DependencyMetadata(BaseModel):
    dependencies_count: int | None = Field(None, description="Runtime dependency count")
    dev_dependencies_count: int | None = Field(None, description="Dev dependency count")
    dependencies: list[str] = Field(default_factory=list, description="Visible runtime dependencies")
    dev_dependencies: list[str] = Field(default_factory=list, description="Visible dev dependencies")


def package_url(package_name: str, active_tab: str | None = None) -> str:
    encoded_name = quote(package_name, safe="@/")
    url = f"{NPM_PACKAGE_BASE_URL}/{encoded_name}"
    if active_tab:
        url = f"{url}?activeTab={active_tab}"
    return url


def print_viewer_url(session) -> None:
    viewer_url = getattr(session, "viewer_url", None)
    if not viewer_url:
        viewer_url = getattr(session.status(), "viewer_url", None)
    if viewer_url:
        print(f"Live View: {viewer_url}")


def scrape_overview(session, package_name: str) -> PackageOverview:
    session.execute(type="goto", url=package_url(package_name))
    session.execute(type="wait", time_ms=1000)
    return session.scrape(
        instructions=(
            f"Extract npm package health facts for package {package_name}. "
            "Return the package name, current version, public/published state, weekly downloads, "
            "license, repository link, homepage link, last publish text, dependency count, "
            "dependent count, version count, maintainers/collaborators, and visible health, "
            "security, provenance, bundle-size, dependency, or malware-report links."
        ),
        response_format=PackageOverview,
    )


def scrape_code_metadata(session, package_name: str) -> CodeMetadata:
    session.execute(type="goto", url=package_url(package_name, "code"))
    session.execute(type="wait", time_ms=1000)
    return session.scrape(
        instructions=(
            f"On npm's Code tab for package {package_name}, extract package file metadata: "
            "unpacked size, total file count, visible top-level files or folders, and links "
            "to package quality tools such as Socket, Bundlephobia, Snyk, or npmgraph."
        ),
        response_format=CodeMetadata,
    )


def scrape_dependency_metadata(session, package_name: str) -> DependencyMetadata:
    session.execute(type="goto", url=package_url(package_name, "dependencies"))
    session.execute(type="wait", time_ms=1000)
    return session.scrape(
        instructions=(
            f"On npm's Dependencies tab for package {package_name}, extract runtime and dev "
            "dependency counts plus any visible dependency names."
        ),
        response_format=DependencyMetadata,
    )


def build_health_report(
    package_name: str,
    overview: PackageOverview,
    code: CodeMetadata,
    dependencies: DependencyMetadata,
) -> dict:
    warnings: list[str] = []

    dependency_count = dependencies.dependencies_count
    if dependency_count is None:
        dependency_count = overview.dependency_count

    if not overview.repository_link:
        warnings.append("No repository link found")
    if not overview.license:
        warnings.append("No license found")
    if dependency_count and dependency_count > 20:
        warnings.append(f"High runtime dependency count: {dependency_count}")
    if not overview.last_publish:
        warnings.append("No last publish signal found")

    status = "pass" if not warnings else "review"

    return {
        "package": package_name,
        "status": status,
        "warnings": warnings,
        "overview": overview.model_dump(),
        "code": code.model_dump(),
        "dependencies": dependencies.model_dump(),
    }


def run(package_name: str = PACKAGE_NAME) -> dict:
    api_key = os.environ.get("NOTTE_API_KEY")
    client = NotteClient(api_key=api_key) if api_key else NotteClient()

    with client.Session(open_viewer=True, idle_timeout_minutes=3, proxies=True) as session:
        print(f"Session ID: {session.session_id}")
        print_viewer_url(session)

        print(f"Warming up browser with {WARMUP_URL}...")
        session.execute(type="goto", url=WARMUP_URL)

        print(f"Checking npm package: {package_name}")
        overview = scrape_overview(session, package_name)
        code = scrape_code_metadata(session, package_name)
        dependencies = scrape_dependency_metadata(session, package_name)

    return build_health_report(package_name, overview, code, dependencies)


def main() -> None:
    report = run()
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    try:
        main()
    except Exception as err:
        print(f"Error: {err}")
        print("\nTroubleshooting:")
        print("  - Set NOTTE_API_KEY in your environment or .env file")
        print("  - Try another package with: uv run main.py <package-name>")
        print("  - npm may occasionally block first navigation; keep WARMUP_URL enabled")
        raise SystemExit(1)
