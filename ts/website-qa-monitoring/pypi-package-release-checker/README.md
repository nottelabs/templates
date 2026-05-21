# Check PyPI package releases

Read PyPI package pages and extract current version and release metadata for dependency monitoring.

Template path: `notte-templates/ts/website-qa-monitoring/pypi-package-release-checker`
Runtime: TypeScript, entrypoint `main.ts`.

## Run the check

```bash
cd notte-templates/ts/website-qa-monitoring/pypi-package-release-checker
cp .env.example .env
npm install --no-package-lock
npm start
```

Useful alternate invocations:

```bash
npm start -- requests
```

## Check inputs

- `NOTTE_API_KEY`: required Notte API key.
- `PACKAGE_NAME`: default package when no CLI argument is provided.
- `KNOWN_VERSION`: optional version to compare against.
- `USE_PROXY`: defaults to `true`; keep enabled if PyPI blocks direct browser traffic.

The script opens the PyPI project page in a Notte browser, fetches PyPI JSON metadata, validates it with Zod schemas, and prints the latest release report.

## Reference

Notte documentation: https://docs.notte.cc/
