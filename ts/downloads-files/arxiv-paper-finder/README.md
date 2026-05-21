# Find and download arXiv papers

Search arXiv, choose a result, and download the selected paper PDF with metadata for the run.

Template path: `notte-templates/ts/downloads-files/arxiv-paper-finder`
Runtime: TypeScript, entrypoint `main.ts`.

## Download once

```bash
cd notte-templates/ts/downloads-files/arxiv-paper-finder
cp .env.example .env
npm install --no-package-lock
npm start
```

Useful alternate invocations:

```bash
npm start -- "openai" --limit 5 --result-index 1
npm --prefix ts/downloads-files/arxiv-paper-finder start -- "openai" --limit 5 --result-index 1
```

## File workflow

- Default query: `openai`.
- Parameterized by search query, result limit, selected result index, and local download directory.
- Uses arXiv Advanced Search because `openai` returns a smaller result set there than the broad homepage search.
- Uses `evaluate_js` to read only the selected search result and article metadata from the DOM.
- Uses Node `fetch` for the final PDF download because the current Node SDK does not expose Python's `client.FileStorage()` helper.

## Download controls

- `NOTTE_API_KEY`: Notte API key used by the Node SDK.
- `SEARCH_QUERY`: default query when no command-line query is provided.
- `RESULT_LIMIT`: default number of results to extract. Must be between 1 and 50.
- `RESULT_INDEX`: default 1-based result index to open and download.
- `DOWNLOAD_DIR`: local directory where PDFs are saved. Defaults to `./downloads/arxiv`.
- `USE_PROXY`: optional; set to `true` if arXiv rejects direct browser traffic.

## Reference

Notte documentation: https://docs.notte.cc/
