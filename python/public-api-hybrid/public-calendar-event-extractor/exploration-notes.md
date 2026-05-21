# Public Calendar Event Extractor Exploration

Target: https://www.loc.gov/events/

## Notte CLI Session IDs

- `1a930ea2-8738-44c2-b615-6c2692774699`: direct session start closed before page use.
- `43b8fd89-15af-442c-975f-762b92e13512`: direct navigation to `https://www.loc.gov/events/` closed the browser context.
- `f21dade3-5e46-42b1-8eea-032bc64bfa39`: proxied navigation to `https://www.loc.gov/events/` also closed the browser context; this session was exported with `notte sessions workflow-code --session-id f21dade3-5e46-42b1-8eea-032bc64bfa39`.
- `f2ec781c-403c-4b7d-ac31-3b88df1e982a`: proxied navigation to `https://www.loc.gov/events/?fo=json` also closed the browser context.
- `7e8b25aa-6d41-4261-bc3a-3bf01cde5f14`: session closed before `eval-js` could run.

All `notte page ...`, `notte sessions ...`, and `workflow-code` commands after session creation were run with an explicit `--session-id`.

## Findings

- The Library of Congress events page is exposed as JSON by adding `fo=json`.
- `https://www.loc.gov/events/?fo=json&c=3` returns event records under `content.results`.
- Useful fields include top-level `title`, `url`, `date`, `description`, and nested `item.event_start`, `item.event_end`, `item.building`, `item.campus`, `item.categories`, `item.attendance_conditions`, and `item.event_status`.

## Template Approach

The exported Notte workflow records the intended browser navigation but the LOC page closed the Notte browser context during CLI exploration. When `NOTTE_API_KEY` is set, the template creates a Notte session and attempts a lightweight browser visit for traceability, then performs the durable extraction against the LOC JSON listing URL. This keeps the output reliable while preserving the browser automation pattern and session visibility.
