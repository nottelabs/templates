# Download recent arXiv AI papers

Open arXiv's Computing Research Repository Artificial Intelligence page, choose a recent article, and download the selected paper PDF with metadata for the run.

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
npm start -- --result-index 1
npm --prefix ts/downloads-files/arxiv-paper-finder start -- --result-index 1
```

## File workflow

- Opens `https://arxiv.org/`.
- Clicks the homepage link named `Computing Research Repository Artificial Intelligence`.
- Uses `evaluate_js` to click the selected recent article link from the `cs.AI` recent submissions list.
- Parameterized by selected recent article index and local download directory.
- Hardcodes Notte session proxies with `proxies: true`.
- Uses `evaluate_js` to read only the selected recent-list result and article metadata from the DOM.
- Uses Node `fetch` for the final PDF download because the current Node SDK does not expose Python's `client.FileStorage()` helper.

## Download controls

- `NOTTE_API_KEY`: Notte API key used by the Node SDK.
- `RESULT_INDEX`: default 1-based recent article index to open and download.
- `DOWNLOAD_DIR`: local directory where PDFs are saved. Defaults to `./downloads/arxiv`.

## Reference

Notte documentation: https://docs.notte.cc/
