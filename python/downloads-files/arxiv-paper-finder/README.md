# Download recent arXiv AI papers

Open arXiv's Computing Research Repository Artificial Intelligence page, choose a recent article, and download the selected paper PDF with metadata for the run.

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
uv run main.py --result-index 1
```

## File workflow

- Opens `https://arxiv.org/`.
- Clicks the homepage link named `Computing Research Repository Artificial Intelligence`.
- Uses `evaluate_js` to click the selected recent article link from the `cs.AI` recent submissions list.
- Parameterized by selected recent article index and local download directory.
- Avoids `scrape()` for speed; it uses `evaluate_js` to read only the selected recent-list result and article metadata from the DOM.
- Uses `client.FileStorage()` attached to the session, then downloads stored files into `./downloads/arxiv` by default.
- Uses inline `uv` script metadata, so no template-specific `pyproject.toml` is required.
- The arXiv category and selected recent article index.
- arXiv's visible recent-submissions count text.
- The selected recent result with title, authors, arXiv ID, abstract URL, PDF URL, submitted date, subject tags, and abstract snippet.
- Metadata extracted from the selected arXiv article page.
- Local file paths for PDFs retrieved from Notte file storage.

## Download controls

- `NOTTE_API_KEY`: Notte API key used by the Python SDK.
- `RESULT_INDEX`: default 1-based recent article index to open and download.
- `DOWNLOAD_DIR`: local directory where files from Notte storage are saved. Defaults to `./downloads/arxiv`.
- `FORCE_DOWNLOAD`: overwrite local files retrieved from Notte storage. Defaults to `true`.
- `USE_PROXY`: optional; set to `true` if arXiv rejects direct browser traffic.

## Other downloads

```bash
uv run notte-templates/python/downloads-files/arxiv-paper-finder/main.py --result-index 1
uv run notte-templates/python/downloads-files/arxiv-paper-finder/main.py --result-index 2
RESULT_INDEX=3 uv run notte-templates/python/downloads-files/arxiv-paper-finder/main.py
DOWNLOAD_DIR=./downloads/arxiv-papers uv run notte-templates/python/downloads-files/arxiv-paper-finder/main.py --result-index 1
```

- `exploration-notes.md` records the Notte CLI session details and selectors.
- `exported_workflow.py` keeps the exported workflow code from `notte sessions workflow-code --session-id ...` as a reference.

## Reference

Notte documentation: https://docs.notte.cc/
