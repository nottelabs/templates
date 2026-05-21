# Basic Text CAPTCHA Solving with Notte - See README.md for full documentation
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

load_dotenv(Path(__file__).with_name(".env"))

DEMO_URL = "https://captcha.com/demos/features/captcha-demo.aspx#"
VALIDATE_SELECTOR = 'internal:role=button[name="Validate"i]'
RESULT_SELECTOR = (
    "xpath=/html[1]/body[1]/div[1]/div[1]/div[1]/form[1]/fieldset[1]/div[2]/span[1]/span[1]"
)

# Set to False to disable automatic captcha solving.
solve_captchas = True
MAX_CAPTCHA_SOLVE_ATTEMPTS = 3


def print_viewer_url(session) -> None:
    viewer_url = getattr(session, "viewer_url", None)
    if not viewer_url:
        viewer_url = getattr(session.status(), "viewer_url", None)
    if viewer_url:
        print(f"Live View Link: {viewer_url}")


def solve_text_captcha_with_retries(
    session, max_attempts: int = MAX_CAPTCHA_SOLVE_ATTEMPTS
) -> None:
    last_message = "captcha solve did not run"
    for attempt in range(1, max_attempts + 1):
        print(f"Solving text captcha, attempt {attempt}/{max_attempts}...")
        result = session.execute(
            type="captcha_solve",
            captcha_type="text",
            raise_on_failure=False,
        )
        last_message = getattr(result, "message", "") or str(result)
        if getattr(result, "success", False):
            print("Text captcha solve action succeeded")
            return

        print(f"Text captcha solve action failed: {last_message}")
        if attempt < max_attempts:
            session.execute(type="wait", time_ms=3000)

    raise RuntimeError(
        f"Failed to solve text captcha after {max_attempts} attempts: {last_message}"
    )


def main() -> None:
    api_key = os.environ.get("NOTTE_API_KEY")
    if not api_key:
        raise RuntimeError("Missing NOTTE_API_KEY. Set it in your environment or .env file.")

    client = NotteClient(api_key=api_key)

    with client.Session(
        open_viewer=True,
        idle_timeout_minutes=2,
        solve_captchas=solve_captchas,
        proxies=True,
        viewport_width=720,
        viewport_height=640,
    ) as session:
        print("Notte session initialized successfully")
        print(f"Session ID: {session.session_id}")
        print_viewer_url(session)

        print("Navigating to text CAPTCHA demo page...")
        session.execute(type="goto", url=DEMO_URL)

        if solve_captchas:
            solve_text_captcha_with_retries(session)
        else:
            print("Captcha solving is disabled. Skipping solve action...")

        print("Clicking Validate button after captcha solve step...")
        session.execute(type="click", selector=VALIDATE_SELECTOR)

        print("Scraping validation result...")
        data = session.scrape(
            only_main_content=False,
            use_link_placeholders=False,
            selector=RESULT_SELECTOR,
        )

        result_text = str(data).strip()
        print("Validation result:")
        print(result_text)

        if "Correct!" in result_text:
            print("Text CAPTCHA successfully solved!")
        elif "Incorrect!" in result_text:
            raise RuntimeError("Text CAPTCHA validation failed: Incorrect!")
        else:
            raise RuntimeError(
                f"Could not verify text CAPTCHA result from scraped content: {result_text}"
            )

    print("Session closed successfully")


if __name__ == "__main__":
    try:
        main()
    except Exception as err:
        print(f"Error in text CAPTCHA solving example: {err}")
        print("Common issues:")
        print("  - Check .env has NOTTE_API_KEY")
        print("  - Verify captcha solving and proxy access are enabled for your Notte account")
        print("  - Ensure the demo page is accessible")
        print("Docs: https://docs.notte.cc/")
        exit(1)
