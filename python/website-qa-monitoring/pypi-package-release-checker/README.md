# Check PyPI package releases

Read PyPI package pages and extract current version and release metadata for dependency monitoring.

Template path: `notte-templates/python/website-qa-monitoring/pypi-package-release-checker`
Runtime: Python, entrypoint `main.py`.

## Run the check

```bash
cd notte-templates/python/website-qa-monitoring/pypi-package-release-checker
cp .env.example .env
uv run main.py
```

Run from the repository root when you do not want to change directories:

```bash
uv run notte-templates/python/website-qa-monitoring/pypi-package-release-checker/main.py
```

## Monitor behavior

- Default target: `requests` at https://pypi.org/project/requests/.
- Parameterized by package name through a CLI argument or `PACKAGE_NAME`.
- Uses PyPI's JSON endpoint from inside the browser context for structured release data.
- Uses inline `uv` script metadata, so no template-specific `pyproject.toml` is required.
- Opens the package page in a Notte browser session.
- Fetches package metadata from `https://pypi.org/pypi/<package>/json`.
- Prints package name, summary, latest version, release date, Python requirement, license, project URLs, and release files.
- If `KNOWN_VERSION` is set, reports whether the latest version is newer.

## Check inputs

- `NOTTE_API_KEY`: Notte API key used by the Python SDK.
- `PACKAGE_NAME`: default package when no CLI argument is provided.
- `KNOWN_VERSION`: optional version to compare against.
- `USE_PROXY`: defaults to `true`; keep enabled if PyPI blocks direct browser traffic.

## Monitoring variants

- Dependency release monitoring.
- CI-friendly package freshness checks.
- Lightweight software supply chain dashboards.

## False-positive checks

- Missing credentials: verify `.env` contains `NOTTE_API_KEY`.
- Package not found: make sure the PyPI package name is spelled correctly.
- Direct traffic blocked: leave `USE_PROXY=true`.

## Reference

Notte documentation: https://docs.notte.cc/
