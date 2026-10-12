"""
SmartWaiver Automated Login Bot (Persistent Dedicated Profile)
Launches system Google Chrome in a separate isolated window (without closing user's existing Chrome windows).
Allows manual CAPTCHA solving, auto-fills login credentials, and navigates to https://app.smartwaiver.com/console/
"""

import asyncio
import os
import sys
import argparse
from typing import Optional
from playwright.async_api import async_playwright

SMARTWAIVER_LOGIN_URL = "https://app.smartwaiver.com/login"
SMARTWAIVER_CONSOLE_URL = "https://app.smartwaiver.com/console/"
PROFILE_DIR = os.path.abspath("smartwaiver_chrome_profile")
CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

DEFAULT_EMAIL = "qi.n.gy.a.n.t.r.on.g@gmail.com"
DEFAULT_PASSWORD = "Rohit@123321"

try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

async def login_to_smartwaiver(
    email: str = DEFAULT_EMAIL,
    password: str = DEFAULT_PASSWORD,
    profile_dir: str = PROFILE_DIR
) -> bool:
    """
    Launches system Chrome in a separate isolated profile context.
    Safely leaves user's other Chrome windows untouched.
    """
    print("=" * 60)
    print("[+] SMARTWAIVER BOT STARTED (DEDICATED CHROME PROFILE)")
    print("=" * 60)
    print(f"Target Login URL   : {SMARTWAIVER_LOGIN_URL}")
    print(f"Target Console URL : {SMARTWAIVER_CONSOLE_URL}")
    print(f"Isolated Profile   : {profile_dir}")
    print(f"Account Email      : {email}")
    print("=" * 60)

    os.makedirs(profile_dir, exist_ok=True)

    async with async_playwright() as p:
        # Launch persistent context using system Chrome executable
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

        print("\n[*] Navigating to SmartWaiver Login Page...")
        await page.goto(SMARTWAIVER_LOGIN_URL)

        # Check if already logged in / redirected to console
        if "console" in page.url:
            print("[+] Already logged in! Currently on SmartWaiver Console.")
            return True

        print("\n[*] Waiting for Login Form or Manual CAPTCHA Resolution...")
        
        email_selector = "input[type='email'], input[name='username'], input[name='email'], #username, #email"
        password_selector = "input[type='password'], input[name='password'], #password"
        
        form_found = False
        captcha_warned = False

        for _ in range(300): # Up to 5 minutes for user manual CAPTCHA solving
            if "console" in page.url:
                print("\n[+] Redirected to console URL!")
                form_found = True
                break

            try:
                email_el = await page.query_selector(email_selector)
                password_el = await page.query_selector(password_selector)

                if email_el and password_el and (await email_el.is_visible()) and (await password_el.is_visible()):
                    form_found = True
                    print("[+] Login form detected and ready!")
                    break
            except Exception:
                pass

            is_captcha = await page.evaluate("""() => {
                const text = document.body ? document.body.innerText : '';
                const btn = document.querySelector('#amzn-captcha-verify-button, .captcha, iframe[src*="captcha"]');
                return text.includes('Human Verification') || text.includes('CAPTCHA') || Boolean(btn);
            }""")

            if is_captcha and not captcha_warned:
                print("\n[!] CAPTCHA / Human Verification DETECTED ON SCREEN!")
                print("    👉 PLEASE SOLVE THE CAPTCHA MANUALLY IN THE OPENED CHROME WINDOW!")
                captcha_warned = True

            await asyncio.sleep(1)

        if not form_found and "console" not in page.url:
            print("\n[-] Timeout waiting for CAPTCHA resolution or login form.")
            await context.close()
            return False

        if "console" in page.url:
            print(f"\n[+] Successfully logged in! Console URL: {page.url}")
            return True

        # Auto-fill credentials
        print("\n[*] Auto-filling Email & Password credentials...")
        email_input = page.locator(email_selector).first
        await email_input.fill(email)

        password_input = page.locator(password_selector).first
        await password_input.fill(password)

        print("[*] Submitting Login Form...")
        submit_btn = page.locator("button[type='submit'], input[type='submit'], button:has-text('Log In'), button:has-text('Login')").first
        
        if await submit_btn.count() > 0:
            await submit_btn.click()
        else:
            await password_input.press("Enter")

        # Monitor navigation to /console/
        print("\n[*] Waiting for redirect to https://app.smartwaiver.com/console/...")
        
        console_reached = False
        captcha_after_warned = False

        for _ in range(300):
            current_url = page.url
            if "console" in current_url:
                console_reached = True
                break

            is_captcha = await page.evaluate("""() => {
                const text = document.body ? document.body.innerText : '';
                return text.includes('Human Verification') || text.includes('CAPTCHA') || text.includes('Verification Code');
            }""")

            if is_captcha and not captcha_after_warned:
                print("\n[!] Additional Verification/CAPTCHA/2FA detected after submit!")
                print("    👉 PLEASE COMPLETE THE VERIFICATION MANUALLY IN THE CHROME WINDOW!")
                captcha_after_warned = True

            await asyncio.sleep(1)

        if console_reached or "console" in page.url:
            print("\n" + "=" * 60)
            print("[+] SUCCESS! LOGGED IN TO SMARTWAIVER CONSOLE!")
            print(f"[*] Current Page URL: {page.url}")
            print("=" * 60)
            return True
        else:
            print(f"\n[-] Login process ended at URL: {page.url}")
            return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SmartWaiver Automated Login Bot")
    parser.add_argument("--email", type=str, default=DEFAULT_EMAIL, help="SmartWaiver Account Email")
    parser.add_argument("--password", type=str, default=DEFAULT_PASSWORD, help="SmartWaiver Account Password")
    args = parser.parse_args()

    asyncio.run(login_to_smartwaiver(
        email=args.email,
        password=args.password
    ))
