# Deploy browser automations as Functions

Package a Notte browser workflow as a reusable Function that can be invoked, inspected, and scheduled.

Template path: `notte-templates/python/functions/daily-release-monitor`
Runtime: Python, entrypoint `main.py`.

## Prepare it

```bash
cd notte-templates/python/functions/daily-release-monitor
cp .env.example .env
uv run main.py
```

Run from the repository root when you do not want to change directories:

```bash
uv run notte-templates/python/functions/daily-release-monitor/main.py
```

## Function lifecycle

- Notte Functions with a `run(...)` entry point.
- Function parameters for different targets.
- JSON return values available from run metadata.
- Scheduling a browser task with cron.

## Invocation inputs

Set `NOTTE_API_KEY` in `.env` before running the template.

## Local checks

Run against npm instead of the default target:

```bash
RELEASE_MONITOR_TARGET="npm:react" uv run main.py
```

Compare with a previous version:

```bash
RELEASE_MONITOR_TARGET="https://github.com/nottelabs/notte" \
PREVIOUS_RELEASE_VERSION="v1.0.0" \
uv run main.py
```

## Deploy it

Create the Function from this directory:

```bash
notte functions create \
  --file main.py \
  --name "Daily Release Monitor" \
  --description "Checks the latest GitHub or npm release and returns structured JSON"
```

After deployment, inspect runs with:

```bash
notte functions run
notte functions runs
notte functions run-metadata --run-id <run-id>
```

Schedule a daily check at 9 AM UTC:

```bash
notte functions schedule --cron "0 9 * * *"
```

## Reference

Notte documentation: https://docs.notte.cc/
