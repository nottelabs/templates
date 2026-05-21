# Notte: Form Filling Automation - See README.md for full documentation
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "notte-sdk",
#     "python-dotenv",
# ]
# ///

import os
from pathlib import Path

from dotenv import load_dotenv
from notte_sdk import NotteClient

# Load environment variables from this template directory.
load_dotenv(Path(__file__).with_name(".env"))

# Form data variables - using fake data for testing.
# Set your own variables below to customize the form submission.
text_value = "Notte deterministic form test"
password_value = "sample-password"
textarea_value = "Filled by a Notte browser session against Selenium's public demo form."
select_value = "2"
datalist_value = "Seattle"
date_value = "05/19/2026"
color_value = "#2f80ed"


def main():
    print("Starting Form Filling Example...")

    api_key = os.environ.get("NOTTE_API_KEY")
    if not api_key:
        raise RuntimeError("Missing NOTTE_API_KEY. Set it in your environment or .env file.")

    client = NotteClient(api_key=api_key)

    with client.Session(open_viewer=True, idle_timeout_minutes=2) as session:
        print("Notte session initialized successfully")
        print(f"Session ID: {session.session_id}")
        viewer_url = getattr(session, "viewer_url", None)
        if not viewer_url:
            viewer_url = getattr(session.status(), "viewer_url", None)
        if viewer_url:
            print(f"Live View Link: {viewer_url}")

        print("Navigating to Selenium web form demo...")
        session.execute(type="goto", url="https://www.selenium.dev/selenium/web/web-form.html")
        session.execute(type="wait", time_ms=1000)

        print("Filling in demo form fields...")
        session.execute(
            type="fill",
            selector='input[name="my-text"]',
            value=text_value,
            clear_before_fill=True,
        )
        session.execute(
            type="fill",
            selector='input[name="my-password"]',
            value=password_value,
            clear_before_fill=True,
        )
        session.execute(
            type="fill",
            selector='textarea[name="my-textarea"]',
            value=textarea_value,
            clear_before_fill=True,
        )
        session.execute(
            type="select_dropdown_option",
            selector='select[name="my-select"]',
            value=select_value,
        )
        session.execute(
            type="fill",
            selector='input[name="my-datalist"]',
            value=datalist_value,
            clear_before_fill=True,
        )
        session.execute(
            type="fill",
            selector='input[name="my-date"]',
            value=date_value,
            clear_before_fill=True,
        )
        session.execute(
            type="fill",
            selector='input[name="my-colors"]',
            value=color_value,
            clear_before_fill=True,
        )
        session.execute(type="click", selector="#my-check-2")
        session.execute(type="click", selector="#my-radio-2")

        # Uncomment the line below if you want to submit the form.
        # session.execute(type="click", selector='button[type="submit"]')

        print("Form filled successfully")
        session.execute(type="wait", time_ms=5000)

    print("Session closed successfully")


if __name__ == "__main__":
    try:
        main()
    except Exception as err:
        print(f"Error in form filling example: {err}")
        print("Common issues:")
        print("  - Check .env has NOTTE_API_KEY set")
        print("  - Ensure form fields are available on the Selenium demo page")
        print("Docs: https://docs.notte.cc/")
        exit(1)
