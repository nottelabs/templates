# Check npm package health

Inspect npm package pages and extract release, maintenance, and repository signals for package monitoring.

Template path: `notte-templates/python/website-qa-monitoring/npm-package-health-checker`
Runtime: Python, entrypoint `main.py`.

## Run the check

```bash
cd notte-templates/python/website-qa-monitoring/npm-package-health-checker
cp .env.example .env
uv run main.py
```

Run from the repository root when you do not want to change directories:

```bash
uv run notte-templates/python/website-qa-monitoring/npm-package-health-checker/main.py
```

Useful alternate invocations:

```bash
uv run main.py react
```

## Monitor behavior

- Uses Notte browser sessions and structured scraping across npm's Overview, Code, and Dependencies tabs.
- Defaults to `react`, but accepts any package name from the command line or `.env`.
- Uses inline `uv` script metadata, so no template-specific `pyproject.toml` is required.
- Package name, version, publish status, license, homepage, repository, and last publish signal.
- Weekly downloads, dependency count, dependent count, and version count.
- Unpacked size, total file count, and visible top-level package files.
- Runtime and development dependencies from npm's Dependencies tab.
- A simple `pass` or `review` status with warnings for missing or high-risk signals.

## Check inputs

- `NOTTE_API_KEY`: required unless you are already authenticated for Notte in your environment.
- `PACKAGE_NAME`: default package when no command-line argument is provided.
- `WARMUP_URL`: page opened before npm. The CLI exploration found this made npm navigation more reliable.

## Monitoring variants

```bash
uv run notte-templates/python/website-qa-monitoring/npm-package-health-checker/main.py react
uv run notte-templates/python/website-qa-monitoring/npm-package-health-checker/main.py @types/react
PACKAGE_NAME=typescript uv run notte-templates/python/website-qa-monitoring/npm-package-health-checker/main.py
```

The raw Notte export from the CLI session is kept in `exported_workflow.py`. The final `main.py` keeps the same flow but replaces recorded package-specific selectors with parameterized package URLs.

## Reference

Notte documentation: https://docs.notte.cc/
