# Notte: Apartment Applications with Vault - See README.md for full documentation
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
from pathlib import Path

from dotenv import load_dotenv
from notte_core.credentials import PASSWORD, USERNAME
from notte_sdk import NotteClient
from pydantic import BaseModel, Field

load_dotenv(Path(__file__).with_name(".env"))

BASE_URL = "https://apartment-board-demo-nine.vercel.app"
LOGIN_URL = f"{BASE_URL}/auth/signin"
STATE_FILE = Path(__file__).with_name(".vault-state.json")


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


def setup_vault(client: NotteClient) -> dict:
    vault = client.vaults.create(name="Alder Apartments Demo")
    client.vaults.add_or_update_credentials(
        vault_id=vault.vault_id,
        url=LOGIN_URL,
        username="alder",
        password="rentals123",
    )
    state = {"vault_id": vault.vault_id}
    save_state(state)
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
    state = load_state() or setup_vault(client)

    with client.Session(
        headless=True,
        idle_timeout_minutes=3,
        max_duration_minutes=15,
        vault_id=state["vault_id"],
        open_viewer=True,
    ) as session:
        session.execute(type="goto", url="https://apartment-board-demo-nine.vercel.app/")
        session.execute(type="click", selector='internal:role=link[name="Log In"i]')
        session.observe()
        session.execute(type="form_fill", value={"username": USERNAME, "password": PASSWORD})
        session.execute(type="click", selector='internal:role=button[name="Log In"i]')
        session.page.wait_for_load_state()
        applications = scrape_applications(session)

    return {
        "vault_id": state["vault_id"],
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
        print("  - Delete .vault-state.json to recreate the vault and demo credentials")
        raise SystemExit(1)
