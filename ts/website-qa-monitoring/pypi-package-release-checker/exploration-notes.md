# Exploration Notes

Assigned website: https://pypi.org/project/requests/

## Notte CLI Exploration

- Auth check succeeded with `notte auth status`.
- First session `1a4de664-9d46-4c74-9629-e2710796a943` closed immediately after resolving an existing active session conflict.
- Second session `124a7a12-0a9e-42c3-ac29-0a77d486142f` failed direct PyPI navigation with a reachability error.
- Proxy session `07a2a926-5aa3-431f-a5c3-b417fc9fc6b8` successfully navigated to `https://pypi.org/project/requests/`.
- Follow-up `observe`, `scrape`, and `eval-js` calls could not attach because the proxy session had closed after the successful navigation step.

## Exported Workflow Code

Export command:

```bash
notte sessions workflow-code --session-id 07a2a926-5aa3-431f-a5c3-b417fc9fc6b8
```

Exported code:

```python
from notte_sdk import NotteClient

client = NotteClient()

def run():
    with client.Session(proxies=True, use_file_storage=True) as session:
        _ = session.execute(type='goto', url='https://pypi.org/project/requests/')
        return "Successfully completed task"

run()
```

## Template Notes

The final template keeps the exported workflow's Notte client, proxied session, file storage setting, and PyPI project navigation. It parameterizes the package name and fetches PyPI's structured JSON metadata from the browser context for reliable release fields.
