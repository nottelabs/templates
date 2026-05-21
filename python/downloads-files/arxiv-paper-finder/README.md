# Find and download arXiv papers

Search arXiv, choose a result, and download the selected paper PDF with metadata for the run.

Template path: `notte-templates/python/downloads-files/arxiv-paper-finder`
Runtime: Python, entrypoint `main.py`.

## Download once

```bash
cd notte-templates/python/downloads-files/arxiv-paper-finder
cp .env.example .env
uv run main.py
```

Run from the repository root when you do not want to change directories:

```bash
uv run notte-templates/python/downloads-files/arxiv-paper-finder/main.py
```

Useful alternate invocations:

```bash
uv run main.py "openai" --limit 5 --result-index 1
```

## File workflow

- Default query: `openai`.
- Parameterized by search query, result limit, selected result index, and local download directory.
- Uses arXiv Advanced Search because `openai` returns a smaller result set there than the broad homepage search.
- Avoids `scrape()` for speed; it uses `evaluate_js` to read only the selected search result and article metadata from the DOM.
- Uses `client.FileStorage()` attached to the session, then downloads stored files into `./downloads/arxiv` by default.
- Uses inline `uv` script metadata, so no template-specific `pyproject.toml` is required.
- The submitted query and requested limit.
- arXiv's visible result count text.
- The selected search result with title, authors, arXiv ID, abstract URL, PDF URL, submitted date, subject tags, and abstract snippet.
- Metadata extracted from the selected arXiv article page.
- Local file paths for PDFs retrieved from Notte file storage.

## Download controls

- `NOTTE_API_KEY`: Notte API key used by the Python SDK.
- `SEARCH_QUERY`: default query when no command-line query is provided.
- `RESULT_LIMIT`: default number of results to extract. Must be between 1 and 50.
- `RESULT_INDEX`: default 1-based result index to open and download.
- `DOWNLOAD_DIR`: local directory where files from Notte storage are saved. Defaults to `./downloads/arxiv`.
- `FORCE_DOWNLOAD`: overwrite local files retrieved from Notte storage. Defaults to `true`.
- `USE_PROXY`: optional; set to `true` if arXiv rejects direct browser traffic.

## Other downloads

```bash
uv run notte-templates/python/downloads-files/arxiv-paper-finder/main.py "openai" --limit 5 --result-index 1
uv run notte-templates/python/downloads-files/arxiv-paper-finder/main.py "large language models browser agents" --limit 10 --result-index 2
SEARCH_QUERY="robotics control" RESULT_LIMIT=3 RESULT_INDEX=1 uv run notte-templates/python/downloads-files/arxiv-paper-finder/main.py
DOWNLOAD_DIR=./downloads/arxiv-papers uv run notte-templates/python/downloads-files/arxiv-paper-finder/main.py "retrieval augmented generation" --limit 5
```

- `exploration-notes.md` records the Notte CLI session details and selectors.
- `exported_workflow.py` keeps the exported workflow code from `notte sessions workflow-code --session-id ...` as a reference.

## Reference

Notte documentation: https://docs.notte.cc/
