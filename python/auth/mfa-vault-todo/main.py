# Notte: MFA with Vaults - See README.md for full documentation
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "notte-sdk[playwright]",
#     "python-dotenv",
#     "pydantic",
# ]
# ///

import os
import traceback
from pathlib import Path

from dotenv import load_dotenv
from notte_core.credentials.base import EmailField, MFAField, PasswordField
from notte_sdk import NotteClient
from pydantic import BaseModel, Field

load_dotenv(Path(__file__).with_name(".env"))

DEMO_URL = "https://authenticationtest.com/totpChallenge/"
EMAIL = EmailField.placeholder_value
MFA = MFAField.placeholder_value
PASSWORD = PasswordField.placeholder_value


class Credentials(BaseModel):
    email: str = Field(..., description="Email address")
    password: str = Field(..., description="Password")
    totp_secret: str = Field(..., description="The TOTP secret key for generating codes")


class AuthResult(BaseModel):
    success: bool = Field(..., description="Whether authentication was successful")
    message: str = Field(..., description="Success or error message")


def print_viewer_url(session) -> None:
    viewer_url = getattr(session, "viewer_url", None)
    if not viewer_url:
        viewer_url = getattr(session.status(), "viewer_url", None)
    if viewer_url:
        print(f"Live View Link: {viewer_url}")


def create_client() -> NotteClient:
    api_key = os.environ.get("NOTTE_API_KEY")
    if not api_key:
        raise RuntimeError("Missing NOTTE_API_KEY. Set it in your environment or .env file.")
    return NotteClient(api_key=api_key)


def extract_demo_credentials(client: NotteClient) -> Credentials:
    with client.Session(open_viewer=True, idle_timeout_minutes=2) as session:
        print("Opening demo page to extract one-time setup credentials...")
        print_viewer_url(session)
        session.execute(type="goto", url=DEMO_URL)
        return session.scrape(
            instructions="Extract the test email, password, and TOTP secret key shown on the page",
            response_format=Credentials,
        )


def fill_and_submit(session) -> None:
    session.observe()
    session.execute(
        type="form_fill",
        value={
            "email": EMAIL,
            "password": PASSWORD,
            "totp": MFA,
        },
    )
    print("Filled email, password, and TOTP fields from the vault")

    page = session.page
    page.locator('input[type="submit"], button[type="submit"], form button').first.click()
    print("Submitted form")
    page.wait_for_load_state("domcontentloaded", timeout=20000)


def main() -> None:
    print("Starting MFA with Vaults...")

    client = create_client()
    credentials = extract_demo_credentials(client)

    with client.Vault() as vault:
        vault.add_credentials(
            url=DEMO_URL,
            email=credentials.email,
            password=credentials.password,
            mfa_secret=credentials.totp_secret,
        )
        print("Created an ephemeral vault with email, password, and TOTP secret")

        with client.Session(
            open_viewer=True,
            idle_timeout_minutes=2,
            vault_id=vault.vault_id,
        ) as session:
            print("Notte session initialized with ephemeral vault")
            print_viewer_url(session)

            page = session.page
            print("Navigating to TOTP Challenge page...")
            page.goto(DEMO_URL, wait_until="domcontentloaded")

            print("Filling and submitting login form with vault placeholders...")
            fill_and_submit(session)

            print("Checking authentication result...")
            result = session.scrape(
                instructions="Check if the login was successful or if there's an error message",
                response_format=AuthResult,
            )

            if result.success:
                print("SUCCESS! TOTP authentication completed automatically!")
                print(f"Authentication Result: {result.message}")
                return

            print(f"Authentication may have failed. Message: {result.message}")
            print("Retrying with a fresh vault-generated TOTP code...")
            page.goto(DEMO_URL, wait_until="domcontentloaded")
            fill_and_submit(session)

            retry_result = session.scrape(
                instructions="Check if the login was successful",
                response_format=AuthResult,
            )
            if retry_result.success:
                print("Success on retry!")
            else:
                print("Authentication failed after retry")

    print("Session closed successfully")


if __name__ == "__main__":
    try:
        main()
    except Exception as err:
        print(f"Error in MFA handling: {err}")
        traceback.print_exc()
        print("Common issues:")
        print("  - Check .env file has NOTTE_API_KEY")
        print("  - TOTP code may have expired; rerun so the vault generates a fresh one")
        print("  - Page structure may have changed")
        print("Docs: https://docs.notte.cc/")
        raise SystemExit(1)
