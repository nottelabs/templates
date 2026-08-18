# Template contribution rules

These instructions apply to the entire repository.

## Keep Python and TypeScript templates paired

- Every template must have both a Python and a TypeScript implementation at matching paths:
  - `python/<category>/<template-name>/`
  - `ts/<category>/<template-name>/`
- Both implementations must provide the same workflow, inputs, defaults, CLI options, and output shape.
- Do not publish or document one runtime before the other is ready.

## Required files

Each Python template must include:

- `main.py` with inline `uv` script metadata for its dependencies
- `.env.example` containing placeholders only
- `README.md` with setup, run commands, inputs, behavior, and operational caveats

Each TypeScript template must include:

- `main.ts`
- `package.json` with `start` and `typecheck` scripts
- `.env.example` containing placeholders only
- `README.md` matching the Python documentation and behavior

Add focused tests for deterministic parsing, normalization, fallback, or orchestration logic. TypeScript templates with tests should expose an `npm test` script and include test files in their `typecheck` command.

## Validation

Before submitting a template:

1. Run the Python entrypoint's help or non-destructive smoke path with `uv run`.
2. Run the TypeScript template's tests and type-check.
3. Run the full TypeScript workspace type-check from `ts/`.
4. Perform one safe live run for both implementations when credentials and a suitable public target are available.
5. Confirm both runtimes produce equivalent results.

Do not commit API keys, `.env` files, `node_modules`, generated reports, or unrelated run artifacts.

## Publishing to the templates gallery

The public gallery is maintained in `nottelabs/monorepo` under `apps/front/notte-landing-v1/app/templates/`.

- Add the gallery entry only after both runtime folders exist.
- Keep the gallery slug identical to `<category>/<template-name>` so its generated Python and TypeScript source paths resolve correctly.
- Include a real Notte session replay as an MP4 and a representative poster image when publishing the gallery entry.
- Verify the landing-site production build and the generated template detail route.
- Cross-link the templates and landing pull requests.
