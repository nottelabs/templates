# Extract and download images

Give the template a page URL and download the images discovered during the Notte browser session.

Template path: `notte-templates/ts/downloads-files/image-url-download`
Runtime: TypeScript, entrypoint `main.ts`.

## Download once

```bash
cd notte-templates/ts/downloads-files/image-url-download
cp .env.example .env
npm install --no-package-lock
npm start
```

Useful alternate invocations:

```bash
npm start -- "https://example.com/gallery"
```

## File workflow

- URL extraction: uses Playwright over the Notte session CDP URL to read `img` sources and CSS background image URLs from the rendered DOM.
- Format-aware naming: uses the `Content-Type` response header to choose file extensions.
- Organized output: images are saved to `./images/<hostname>/`.

## Download controls

- `NOTTE_API_KEY`: Notte API key used by the Node SDK.
- `MAX_IMAGES`: configurable cap on how many images to download per run. Defaults to `10`.
- `OUTPUT_DIR`: configurable output directory, defaulting to `./images`.

## File handling notes

- Missing credentials: verify `.env` contains `NOTTE_API_KEY`.
- Zero images found: the page may lazy-load images; add scrolling before extraction if needed.
- Download failures: some image endpoints block direct asset requests.

## Reference

Notte documentation: https://docs.notte.cc/
