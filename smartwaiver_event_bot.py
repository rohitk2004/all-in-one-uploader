"""
SmartWaiver Automated Event Creation Bot
1. Logs into SmartWaiver using provided credentials (akashdalla / Rohan@123321#).
2. Navigates to https://app.smartwaiver.com/events.
3. Explicitly clicks the green '+ CREATE NEW EVENT' button on screen.
4. Confirms transition to https://app.smartwaiver.com/events/create.
"""

import asyncio
import os
import sys
import argparse
from typing import Dict, Any, Optional
from playwright.async_api import async_playwright

SMARTWAIVER_LOGIN_URL = "https://app.smartwaiver.com/login"
SMARTWAIVER_EVENTS_URL = "https://app.smartwaiver.com/events"
SMARTWAIVER_CREATE_EVENT_URL = "https://app.smartwaiver.com/events/create"

PROFILE_DIR = os.path.abspath("smartwaiver_chrome_profile")
CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

DEFAULT_ID = "akashdalla"
DEFAULT_PASSWORD = "Rohan@123321#"

try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

async def click_create_new_event_button(
    username: str = DEFAULT_ID,
    password: str = DEFAULT_PASSWORD,
    profile_dir: str = PROFILE_DIR
) -> Dict[str, Any]:
    """
    Navigates to https://app.smartwaiver.com/events and clicks the green '+ CREATE NEW EVENT' button.
    """
    result = {
        "success": False,
        "current_url": None,
        "message": ""
    }

    print("=" * 60)
    print("[+] SMARTWAIVER BOT: CLICK '+ CREATE NEW EVENT'")
    print("=" * 60)

    os.makedirs(profile_dir, exist_ok=True)

    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir=profile_dir,
            executable_path=CHROME_PATH if os.path.exists(CHROME_PATH) else None,
            headless=False,
            channel="chrome" if not os.path.exists(CHROME_PATH) else None,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--start-maximized",
                "--no-default-browser-check"
            ],
            viewport=None
        )

        page = context.pages[0] if context.pages else await context.new_page()

        # Step 1: Open login page if needed
        print("\n[*] Checking authentication on https://app.smartwaiver.com/events...")
        await page.goto(SMARTWAIVER_EVENTS_URL)
        await page.wait_for_timeout(2000)

        if "login" in page.url:
            print("[*] Login required. Navigating to Login Page...")
            await page.goto(SMARTWAIVER_LOGIN_URL)
            
            email_selector = "input[type='email'], input[name='username'], input[name='email'], #username, #email"
            password_selector = "input[type='password'], input[name='password'], #password"

            form_found = False
            captcha_warned = False

            for _ in range(300):
                if "login" not in page.url:
                    form_found = True
                    break

                try:
                    email_el = await page.query_selector(email_selector)
                    password_el = await page.query_selector(password_selector)
                    if email_el and password_el and (await email_el.is_visible()) and (await password_el.is_visible()):
                        form_found = True
                        break
                except Exception:
                    pass

                is_captcha = await page.evaluate("""() => {
                    const text = document.body ? document.body.innerText : '';
                    const btn = document.querySelector('#amzn-captcha-verify-button, .captcha, iframe[src*="captcha"]');
                    return text.includes('Human Verification') || text.includes('CAPTCHA') || Boolean(btn);
                }""")

                if is_captcha and not captcha_warned:
                    print("\n[!] CAPTCHA DETECTED! PLEASE SOLVE MANUALLY IN CHROME WINDOW!")
                    captcha_warned = True

                await asyncio.sleep(1)

            if "login" in page.url and form_found:
                print("[*] Auto-filling username & password...")
                await page.locator(email_selector).first.fill(username)
                await page.locator(password_selector).first.fill(password)

                submit_btn = page.locator("button[type='submit'], input[type='submit'], button:has-text('Log In')").first
                if await submit_btn.count() > 0:
                    await submit_btn.click()
                else:
                    await page.locator(password_selector).first.press("Enter")

                await page.wait_for_timeout(3000)

            # Re-navigate to Events page
            await page.goto(SMARTWAIVER_EVENTS_URL)
            await page.wait_for_timeout(2000)

        # Step 2: On https://app.smartwaiver.com/events, click green button "+ CREATE NEW EVENT"
        print(f"\n[*] Currently at URL: {page.url}")
        print("[*] Locating green '+ CREATE NEW EVENT' button on https://app.smartwaiver.com/events...")

        # Selector for the green CREATE NEW EVENT button
        create_btn_locators = [
            "button:has-text('CREATE NEW EVENT')",
            "button:has-text('+ CREATE NEW EVENT')",
            "a:has-text('CREATE NEW EVENT')",
            "button:has-text('Create New Event')",
            ".btn-success",
            "[href*='events/create']"
        ]

        button_clicked = False
        for loc in create_btn_locators:
            btn = page.locator(loc).first
            try:
                if await btn.count() > 0 and await btn.is_visible():
                    print(f"[+] Found button using selector: '{loc}'")
                    print("[*] Clicking green '+ CREATE NEW EVENT' button...")
                    await btn.click()
                    button_clicked = True
                    break
            except Exception as e:
                pass

        if not button_clicked:
            print("[-] Button not found by text locator. Executing JS click on CREATE NEW EVENT button...")
            button_clicked = await page.evaluate("""() => {
                const btns = Array.from(document.querySelectorAll('button, a, div'));
                const target = btns.find(b => b.innerText && b.innerText.includes('CREATE NEW EVENT'));
                if (target) {
                    target.click();
                    return true;
                }
                return false;
            }""")

        await page.wait_for_timeout(2000)

        # Confirm landing on https://app.smartwaiver.com/events/create
        current_url = page.url
        result["current_url"] = current_url
        result["success"] = ("events/create" in current_url) or ("Create New Event" in (await page.content()))

        if result["success"]:
            print("\n" + "=" * 60)
            print("[+] SUCCESS! CLICKED GREEN BUTTON & NAVIGATED TO CREATE NEW EVENT SCREEN!")
            print(f"[*] Current URL: {current_url}")
            print("=" * 60)
            result["message"] = "Successfully clicked green '+ CREATE NEW EVENT' button!"
        else:
            print(f"[-] Ended at URL: {current_url}")
            result["message"] = f"Failed to open Create Event form. Current URL: {current_url}"

        print("\n[*] Keeping Chrome browser open for next instructions...")
        await asyncio.sleep(10)

    return result

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SmartWaiver Click Create New Event Bot")
    parser.add_argument("--id", type=str, default=DEFAULT_ID, help="Username/ID")
    parser.add_argument("--pass", type=str, default=DEFAULT_PASSWORD, help="Password")
    args = parser.parse_args()

    asyncio.run(click_create_new_event_button(
        username=args.id,
        password=getattr(args, 'pass')
    ))
