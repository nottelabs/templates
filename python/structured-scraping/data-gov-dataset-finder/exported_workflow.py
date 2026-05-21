# Exported from Notte CLI session 8a14e37b-c788-4ce8-b2be-b2d06468e2df.
# Kept as the raw exploration baseline for the polished template in main.py.

from __future__ import annotations

from datetime import date

from notte_sdk import NotteClient
from pydantic import BaseModel, Field


class Option(BaseModel):
    label: str | None = None
    count: int | None = None


class FacetsFilter(BaseModel):
    name: str | None = None
    options: list[Option] | None = None


class Dataset(BaseModel):
    title: str | None = None
    url: str | None = None
    organization: str | None = None
    description: str | None = None
    tags: list[str] | None = None


class Model(BaseModel):
    search_query: str | None = None
    result_count_text: str | None = None
    sort_options: list[str] | None = None
    facets_filters: list[FacetsFilter] | None = None
    datasets: list[Dataset] | None = None


class Dataset1(BaseModel):
    title: str | None = None
    url: str | None = None
    organization: str | None = None
    last_updated_date: str | None = None
    description_summary: str | None = None
    formats: list[str] | None = None
    relevance_text: str | None = None
    views_text: str | None = None


class Model1(BaseModel):
    search_query: str | None = None
    result_count_text: str | None = None
    current_url: str | None = None
    sort_option: str | None = None
    datasets: list[Dataset1] | None = None


class ContactPoint2(BaseModel):
    fn: str | None = None
    field_type: str | None = Field(None, alias="@type")
    hasEmail: str | None = None


class Publisher2(BaseModel):
    name: str | None = None
    field_type: str | None = Field(None, alias="@type")


class MetadataFields2(BaseModel):
    field_type: str | None = Field(None, alias="@type")
    accessLevel: str | None = None
    contactPoint: ContactPoint2 | None = None
    description: str | None = None
    identifier: str | None = None
    issued: date | None = None
    keyword: list[str] | None = None
    landingPage: str | None = None
    modified: date | None = None
    publisher: Publisher2 | None = None
    theme: list[str] | None = None


class Resource2(BaseModel):
    name: str | None = None
    format: str | None = None
    url: str | None = None


class Model2(BaseModel):
    title: str | None = None
    organization: str | None = None
    description: str | None = None
    last_updated: date | None = None
    homepage_source_link: str | None = None
    license: str | None = None
    metadata_fields: MetadataFields2 | None = None
    resources: list[Resource2] | None = None


client = NotteClient()


def run():
    with client.Session(use_file_storage=True) as session:
        _ = session.execute(type="goto", url="https://catalog.data.gov/dataset/?q=climate")
        _ = session.scrape(
            instructions=(
                "Extract the current data.gov search page state: search query, result count text if "
                "visible, sort options, first five dataset result titles with URLs, organizations, "
                "descriptions, tags, and any facets or filters shown. Return concise JSON-like text."
            ),
            only_main_content=True,
            only_images=False,
            scrape_links=True,
            scrape_images=False,
            response_format=Model,
        )
        _ = session.execute(type="evaluate_js", code="window.location.href")
        # This step failed because input[name='q'] matched both visible and hidden fields.
        # _ = session.execute(type="fill", selector="input[name='q']", press_enter=True, value="climate", clear_before_fill=True)
        _ = session.execute(
            type="fill",
            selector="#search-query",
            press_enter=True,
            value="climate",
            clear_before_fill=True,
        )
        _ = session.execute(type="evaluate_js", code="window.location.href")
        _ = session.execute(type="wait", time_ms=1000)
        _ = session.scrape(
            instructions=(
                "Extract the current data.gov search results as concise JSON: search query, result "
                "count text if visible, current URL, sort option, and first 5 datasets with title, "
                "URL, organization, last updated date, description summary, formats, relevance text "
                "and views text if visible."
            ),
            only_main_content=True,
            only_images=False,
            scrape_links=True,
            scrape_images=False,
            response_format=Model1,
        )
        _ = session.execute(
            type="click",
            selector={
                "css_selector": (
                    "html > body > main > div > div > div > div > div > section > ul > "
                    "li:nth-of-type(1) > div > div:nth-of-type(2) > div:nth-of-type(1) > "
                    "h3 > a.usa-link"
                ),
                "xpath_selector": "html/body/main/div/div/div/div/div/section/ul/li[1]/div/div[2]/div[1]/h3/a",
                "playwright_selector": (
                    'internal:role=link[name="NYC Climate Budgeting Report: Climate Alignment '
                    'Assessment and Capital Climate"i]'
                ),
            },
        )
        _ = session.execute(type="wait", time_ms=1000)
        return session.scrape(
            instructions=(
                "Extract dataset detail page as JSON: title, organization, description, last updated, "
                "homepage/source link if visible, license, metadata fields, and available "
                "resources/distributions with name, format, and URL."
            ),
            only_main_content=True,
            only_images=False,
            scrape_links=True,
            scrape_images=False,
            response_format=Model2,
        )


run()
