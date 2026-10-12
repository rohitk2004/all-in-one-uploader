"""
Firstory Automation Bot
======================
Automates login to Firstory Studio (studio.firstory.me),
generates AI content via OpenRouter, creates a new playlist with Title & Description,
and extracts the public share URL.

Login Credentials:
  Email: fultois@purelymail.com
  Password: Rohit@123321#
"""

import os
import sys
import time
from typing import Dict, Optional, List, Generator
from playwright.sync_api import sync_playwright
from unique_content_engine import generate_unique_description

FIRSTORY_LOGIN_URL = "https://studio.firstory.me/login?role=creator"
FIRSTORY_NEW_PLAYLIST_URL = "https://studio.firstory.me/playlists/new"

DEFAULT_EMAIL = "fultois@purelymail.com"
DEFAULT_PASSWORD = "Rohit@123321#"

def create_firstory_playlist(
    title: str,
    description: Optional[str] = None,
    email: str = DEFAULT_EMAIL,
    password: str = DEFAULT_PASSWORD,
    headless: bool = True,
    api_key: Optional[str] = None,
    tfn: Optional[str] = None
) -> Dict:
    """
    Log into Firstory, generate description via OpenRouter using Unique Content Engine (if not provided),
    create a new playlist, and return the public share URL.
    """
    if not description:
        print(f"[*] Generating AI description via Unique Content Engine for title: '{title}'...")
        try:
            description = generate_unique_description(title=title, api_key=api_key, tfn=tfn)
        except Exception as e:
            print(f"[!] Warning: Unique Content Engine error: {e}. Falling back to default description.")
            description = f"{title}\n\nFor official assistance and support, call +1 877 848 5082 or +1 888 308 7172."

    print(f"[*] Launching Playwright browser (headless={headless})...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context(viewport={"width": 1280, "height": 800})
        page = context.new_page()

        try:
            print(f"[*] [1/5] Navigating to login page: {FIRSTORY_LOGIN_URL}...")
            page.goto(FIRSTORY_LOGIN_URL, wait_until="networkidle", timeout=60000)

            # Check if email field is present
            if page.locator("input#email").is_visible(timeout=5000):
                print(f"[*] Logging in as {email}...")
                page.fill("input#email", email)
                page.fill("input#password", password)
                page.click('button:has-text("Log in")')
                page.wait_for_timeout(5000)

            print(f"[*] [2/5] Checking show selection...")
            # If on /shows page, click the first show row
            if "shows" in page.url or page.locator("table tr").count() > 1:
                print("[*] Clicking first available show row...")
                page.locator("tr button, tr a, td").first.click()
                page.wait_for_timeout(3000)

            print(f"[*] [3/5] Navigating to playlist creation page: {FIRSTORY_NEW_PLAYLIST_URL}...")
            page.goto(FIRSTORY_NEW_PLAYLIST_URL, wait_until="networkidle", timeout=60000)
            page.wait_for_timeout(3000)

            # Fill title and description
            print(f"[*] [4/5] Filling Playlist Title & Description...")
            page.wait_for_selector("input#title", timeout=20000)
            page.fill("input#title", title)
            
            page.wait_for_selector("textarea#description", timeout=20000)
            page.fill("textarea#description", description)

            # Click Save button
            print("[*] [5/5] Saving Playlist...")
            save_button = page.locator('button:has-text("Save")').first
            save_button.scroll_into_view_if_needed()
            save_button.click()

            page.wait_for_timeout(6000)

            # Extract share link from "Share Playlist" input field
            share_url = None
            
            # Selector strategies for the share playlist URL box
            for selector in [
                'input[value*="open.firstory.me/playlists"]',
                '//h6[contains(text(),"Share Playlist")]/parent::div/following-sibling::div//input',
                '//div[contains(text(),"Share Playlist")]/following-sibling::div//input',
                'div:has(> h6:has-text("Share Playlist")) + div input'
            ]:
                if page.locator(selector).count() > 0:
                    share_url = page.locator(selector).first.input_value()
                    if share_url and "open.firstory.me/playlists" in share_url:
                        break

            # Fallback: search all input fields on page for open.firstory.me link
            if not share_url:
                inputs = page.locator('input').all()
                for inp in inputs:
                    try:
                        val = inp.input_value()
                        if val and "open.firstory.me/playlists" in val:
                            share_url = val
                            break
                    except Exception:
                        pass

            # Fallback 2: check page content or current URL for playlist ID
            if not share_url:
                page_url = page.url
                if "/playlists/" in page_url and "/new" not in page_url:
                    playlist_id = page_url.split("/playlists/")[-1].split("?")[0]
                    if playlist_id:
                        share_url = f"https://open.firstory.me/playlists/{playlist_id}"

            browser.close()

            if share_url:
                print(f"[+] SUCCESS: Playlist created! Public URL: {share_url}")
                return {
                    "success": True,
                    "title": title,
                    "share_url": share_url,
                    "description_length": len(description),
                    "error": None
                }
            else:
                print("[-] FAILED: Save clicked but could not locate Share Playlist URL.")
                return {
                    "success": False,
                    "title": title,
                    "share_url": None,
                    "error": "Share URL element not found after saving."
                }

        except Exception as e:
            browser.close()
            print(f"[!] Error creating Firstory playlist: {e}")
            return {
                "success": False,
                "title": title,
                "share_url": None,
                "error": str(e)
            }

def batch_create_firstory_playlists(
    titles: List[str],
    email: str = DEFAULT_EMAIL,
    password: str = DEFAULT_PASSWORD,
    start_index: int = 1,
    headless: bool = True,
    api_key: Optional[str] = None,
    tfn: Optional[str] = None
) -> Generator[Dict, None, None]:
    """
    Yields creation result dictionary for each title in the list.
    """
    total = len(titles)
    for idx, title in enumerate(titles, 1):
        print(f"\n[{idx}/{total}] Processing Firstory playlist for: '{title}'...")
        res = create_firstory_playlist(title, email=email, password=password, headless=headless, api_key=api_key, tfn=tfn)
        yield res

if __name__ == "__main__":
    test_title = "How to cancel Total Adblock Subscription - Live Test"
    res = create_firstory_playlist(test_title, headless=True)
    print("\n============================================================")
    print("[+] TEST RESULT:")
    for k, v in res.items():
        print(f"  {k}: {v}")
    print("============================================================")
