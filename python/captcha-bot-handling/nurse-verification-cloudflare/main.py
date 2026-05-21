# Notte: Automated License Verification - See README.md for full documentation
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "notte-sdk[playwright]",
#     "pydantic",
#     "python-dotenv",
# ]
# ///

import json
import os
from pathlib import Path

from dotenv import load_dotenv
from notte_sdk import NotteClient
from pydantic import BaseModel, Field

load_dotenv(Path(__file__).with_name(".env"))


class LicenseRecord(BaseModel):
    """Single license verification record."""

    name: str | None = Field(None, description="the name of the license holder")
    license_number: str | None = Field(None, description="the license number")
    status: str | None = Field(None, description="the status of the license")
    more_info_url: str | None = Field(None, description="URL for more information")


class LicenseResults(BaseModel):
    """Collection of license verification results."""

    list_of_licenses: list[LicenseRecord] = Field(
        default_factory=list, description="array of license verification results"
    )


LICENSE_RECORDS = [
    {
        "Site": "https://pod-search.kalmservices.net/",
        "FirstName": "Angelo",
        "LastName": "Agee",
        "LicenseNumber": "91",
    },
]


def print_viewer_url(session) -> None:
    viewer_url = getattr(session, "viewer_url", None)
    if not viewer_url:
        viewer_url = getattr(session.status(), "viewer_url", None)
    if viewer_url:
        print(f"Watch live: {viewer_url}")


def main() -> None:
    print("Starting License Verification Automation...")

    api_key = os.environ.get("NOTTE_API_KEY")
    if not api_key:
        raise RuntimeError("Missing NOTTE_API_KEY. Set it in your environment or .env file.")

    client = NotteClient(api_key=api_key)

    with client.Session(
        open_viewer=True,
        idle_timeout_minutes=2,
        solve_captchas=True,
        proxies=True,
    ) as session:
        print("Notte session started successfully")
        print(f"Session ID: {session.session_id}")
        print_viewer_url(session)

        page = session.page

        for license_record in LICENSE_RECORDS:
            print(
                f"Verifying license for: {license_record['FirstName']} {license_record['LastName']}"
            )
            print(f"Navigating to: {license_record['Site']}")
            page.goto(license_record["Site"], wait_until="domcontentloaded")
            page.wait_for_timeout(1000)

            print("Filling in license information...")
            inputs = page.locator("input")
            inputs.nth(0).press_sequentially(license_record["FirstName"])
            page.wait_for_timeout(1000)
            inputs.nth(1).press_sequentially(license_record["LastName"])
            page.wait_for_timeout(1000)
            inputs.nth(3).press_sequentially(license_record["LicenseNumber"])

            print("Clicking search button...")
            page.get_by_role("button", name="Search").click()
            session.execute(type="wait", time_ms=3000)

            try:
                session.execute(
                    type="captcha_solve", captcha_type="cloudflare", raise_on_failure=False
                )
            except Exception as error:
                print(f"Captcha solve step did not complete: {error}")

            print("Extracting license verification results...")
            try:
                extracted = session.scrape(
                    instructions=(
                        "Extract all license verification results from the page, including name, "
                        "license number, status, and more info URL if present."
                    ),
                    response_format=LicenseResults,
                )
            except Exception as error:
                print(f"No extractable license results found: {error}")
                extracted = LicenseResults()

            print("License verification results extracted:")
            print(json.dumps(extracted.model_dump(), indent=2))

    print("Session closed successfully")


if __name__ == "__main__":
    try:
        main()
    except Exception as err:
        print(f"Application error: {err}")
        print("Common issues:")
        print("  - Check .env has NOTTE_API_KEY")
        print("  - The license site may require captcha solving")
        print("Docs: https://docs.notte.cc/")
        exit(1)
