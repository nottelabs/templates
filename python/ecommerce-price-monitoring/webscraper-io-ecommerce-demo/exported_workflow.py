from __future__ import annotations

# Exported from Notte CLI session 1a49fb7a-8225-4a53-94fa-fbce55c53c6f.
# Kept as the raw exploration baseline for the polished template in main.py.

from notte_sdk import NotteClient

from pydantic import BaseModel


class Product(BaseModel):
    title: str | None = None
    price_text: str | None = None
    description: str | None = None
    review_count: str | None = None
    detail_url: str | None = None
    image_url: str | None = None


class PaginationLink(BaseModel):
    label: str | None = None
    url: str | None = None


class Model(BaseModel):
    category_title: str | None = None
    total_item_count_text: str | None = None
    current_page_number: str | None = None
    products: list[Product] | None = None
    pagination_links: list[PaginationLink] | None = None


class Model1(BaseModel):
    title: str | None = None
    price_text: str | None = None
    description: str | None = None
    review_count: str | None = None
    selectable_hdd_options: list[str] | None = None
    currently_selected_hdd_text: str | None = None
    image_url: str | None = None
    category_breadcrumb_labels: list[str] | None = None
    current_url: str | None = None


client = NotteClient()


def run():
    with client.Session(use_file_storage=True) as session:
        _ = session.execute(
            type="goto",
            url="http://webscraper.io/test-sites/e-commerce/static/computers/laptops",
        )
        _ = session.execute(
            type="click",
            selector={
                "css_selector": (
                    "html > body > div:nth-of-type(1) > div > div > div > div > div > "
                    "div:nth-of-type(2) > button:nth-of-type(3).termly-styles-module-root-aecb0e."
                    "termly-styles-module-primary-c223ae.termly-styles-module-solid-aab01d."
                    "termly-styles-button-a4543c.t-acceptAllButton"
                ),
                "xpath_selector": "html/body/div[1]/div/div/div/div/div/div[2]/button[3]",
                "playwright_selector": 'internal:role=button[name="Accept"i]',
            },
        )
        _ = session.scrape(
            instructions=(
                "Extract the visible laptop listing page as JSON. Include category title, total item "
                "count text, current page number, product cards with title, price text, description, "
                "review count, detail URL, and image URL, plus pagination links with label and URL."
            ),
            only_main_content=True,
            only_images=False,
            scrape_links=True,
            scrape_images=False,
            response_format=Model,
        )
        _ = session.execute(
            type="evaluate_js",
            code=(
                "() => Array.from(document.querySelectorAll(\".thumbnail\")).map((card, index) => "
                "({index, title: card.querySelector(\".title\")?.textContent?.trim(), href: "
                "card.querySelector(\".title\")?.href, price: card.querySelector(\".price\")?."
                "textContent?.trim(), description: card.querySelector(\".description\")?."
                "textContent?.trim(), reviews: card.querySelector(\".ratings p.pull-right\")?."
                "textContent?.trim(), image: card.querySelector(\"img\")?.src}))"
            ),
        )
        _ = session.execute(
            type="evaluate_js",
            code=(
                "() => ({pagination: Array.from(document.querySelectorAll(\"ul.pagination a\"))."
                "map(a => ({label: a.textContent.trim(), href: a.href, parentClass: "
                "a.parentElement.className})), cards: Array.from(document.querySelectorAll("
                "\".thumbnail\")).map(card => card.innerText)})"
            ),
        )
        _ = session.execute(
            type="click",
            selector={
                "css_selector": (
                    "html > body > div:nth-of-type(2) > main > div:nth-of-type(3) > div > "
                    "div:nth-of-type(2) > div:nth-of-type(1) > div:nth-of-type(1) > div > div > "
                    "div:nth-of-type(1) > h4:nth-of-type(2) > a.title[href=\"/test-sites/e-commerce/"
                    "static/product/31\"][title=\"Packard 255 G2\"]"
                ),
                "xpath_selector": (
                    "html/body/div[2]/main/div[3]/div/div[2]/div[1]/div[1]/div/div/div[1]/h4[2]/a"
                ),
                "playwright_selector": 'internal:role=link[name="Packard 255 G2"i]',
            },
        )
        _ = session.scrape(
            instructions=(
                "Extract this product detail page as JSON: title, price text, description, review "
                "count, selectable HDD options, currently selected HDD text if any, image URL, "
                "category breadcrumb labels, and current URL."
            ),
            only_main_content=True,
            only_images=False,
            scrape_links=True,
            scrape_images=False,
            response_format=Model1,
        )
        _ = session.execute(
            type="evaluate_js",
            code=(
                "() => ({url: window.location.href, title: document.querySelector(\".caption "
                "h4:not(.price)\")?.textContent?.trim() || document.querySelector(\"h4.title\")?."
                "textContent?.trim(), price: document.querySelector(\".price\")?.textContent?."
                "trim(), description: document.querySelector(\".description\")?.textContent?.trim(), "
                "reviewsText: document.querySelector(\".ratings p\")?.textContent?.trim(), hddOptions: "
                "Array.from(document.querySelectorAll(\"button[value]\")).map(button => button."
                "textContent.trim()), image: document.querySelector(\".thumbnail img, .product-wrapper "
                "img, img\")?.src, breadcrumbs: Array.from(document.querySelectorAll(\".breadcrumb a, "
                ".sidebar a\")).map(a => a.textContent.trim()).filter(Boolean)})"
            ),
        )
        _ = session.execute(
            type="goto",
            url="http://webscraper.io/test-sites/e-commerce/static/computers/laptops?page=2",
        )
        return session.scrape(
            code=(
                "() => ({url: window.location.href, heading: document.querySelector(\"h1\")?."
                "textContent?.trim(), products: Array.from(document.querySelectorAll(\".thumbnail\"))"
                ".map((card, index) => ({index, title: card.querySelector(\".title\")?.textContent?."
                "trim(), href: card.querySelector(\".title\")?.href, price: card.querySelector("
                "\".price\")?.textContent?.trim(), description: card.querySelector(\".description\")?."
                "textContent?.trim(), reviewsText: Array.from(card.querySelectorAll(\"p\")).map(p => "
                "p.textContent.trim()).find(text => text.includes(\"reviews\")), image: card."
                "querySelector(\"img\")?.src}))})"
            )
        )


run()
