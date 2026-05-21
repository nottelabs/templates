# Exploration Notes

- Target: `https://www.npmjs.com/package/react`
- Notte auth: succeeded via local keyring.
- Initial direct navigation to npm in session `d44a5818-3c50-4371-b0f5-75f289e7a55c` failed and closed the session.
- A proxy-backed retry session `ff117ac4-a371-440f-9232-d663a07cf61c` also closed before page interaction.
- Session `cd12f557-0731-4bbb-bc3c-9ccde7577a31` succeeded after first navigating to `https://example.com`, then to npm.
- CLI observed npm package page signals: `react` version `19.2.6`, public/published, `132,495,634` weekly downloads, MIT license, GitHub repository, React homepage, `0 Dependencies`, `210953 Dependents`, `2,804 Versions`, collaborators `fb` and `react-bot`.
- Code tab scrape returned unpacked size `166 kB`, `11` files, and visible top-level files including `cjs/`, `LICENSE`, `README.md`, `index.js`, `package.json`, and JSX runtime files.
- Dependencies tab scrape returned zero runtime dependencies and zero dev dependencies.
- Exported with `notte sessions workflow-code --session-id cd12f557-0731-4bbb-bc3c-9ccde7577a31`.
