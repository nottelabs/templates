# Notte: Job Board Persona Email Applications - See README.md for full documentation
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "notte-sdk",
#     "pydantic",
#     "python-dotenv",
# ]
# ///

from __future__ import annotations

import html
import json
import re
import time
from pathlib import Path

from dotenv import load_dotenv
from notte_sdk import NotteClient
from pydantic import BaseModel, Field

load_dotenv(Path(__file__).with_name(".env"))

JOB_BOARD_URL = "https://job-board-demo-one.vercel.app/"
STATE_FILE = Path(__file__).with_name(".persona-state.json")
VERIFY_LINK_PATTERN = re.compile(r'href="([^"]+)"')


class Application(BaseModel):
    title: str | None = None
    company: str | None = None
    location: str | None = None
    job_type: str | None = None
    submitted_date: str | None = None
    status: str | None = None


class ApplicationsData(BaseModel):
    applications: list[Application] = Field(default_factory=list)


def load_state() -> dict | None:
    if not STATE_FILE.exists():
        return None
    return json.loads(STATE_FILE.read_text())


def save_state(state: dict) -> None:
    STATE_FILE.write_text(json.dumps(state, indent=2) + "\n")


def latest_verify_link(persona, attempts: int = 12) -> str:
    for _ in range(attempts):
        emails = persona.emails(limit=10, only_unread=False)
        for message in emails:
            body = message.html_content or message.text_content or ""
            if "job-board-demo-one.vercel.app" not in body:
                continue
            match = VERIFY_LINK_PATTERN.search(body)
            if match:
                return html.unescape(match.group(1))
        time.sleep(5)
    raise RuntimeError("No job board sign-in email arrived for the persona.")


def setup_persona(client: NotteClient):
    persona = client.Persona(create_vault=True)
    info = persona.info
    return {
        "persona_id": info.persona_id,
        "email": info.email,
        "vault_id": info.vault_id,
    }, persona


def sign_in_with_persona(session, persona, state: dict) -> None:
    session.execute(type="goto", url=JOB_BOARD_URL)
    session.execute(type="click", selector='internal:role=button[name="Sign In"i]')
    session.execute(
        type="fill",
        selector='internal:role=textbox[name="you@example.com"i]',
        value=state["email"],
    )
    session.execute(type="click", selector='internal:role=button[name="Send Sign-In Link"i]')

    verify_url = latest_verify_link(persona)
    session.execute(type="goto", url=verify_url)
    session.page.wait_for_load_state()


def open_applications(session) -> None:
    session.execute(type="click", selector='internal:role=button[name="Open account menu"i]')
    session.execute(type="click", selector='internal:role=menuitem[name="Applications"i]')
    session.page.wait_for_load_state()


def scrape_applications(session) -> ApplicationsData:
    return session.scrape(
        instructions=(
            "Extract the signed-in user's applications. Return each application with title, "
            "company, location, job type, submitted date, and status."
        ),
        response_format=ApplicationsData,
    )


def run() -> dict:
    client = NotteClient()
    state = load_state()
    if state is None:
        state, persona = setup_persona(client)
        save_state(state)
    else:
        persona = client.Persona(state["persona_id"])

    with client.Session(headless=True, idle_timeout_minutes=3, max_duration_minutes=15, open_viewer=True) as session:
        sign_in_with_persona(session, persona, state)
        open_applications(session)
        applications = scrape_applications(session)

    return {
        "persona_id": state["persona_id"],
        "email": state["email"],
        "applications": [application.model_dump() for application in applications.applications],
    }


def main() -> None:
    print(json.dumps(run(), indent=2))


if __name__ == "__main__":
    try:
        main()
    except Exception as err:
        print(f"Error: {err}")
        print("\nCommon fixes:")
        print("  - Set NOTTE_API_KEY in your environment or .env file")
        print("  - Delete .persona-state.json to create a fresh persona")
        print("  - Wait a few seconds and rerun if Supabase email delivery is delayed")
        raise SystemExit(1)
