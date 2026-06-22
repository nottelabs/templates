# Basic reCAPTCHA Solving with Notte - See README.md for full documentation
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "notte-sdk",
#     "pydantic",
#     "python-dotenv",
# ]
# ///

import os
from pathlib import Path

from dotenv import load_dotenv
from notte_sdk import NotteClient
from pydantic import BaseModel, Field

load_dotenv(Path(__file__).with_name(".env"))

DEMO_URL = "https://nopecha.com/captcha/recaptcha#easy"

# Set to False to disable automatic captcha solving.
solve_captchas = True
MAX_CAPTCHA_SOLVE_ATTEMPTS = 3


class PageText(BaseModel):
    text: str = Field(..., description="All text on the page")


def print_viewer_url(session) -> None:
    viewer_url = getattr(session, "viewer_url", None)
    if not viewer_url:
        viewer_url = getattr(session.status(), "viewer_url", None)
    if viewer_url:
        print(f"Live View Link: {viewer_url}")


def solve_recaptcha_with_retries(session, max_attempts: int = MAX_CAPTCHA_SOLVE_ATTEMPTS) -> None:
    last_message = "captcha solve did not run"
    for attempt in range(1, max_attempts + 1):
        print(f"Solving captcha, attempt {attempt}/{max_attempts}...")
        result = session.execute(
            type="captcha_solve",
            captcha_type="recaptcha",
            raise_on_failure=False,
        )
        last_message = getattr(result, "message", "") or str(result)
        if getattr(result, "success", False):
            print("Captcha solve action succeeded")
            return

        print(f"Captcha solve action failed: {last_message}")
        if attempt < max_attempts:
            session.execute(type="wait", time_ms=3000)

    raise RuntimeError(f"Failed to solve captcha after {max_attempts} attempts: {last_message}")


def main() -> None:
    api_key = os.environ.get("NOTTE_API_KEY")
    if not api_key:
        raise RuntimeError("Missing NOTTE_API_KEY. Set it in your environment or .env file.")

    client = NotteClient(api_key=api_key)

    with client.Session(
        open_viewer=True,
        idle_timeout_minutes=2,
        solve_captchas=solve_captchas,
        proxies=False,
        viewport_height=320,
        viewport_width=640,
    ) as session:
        print("Notte session initialized successfully")
        print(f"Session ID: {session.session_id}")
        print_viewer_url(session)

        print("Navigating to reCAPTCHA demo page...")
        session.execute(type="goto", url=DEMO_URL)

        if solve_captchas:
            solve_recaptcha_with_retries(session)
        else:
            print("Captcha solving is disabled. Skipping solve action...")

        print("Waiting for the demo page to receive the solved token callback...")
        session.execute(type="wait", time_ms=2000)

        print("Extracting page content...")
        extracted = session.scrape(
            instructions="Extract all the text on this page",
            response_format=PageText,
        )

        print("Page content:")
        print(extracted.text)

        success_markers = ('"success":true', "'success': true", "success")
        if any(marker in extracted.text.lower() for marker in success_markers):
            print("reCAPTCHA successfully solved!")
        else:
            print("Could not verify captcha success from page content")

    print("Session closed successfully")


if __name__ == "__main__":
    try:
        main()
    except Exception as err:
        print(f"Error in reCAPTCHA solving example: {err}")
        print("Common issues:")
        print("  - Check .env has NOTTE_API_KEY")
        print("  - Verify captcha solving is enabled for your Notte account")
        print("  - Ensure the demo page is accessible")
        print("Docs: https://docs.notte.cc/")
        exit(1)
