# Exploration Notes

- Notte CLI auth status: authenticated via keyring.
- First session ID: `a6bbb14b-97ab-4135-b304-11243a72eaa6`.
- `https://books.toscrape.com/` failed to load and closed that session.
- Successful session ID: `d29a69d7-93d0-45fd-94e9-437910e5c354`.
- Successful entry URL: `http://books.toscrape.com/`.
- Homepage/catalog observations:
  - Listing cards use `article.product_pod`.
  - Product title/detail links are under `h3 a`.
  - Prices use `.price_color`.
  - Stock text uses `.availability`.
  - Ratings are represented by classes on `.star-rating`.
  - Pagination uses `li.next a`.
- Detail page observations:
  - Main title uses `.product_main h1`.
  - Product facts are in `table.table.table-striped tr`.
  - Description uses `#product_description + p`.
  - Breadcrumb categories use `.breadcrumb li a`.

## Exported Workflow Basis

```python
from notte_sdk import NotteClient

client = NotteClient()

def run():
    with client.Session(use_file_storage=True) as session:
        _ = session.execute(type='goto', url='http://books.toscrape.com/')
        _ = session.scrape(
            instructions='Extract the visible books on this catalog page as JSON with title, price, stock status, rating text, product detail URL, image URL, and page URL. Also include any next page URL and visible category names.',
            only_main_content=False,
            only_images=False,
            scrape_links=True,
            scrape_images=False,
        )
        _ = session.execute(type='click', selector={'playwright_selector': 'internal:role=link[name="A Light in the ..."i]'})
        _ = session.execute(
            type='evaluate_js',
            code='() => { const rows=[...document.querySelectorAll("table.table.table-striped tr")].map(tr=>({key:tr.querySelector("th")?.textContent.trim(), value:tr.querySelector("td")?.textContent.trim()})); return {title: document.querySelector(".product_main h1")?.textContent.trim(), rating:[...document.querySelector(".product_main .star-rating")?.classList||[]].find(c=>!["star-rating"].includes(c)), description: document.querySelector("#product_description + p")?.textContent.trim(), rows}; }',
        )
        return session.scrape(
            instructions='Extract this product detail page as JSON with title, price excluding tax, price including tax, tax, availability text, UPC, product type, review count, star rating text, description, category breadcrumb, and image URL.',
            only_main_content=False,
            only_images=False,
            scrape_links=True,
            scrape_images=False,
        )

run()
```
