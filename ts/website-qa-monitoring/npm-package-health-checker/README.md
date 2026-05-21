# Check npm package health

Inspect npm package pages and extract release, maintenance, and repository signals for package monitoring.

Template path: `notte-templates/ts/website-qa-monitoring/npm-package-health-checker`
Runtime: TypeScript, entrypoint `main.ts`.

## Run the check

```bash
cd notte-templates/ts/website-qa-monitoring/npm-package-health-checker
cp .env.example .env
npm install --no-package-lock
npm start
```

Useful alternate invocations:

```bash
npm start -- react
```

## Check inputs

- `NOTTE_API_KEY`: required Notte API key.
- `PACKAGE_NAME`: default package when no command-line argument is provided.
- `WARMUP_URL`: page opened before npm to make first navigation more reliable.

The script uses Notte sessions and Zod structured scraping across npm's Overview, Code, and Dependencies tabs, then prints a simple package health report.

## Reference

Notte documentation: https://docs.notte.cc/
