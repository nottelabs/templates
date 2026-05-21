# Run Notte TypeScript templates

Install shared dependencies once, typecheck the workspace, and run any Notte TypeScript template from one npm workspace.

Template path: `notte-templates/ts`
Runtime: TypeScript, entrypoint `package.json`.

## Workspace layout

This folder is an npm workspace root for all TypeScript Notte templates.

## Install

```bash
cd notte-templates/ts
npm install
```

The install is shared by every template under `ts/<category>/<template>`.
`package-lock=false` is set in `.npmrc`, so this does not create lockfiles.

## Check the workspace

```bash
npm run typecheck
```

## Run one template

From this directory:

```bash
npm --workspace notte-getting-started-node start
```

Or from the template directory:

```bash
cd getting-started/getting-started-with-notte
npm start
```

## Run the full set

```bash
npm run start:all
```

This starts real Notte sessions for every template, so use it intentionally.

## Cleanup

```bash
npm run clean
```

## Reference

Notte documentation: https://docs.notte.cc/
