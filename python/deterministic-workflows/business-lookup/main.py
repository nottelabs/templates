# Notte: Deterministic Business Lookup - See README.md for full documentation
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
import re
from pathlib import Path

from dotenv import load_dotenv
from notte_sdk import NotteClient
from pydantic import BaseModel, Field

load_dotenv(Path(__file__).with_name(".env"))
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

COMPANY_QUERY = os.environ.get("COMPANY_QUERY", "AAPL")
SEC_HOME_URL = "https://www.sec.gov/"
SEC_COMPANY_TICKERS_URL = "https://www.sec.gov/files/company_tickers_exchange.json"
SEC_COMPANY_BROWSE_URL = "https://www.sec.gov/edgar/browse/?CIK={cik}"
SEC_SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik}.json"


class VisibleCompanyProfile(BaseModel):
    company_name: str | None = Field(None, description="Company name shown on the SEC company page")
    cik: str | None = Field(None, description="SEC Central Index Key")
    ticker_symbols: str | None = Field(None, description="Ticker symbols shown on the SEC company page")
    exchanges: str | None = Field(None, description="Exchanges shown on the SEC company page")
    sic: str | None = Field(None, description="SIC code and description shown on the SEC company page")
    fiscal_year_end: str | None = Field(None, description="Fiscal year end shown on the SEC company page")
    state_of_incorporation: str | None = Field(None, description="State or jurisdiction shown on the page")
    business_address: str | None = Field(None, description="Business address shown on the SEC company page")
    mailing_address: str | None = Field(None, description="Mailing address shown on the SEC company page")
    phone: str | None = Field(None, description="Phone number shown on the SEC company page")


class CompanyInfo(BaseModel):
    company_name: str | None = Field(None, description="Company name from SEC submissions data")
    cik: str | None = Field(None, description="Zero-padded SEC Central Index Key")
    tickers: list[str] = Field(default_factory=list, description="Listed ticker symbols")
    exchanges: list[str] = Field(default_factory=list, description="Listing exchanges")
    entity_type: str | None = Field(None, description="SEC entity type")
    sic: str | None = Field(None, description="Standard Industrial Classification code")
    sic_description: str | None = Field(None, description="SIC description")
    state_of_incorporation: str | None = Field(None, description="State or jurisdiction code")
    state_of_incorporation_description: str | None = Field(None, description="State or jurisdiction name")
    fiscal_year_end: str | None = Field(None, description="Fiscal year end in MMDD format")
    business_address: str | None = Field(None, description="Formatted business address")
    mailing_address: str | None = Field(None, description="Formatted mailing address")
    phone: str | None = Field(None, description="Company phone number")
    latest_filing_form: str | None = Field(None, description="Most recent filing form in SEC submissions data")
    latest_filing_date: str | None = Field(None, description="Most recent filing date in SEC submissions data")
    latest_filing_accession_number: str | None = Field(
        None,
        description="Most recent filing accession number in SEC submissions data",
    )
    visible_profile: VisibleCompanyProfile = Field(description="Visible SEC company profile")


def print_viewer_url(session) -> None:
    viewer_url = getattr(session, "viewer_url", None)
    if not viewer_url:
        viewer_url = getattr(session.status(), "viewer_url", None)
    if viewer_url:
        print(f"Live View Link: {viewer_url}")


def wait_for_page(session) -> None:
    page = getattr(session, "page", None)
    if page is None:
        session.execute(type="wait", time_ms=5000)
        return

    page.wait_for_load_state("domcontentloaded", timeout=30000)
    page.wait_for_timeout(1500)


def wait_for_company_profile(session) -> None:
    page = getattr(session, "page", None)
    if page is None:
        session.execute(type="wait", time_ms=3000)
        return

    page.wait_for_load_state("domcontentloaded", timeout=30000)
    page.wait_for_timeout(4000)


def normalize_cik(value: str | int | None) -> str:
    digits = re.sub(r"\D", "", str(value or ""))
    if not digits:
        raise RuntimeError("Could not read a CIK")
    return digits.zfill(10)


def resolve_cik_in_browser(session, company_query: str) -> str:
    if re.fullmatch(r"\s*\d{1,10}\s*", company_query):
        return normalize_cik(company_query)

    page = getattr(session, "page", None)
    if page is None:
        raise RuntimeError("Deterministic SEC lookup requires session.page")

    match = page.evaluate(
        """async ({ url, query }) => {
            const response = await fetch(url);
            if (!response.ok) {
                throw new Error(`SEC ticker dataset request failed with ${response.status}`);
            }

            const payload = await response.json();
            const fields = payload.fields || [];
            const rows = payload.data || [];
            const records = rows.map(row => Object.fromEntries(fields.map((field, index) => [field, row[index]])));
            const normalizedQuery = query.trim().toLowerCase();

            const exactTicker = records.find(record => String(record.ticker || '').toLowerCase() === normalizedQuery);
            if (exactTicker) return exactTicker;

            const exactName = records.find(record => String(record.name || '').toLowerCase() === normalizedQuery);
            if (exactName) return exactName;

            const containsName = records.find(record => String(record.name || '').toLowerCase().includes(normalizedQuery));
            if (containsName) return containsName;

            return null;
        }""",
        {"url": SEC_COMPANY_TICKERS_URL, "query": company_query},
    )
    if not match:
        raise RuntimeError(f"No SEC ticker dataset match found for query: {company_query}")
    return normalize_cik(match.get("cik"))


def scrape_visible_profile(session) -> VisibleCompanyProfile:
    return session.scrape(
        instructions=(
            "Extract the SEC company profile header from this page. Return company_name, CIK, "
            "ticker symbols, exchanges, SIC, fiscal year end, state of incorporation, "
            "business address, mailing address, and phone. Do not include the filings table."
        ),
        response_format=VisibleCompanyProfile,
    )


def fetch_submission_in_browser(session, cik: str) -> dict:
    page = getattr(session, "page", None)
    if page is None:
        raise RuntimeError("Deterministic SEC lookup requires session.page")

    query_url = SEC_SUBMISSIONS_URL.format(cik=cik)
    submission = page.evaluate(
        """async url => {
            const response = await fetch(url);
            if (!response.ok) {
                throw new Error(`SEC submissions request failed with ${response.status}`);
            }
            return await response.json();
        }""",
        query_url,
    )
    if not submission:
        raise RuntimeError(f"No SEC submissions record found for CIK: {cik}")
    return submission


def format_address(address: dict | None) -> str | None:
    if not address:
        return None
    parts = [
        address.get("street1"),
        address.get("street2"),
        address.get("city"),
        address.get("stateOrCountry"),
        address.get("zipCode"),
    ]
    return ", ".join(part for part in parts if part)


def first_recent_value(submission: dict, key: str) -> str | None:
    values = submission.get("filings", {}).get("recent", {}).get(key, [])
    if not values:
        return None
    return values[0]


def to_company_info(submission: dict, visible_profile: VisibleCompanyProfile) -> CompanyInfo:
    addresses = submission.get("addresses", {})
    return CompanyInfo(
        company_name=submission.get("name"),
        cik=normalize_cik(submission.get("cik")),
        tickers=submission.get("tickers") or [],
        exchanges=submission.get("exchanges") or [],
        entity_type=submission.get("entityType"),
        sic=submission.get("sic"),
        sic_description=submission.get("sicDescription"),
        state_of_incorporation=submission.get("stateOfIncorporation"),
        state_of_incorporation_description=submission.get("stateOfIncorporationDescription"),
        fiscal_year_end=submission.get("fiscalYearEnd"),
        business_address=format_address(addresses.get("business")),
        mailing_address=format_address(addresses.get("mailing")),
        phone=submission.get("phone"),
        latest_filing_form=first_recent_value(submission, "form"),
        latest_filing_date=first_recent_value(submission, "filingDate"),
        latest_filing_accession_number=first_recent_value(submission, "accessionNumber"),
        visible_profile=visible_profile,
    )


def main() -> None:
    print("Starting SEC company lookup...")

    api_key = os.environ.get("NOTTE_API_KEY")
    client = NotteClient(api_key=api_key) if api_key else NotteClient()

    with client.Session(
        open_viewer=True,
        idle_timeout_minutes=2,
    ) as session:
        print("Notte session initialized successfully")
        print(f"Session ID: {session.session_id}")
        print_viewer_url(session)

        print(f"Resolving SEC company query: {COMPANY_QUERY}")
        session.execute(type="goto", url=SEC_HOME_URL)
        wait_for_page(session)

        cik = resolve_cik_in_browser(session, COMPANY_QUERY)
        print(f"Opening SEC company page for CIK: {cik}")
        session.execute(type="goto", url=SEC_COMPANY_BROWSE_URL.format(cik=cik))
        wait_for_company_profile(session)

        visible_profile = scrape_visible_profile(session)
        submission = fetch_submission_in_browser(session, cik)
        company_info = to_company_info(submission, visible_profile)

        print("Company information extracted:")
        print(json.dumps(company_info.model_dump(), indent=2))

    print("Session closed successfully")


if __name__ == "__main__":
    try:
        main()
    except Exception as err:
        print(f"Error in company lookup: {err}")
        print("Common issues:")
        print("  - Check .env has NOTTE_API_KEY")
        print("  - Search for a public company name, ticker, or CIK that appears in SEC EDGAR")
        print("  - Set COMPANY_QUERY to search for a different public company")
        print("Docs: https://docs.notte.cc/")
        exit(1)
