# Find datasets on Data.gov

Search Data.gov, visit dataset detail pages, and return ranked metadata for public datasets.

Template path: `notte-templates/python/structured-scraping/data-gov-dataset-finder`
Runtime: Python, entrypoint `main.py`.

## Run a scrape

```bash
cd notte-templates/python/structured-scraping/data-gov-dataset-finder
cp .env.example .env
uv run main.py
```

Run from the repository root when you do not want to change directories:

```bash
uv run notte-templates/python/structured-scraping/data-gov-dataset-finder/main.py
```

Useful alternate invocations:

```bash
uv run main.py --query climate --limit 5
```

## Extraction path

- Defaults to `climate`, but accepts any query and result limit from the CLI or `.env`.
- Uses Notte browser sessions and structured scraping against `catalog.data.gov` search and dataset detail pages.
- Uses inline `uv` script metadata, so no template-specific `pyproject.toml` is required.
- Search query, search URL, result-count text, and sort option.
- Ranked datasets with title, organization, description summary, formats, relevance, views, and detail URL.
- Enriched detail fields for each selected result, including source/homepage and downloadable resources when visible.

## Query controls

- `NOTTE_API_KEY`: required by the Python SDK.
- `DATA_GOV_QUERY`: default query when `--query` is omitted.
- `DATA_GOV_RESULT_LIMIT`: default number of ranked results to enrich with detail pages.

## Try another target

```bash
uv run notte-templates/python/structured-scraping/data-gov-dataset-finder/main.py --query climate --limit 5
uv run notte-templates/python/structured-scraping/data-gov-dataset-finder/main.py --query "water quality" --limit 3
DATA_GOV_QUERY=wildfire DATA_GOV_RESULT_LIMIT=2 uv run notte-templates/python/structured-scraping/data-gov-dataset-finder/main.py
```

The Notte CLI exploration succeeded. The raw exported workflow is kept in `exported_workflow.py`; notes from the exploration are in `exploration-notes.md`.

## Reference

Notte documentation: https://docs.notte.cc/
