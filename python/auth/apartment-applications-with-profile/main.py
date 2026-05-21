# Notte: Apartment Applications with Profile - See README.md for full documentation
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "notte-sdk",
#     "pydantic",
#     "python-dotenv",
# ]
# ///

from __future__ import annotations

import json
import time
from pathlib import Path

from dotenv import load_dotenv
from notte_sdk import NotteClient
from pydantic import BaseModel, Field

load_dotenv(Path(__file__).with_name(".env"))

BASE_URL = "https://apartment-board-demo-nine.vercel.app"
LOGIN_URL = f"{BASE_URL}/auth/signin"
STATE_FILE = Path(__file__).with_name(".profile-state.json")


class RentalApplication(BaseModel):
    applicant: str | None = None
    application_id: str | None = None
    building: str | None = None
    unit: str | None = None
    income: str | None = None
    move_in_date: str | None = None
    status: str | None = None
    submitted_date: str | None = None


class RentalApplicationsData(BaseModel):
    applications: list[RentalApplication] = Field(default_factory=list)


def load_state() -> dict | None:
    if not STATE_FILE.exists():
        return None
    return json.loads(STATE_FILE.read_text())


def save_state(state: dict) -> None:
    STATE_FILE.write_text(json.dumps(state, indent=2) + "\n")


def setup_profile(client: NotteClient) -> dict:
    print("[setup] No saved profile state found. Creating a new Notte profile.")
    profile = client.profiles.create(name="Alder Apartments Profile Demo")
    profile_id = profile.profile_id
    print(f"[setup] Created profile: {profile_id}")
    print("[setup] Starting seed session with persist=True.")

    with client.Session(
        headless=True,
        idle_timeout_minutes=3,
        max_duration_minutes=15,
        profile={"id": profile_id, "persist": True},
    ) as session:
        print(f"[setup] Seed session started: {session.session_id}")
        print("[setup] Logging into Alder Apartments.")
        session.execute(type="goto", url=LOGIN_URL)
        session.execute(type="fill", selector="input#username", value="alder")
        session.execute(type="fill", selector="input#password", value="rentals123")
        session.execute(type="click", selector="button[type='submit']")
        session.page.wait_for_url("**/applications", timeout=10_000)
        session.page.wait_for_load_state()
        print("[setup] Login complete. Closing this session will persist cookies to the profile.")

    state = {"profile_id": profile_id}
    save_state(state)
    print(f"[setup] Saved profile state to {STATE_FILE.name}.")
    return state


def scrape_applications(session) -> RentalApplicationsData:
    return session.scrape(
        instructions=(
            "Extract the rental applications for the signed-in user. Return each application "
            "with applicant, application id, building, unit, income, move-in date, status, "
            "and submitted date."
        ),
        response_format=RentalApplicationsData,
    )


def run() -> dict:
    client = NotteClient()
    state = load_state()
    if state:
        print(f"[setup] Reusing saved profile: {state['profile_id']}")
    else:
        state = setup_profile(client)
        print("[setup] Waiting 5 seconds for the persisted profile state to become available.")
        time.sleep(5)

    print("[reuse] Starting application scrape session with persist=False.")
    with client.Session(
        headless=True,
        idle_timeout_minutes=3,
        max_duration_minutes=15,
        profile={"id": state["profile_id"], "persist": False},
        open_viewer=True
    ) as session:
        print(f"[reuse] Scrape session started: {session.session_id}")
        print("[reuse] Opening homepage and clicking Applications with the persisted profile.")
        session.execute(type="goto", url="https://apartment-board-demo-nine.vercel.app/")
        session.execute(type="click", selector='internal:role=link[name="Applications"i]')
        session.page.wait_for_load_state()
        print("[reuse] Scraping rental applications from persisted profile session.")
        applications = scrape_applications(session)
        print("[reuse] Scrape complete.")

    return {
        "profile_id": state["profile_id"],
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
        print("  - Delete .profile-state.json to create and authenticate a fresh browser profile")
        raise SystemExit(1)
