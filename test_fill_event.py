"""
SmartWaiver Fill Event & Extract Actions Column Copy Link (With 120s Interactive CAPTCHA Timeout Support)
1. Checks logged-in state. If login/CAPTCHA required, fills credentials and waits up to 120s for user to solve CAPTCHA manually.
2. Sanitizes Event Title to remove (), [], ?, :, !, quotes so SmartWaiver API validation passes cleanly.
3. Strips 4-byte UTF-8 emojis from Event Description to prevent SmartWaiver MySQL DB 500/502 Internal Server Error.
4. Enforces Description length <= 990 chars with in-sentence phone number interleaving starting directly on Line 1.
5. Intercepts API response to capture event UUID directly from response payload.
6. Constructs exact Public Waiver Link: https://waiver.smartwaiver.com/e/<UUID>/web/ (matching Event Info Link field).
"""

import asyncio
import os
import sys
import argparse
import json
import re
from typing import Dict, Any, List
from playwright.async_api import async_playwright
from description_generator import generate_event_description, DEFAULT_OPENROUTER_KEY, MAX_CHAR_LIMIT, remove_emojis_and_special

PROFILE_DIR = os.path.abspath("smartwaiver_chrome_profile")
CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
SMARTWAIVER_CREATE_EVENT_URL = "https://app.smartwaiver.com/events/create"
SMARTWAIVER_EVENTS_URL = "https://app.smartwaiver.com/events"

DEFAULT_ID = "akhileshbhai"
DEFAULT_PASSWORD = "Rohit@123321"

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

def sanitize_event_name(title: str) -> str:
    clean = re.sub(r'[\(\)\[\]\?\:\!\;\"\'\`]', ' ', title)
    clean = remove_emojis_and_special(clean)
    clean = re.sub(r'\s+', ' ', clean).strip()
    return clean if clean else "Official Event"

async def ensure_correct_user_logged_in(page, context, username, password):
    """
    Checks if logged into target account (miakhlifaa).
    If a different user is logged in or login required, explicitly signs out first,
    fills target credentials, and waits up to 120s for CAPTCHA if prompted.
    """
    try:
        current_url = page.url
        current_text = await page.evaluate("() => document.body.innerText || ''")

        if username.lower() in current_text.lower() and "login" not in current_url and "signout" not in current_url:
            print(f"[*] Target user '{username}' is already logged in cleanly.")
            return

        print(f"[*] Target account '{username}' is NOT active (Current session text does not match). Signing out old session...")
        try:
            await page.goto("https://app.smartwaiver.com/signout", wait_until="domcontentloaded", timeout=15000)
            await page.wait_for_timeout(2000)
        except Exception:
            pass

        print(f"[*] Navigating to login page for '{username}'...")
        await page.goto("https://app.smartwaiver.com/login", wait_until="domcontentloaded")
        await page.wait_for_timeout(2500)

        email_input = page.locator("input[type='email'], input[name='username'], #username").first
        if await email_input.count() > 0 and await email_input.is_visible():
            print(f"[*] Auto-filling username '{username}' and password...")
            await email_input.fill(username)
            await page.locator("input[type='password'], #password").first.fill(password)
            
            submit_btn = page.locator("button[type='submit'], #submit, button:has-text('Log In')").first
            if await submit_btn.count() > 0 and await submit_btn.is_visible():
                await submit_btn.click()
                await page.wait_for_timeout(2500)

        # Extended 120-second poll to allow manual CAPTCHA solving without browser closing
        print(f"[!] PLEASE SOLVE ANY CAPTCHA PUZZLE IN THE OPEN BROWSER WINDOW IF PROMPTED FOR '{username}'...")
        logged_in = False
        for step in range(24):
            await page.wait_for_timeout(5000)
            cur_url = page.url
            cur_text = await page.evaluate("() => document.body.innerText || ''")
            if ("login" not in cur_url and "signout" not in cur_url) or username.lower() in cur_text.lower():
                print(f"[+] Login successful! Active user: '{username}' (URL: {cur_url})...")
                logged_in = True
                break

        if not logged_in and "login" in page.url:
            print("[!] Still on login page after CAPTCHA wait. Retrying navigation to console...")
            await page.goto("https://app.smartwaiver.com/console", wait_until="domcontentloaded")
            await page.wait_for_timeout(3000)
    except Exception as e:
        print(f"[*] Relogin check notice: {e}")

async def fill_and_create_event(
    event_name: str,
    event_description: str = None,
    api_key: str = DEFAULT_OPENROUTER_KEY,
    username: str = DEFAULT_ID,
    password: str = DEFAULT_PASSWORD,
    profile_dir: str = PROFILE_DIR
) -> Dict[str, Any]:
    original_title = event_name
    sanitized_name = sanitize_event_name(event_name)

    if not event_description or not event_description.strip():
        event_description = generate_event_description(sanitized_name, api_key=api_key)
    else:
        event_description = remove_emojis_and_special(event_description)

    if len(event_description) > MAX_CHAR_LIMIT:
        event_description = event_description[:MAX_CHAR_LIMIT]

    result = {
        "success": False,
        "event_name": original_title,
        "sanitized_name": sanitized_name,
        "event_description": event_description,
        "actions_link": None,
        "console_link": None,
        "event_url": None,
        "event_id": None,
        "error": None
    }

    print("=" * 60)
    print(f"[+] SMARTWAIVER: CREATE EVENT FOR USER '{username}'")
    print("=" * 60)
    print(f"Original Title           : {original_title}")
    print(f"Sanitized Event Title    : {sanitized_name}")
    print(f"Description Length       : {len(event_description)} chars")
    print("=" * 60)

    async with async_playwright() as p:
        context = None
        browser = None

        try:
            os.makedirs(profile_dir, exist_ok=True)
            context = await p.chromium.launch_persistent_context(
                user_data_dir=profile_dir,
                executable_path=CHROME_PATH if os.path.exists(CHROME_PATH) else None,
                headless=False,
                channel="chrome" if not os.path.exists(CHROME_PATH) else None,
                args=["--disable-blink-features=AutomationControlled", "--start-maximized"],
                viewport=None
            )
        except Exception:
            browser = await p.chromium.launch(
                executable_path=CHROME_PATH if os.path.exists(CHROME_PATH) else None,
                headless=False,
                args=["--disable-blink-features=AutomationControlled", "--start-maximized"]
            )
            context = await browser.new_context(viewport=None)

        await context.grant_permissions(["clipboard-read", "clipboard-write"])
        page = context.pages[0] if context.pages else await context.new_page()

        print("\n[*] Navigating to Create Event page...")
        try:
            await page.goto(SMARTWAIVER_CREATE_EVENT_URL, wait_until="domcontentloaded", timeout=20000)
        except Exception:
            pass
        await page.wait_for_timeout(1500)

        # Enforce correct account login with 120s CAPTCHA patience
        await ensure_correct_user_logged_in(page, context, username, password)

        try:
            if "events/create" not in page.url:
                await page.goto(SMARTWAIVER_CREATE_EVENT_URL, wait_until="domcontentloaded", timeout=20000)
                await page.wait_for_timeout(1500)
        except Exception:
            pass

        # 1. Fill Sanitized Event Name
        print(f"[*] Filling Sanitized Event Name into #eventname: '{sanitized_name}'...")
        name_input = page.locator("#eventname, #title, input[name='name']").first
        await name_input.wait_for(state="visible", timeout=15000)
        await name_input.click()
        await page.wait_for_timeout(200)
        await name_input.press("Control+A")
        await name_input.press("Backspace")
        await name_input.type(sanitized_name, delay=20)
        await name_input.dispatch_event("input")
        await name_input.dispatch_event("change")
        await name_input.press("Tab")

        await page.wait_for_timeout(300)

        # 2. Fill Event Description
        print(f"[*] Filling Clean ASCII Event Description into #Eventdescription ({len(event_description)} chars)...")
        desc_input = page.locator("#Eventdescription, textarea[name='description']").first
        await desc_input.wait_for(state="visible", timeout=15000)
        await desc_input.click()
        await page.wait_for_timeout(200)
        await desc_input.press("Control+A")
        await desc_input.press("Backspace")

        await desc_input.fill(event_description)
        await page.evaluate("""(desc) => {
            const el = document.querySelector('#Eventdescription') || document.querySelector('textarea[name="description"]');
            if (el) {
                el.value = desc;
                el.dispatchEvent(new Event('input', { bubbles: true }));
                el.dispatchEvent(new Event('change', { bubbles: true }));
                el.dispatchEvent(new Event('blur', { bubbles: true }));
            }
        }""", event_description)

        await page.wait_for_timeout(500)

        # 3. Intercept API response JSON to capture UUID
        captured_uuid = {}
        async def on_response(response):
            if "api/events" in response.url:
                try:
                    data = await response.json()
                    if "event" in data and "uuid" in data["event"]:
                        captured_uuid["uuid"] = data["event"]["uuid"]
                    elif "uuid" in data:
                        captured_uuid["uuid"] = data["uuid"]
                except Exception:
                    pass

        page.on("response", on_response)

        # 4. Click CREATE EVENT button
        print("[*] Clicking 'CREATE EVENT' button (#createbutton)...")
        create_btn = page.locator("#createbutton, button:has-text('CREATE EVENT')").first
        await create_btn.scroll_into_view_if_needed()
        await create_btn.click()

        print("[*] Waiting 4 seconds for event creation...")
        await page.wait_for_timeout(4000)

        # Dismiss error popup if any
        try:
            ok_btn = page.locator("button:has-text('OK'), .v-btn:has-text('OK')").first
            if await ok_btn.count() > 0 and await ok_btn.is_visible():
                await ok_btn.click()
                await page.wait_for_timeout(500)
        except Exception:
            pass

        # 5. Navigate to Events list table (https://app.smartwaiver.com/events)
        print("[*] Navigating to Events list table (https://app.smartwaiver.com/events)...")
        await page.goto(SMARTWAIVER_EVENTS_URL, wait_until="domcontentloaded")
        await page.wait_for_timeout(2500)

        # 6. Click Actions Copy Button & Extract UUID from row
        print(f"[*] Locating event in table and extracting Actions COPY link...")
        
        extracted_info = await page.evaluate("""(targetName) => {
            const rows = Array.from(document.querySelectorAll('table tbody tr, tr.v-data-table__tr'));
            for (let r of rows) {
                const text = (r.innerText || '').toLowerCase();
                if (text.includes(targetName.substring(0, 15).toLowerCase())) {
                    const copyBtn = r.querySelector('button[title*="Copy"], .mdi-content-copy, button.mr-4');
                    if (copyBtn) copyBtn.click();

                    const anchor = r.querySelector('a[href*="/events/detail/"]');
                    if (anchor) {
                        const href = anchor.getAttribute('href') || anchor.href;
                        const parts = href.split('/events/detail/');
                        if (parts.length > 1) {
                            const uuid = parts[1].split('?')[0].split('#')[0];
                            return { uuid: uuid, found: true };
                        }
                    }
                }
            }
            const firstAnchor = document.querySelector('table tbody tr a[href*="/events/detail/"]');
            if (firstAnchor) {
                const parts = (firstAnchor.getAttribute('href') || firstAnchor.href).split('/events/detail/');
                if (parts.length > 1) {
                    return { uuid: parts[1].split('?')[0].split('#')[0], found: true };
                }
            }
            return { uuid: null, found: false };
        }""", sanitized_name)

        event_uuid = captured_uuid.get("uuid") or extracted_info.get("uuid")

        if event_uuid:
            exact_public_link = f"https://waiver.smartwaiver.com/e/{event_uuid}/web/"
            console_link = f"https://app.smartwaiver.com/events/detail/{event_uuid}"
            result["actions_link"] = exact_public_link
            result["console_link"] = console_link
            result["event_url"] = exact_public_link
            result["event_id"] = event_uuid
            result["success"] = True
        else:
            result["event_url"] = None
            result["success"] = False

        print("\n" + "=" * 60)
        print(f"[+] EXACT PUBLIC EVENT LINK FOR {username}: {result['actions_link']}")
        print(f"[+] CONSOLE DETAIL LINK                     : {result['console_link']}")
        print("=" * 60)

        try:
            if page and not page.is_closed():
                await page.close()
            if browser:
                await browser.close()
            elif context:
                await context.close()
        except Exception:
            pass

    return result

async def batch_fill_and_create_events(
    items_list: List[Dict[str, str]],
    username: str = DEFAULT_ID,
    password: str = DEFAULT_PASSWORD,
    profile_dir: str = PROFILE_DIR
):
    """
    Launches Chrome ONCE, logs in ONCE, and creates all events in items_list
    continuously inside the SAME open browser window without closing between items!
    Yields each created event in real-time as it finishes.
    """
    print("=" * 60)
    print(f"[+] BATCH MODE: PROCESSING {len(items_list)} EVENT(S) IN 1 CONTINUOUS BROWSER SESSION FOR '{username}'")
    print("=" * 60)

    async with async_playwright() as p:
        context = None
        browser = None

        try:
            os.makedirs(profile_dir, exist_ok=True)
            context = await p.chromium.launch_persistent_context(
                user_data_dir=profile_dir,
                executable_path=CHROME_PATH if os.path.exists(CHROME_PATH) else None,
                headless=False,
                channel="chrome" if not os.path.exists(CHROME_PATH) else None,
                args=["--disable-blink-features=AutomationControlled", "--start-maximized"],
                viewport=None
            )
        except Exception:
            browser = await p.chromium.launch(
                executable_path=CHROME_PATH if os.path.exists(CHROME_PATH) else None,
                headless=False,
                args=["--disable-blink-features=AutomationControlled", "--start-maximized"]
            )
            context = await browser.new_context(viewport=None)

        await context.grant_permissions(["clipboard-read", "clipboard-write"])
        page = context.pages[0] if context.pages else await context.new_page()

        print("\n[*] Navigating to Create Event page...")
        try:
            await page.goto(SMARTWAIVER_CREATE_EVENT_URL, wait_until="domcontentloaded", timeout=20000)
        except Exception:
            await page.goto(SMARTWAIVER_EVENTS_URL, wait_until="domcontentloaded")

        # Login ONCE for the whole batch
        await ensure_correct_user_logged_in(page, context, username, password)

        # Loop through all event titles in the SAME open browser session!
        for idx, item in enumerate(items_list):
            original_title = item["name"]
            event_description = item["description"]
            sanitized_name = sanitize_event_name(original_title)

            if len(event_description) > MAX_CHAR_LIMIT:
                event_description = event_description[:MAX_CHAR_LIMIT]

            print("\n" + "=" * 60)
            print(f"[*] BATCH ITEM ({idx + 1}/{len(items_list)}): '{sanitized_name}'")
            print("=" * 60)

            captured_uuid = {"uuid": None}

            async def handle_response(response):
                try:
                    if "/api/v4/events" in response.url or "/events" in response.url:
                        if response.status in [200, 201]:
                            text = await response.text()
                            if "uuid" in text:
                                data = json.loads(text)
                                uuid_val = data.get("uuid") or data.get("data", {}).get("uuid")
                                if uuid_val:
                                    captured_uuid["uuid"] = uuid_val
                except Exception:
                    pass

            page.on("response", handle_response)

            # Always navigate to Create Event for a fresh form on each item
            await page.goto(SMARTWAIVER_CREATE_EVENT_URL, wait_until="domcontentloaded", timeout=20000)
            await page.wait_for_timeout(2000)

            # Step 1: Fill Event Title using the correct #eventname selector
            title_input = page.locator("#eventname, #title, input[name='name'], input[name='eventname']").first
            await title_input.wait_for(state="visible", timeout=20000)
            await title_input.click()
            await page.wait_for_timeout(200)
            await title_input.press("Control+A")
            await title_input.press("Backspace")
            await title_input.type(sanitized_name, delay=20)
            await title_input.dispatch_event("input")
            await title_input.dispatch_event("change")
            await title_input.press("Tab")

            await page.wait_for_timeout(300)

            # Step 2: Fill Description using the correct #Eventdescription selector
            desc_area = page.locator("#Eventdescription, textarea[name='description']").first
            await desc_area.wait_for(state="visible", timeout=20000)
            await desc_area.click()
            await page.wait_for_timeout(200)
            await desc_area.press("Control+A")
            await desc_area.press("Backspace")
            await desc_area.fill(event_description)
            await page.evaluate("""(desc) => {
                const el = document.querySelector('#Eventdescription') || document.querySelector('textarea[name="description"]');
                if (el) { el.value = desc; el.dispatchEvent(new Event('input', {bubbles:true})); el.dispatchEvent(new Event('change', {bubbles:true})); }
            }""", event_description)

            await page.wait_for_timeout(500)

            # Step 3: Click CREATE EVENT button using correct #createbutton selector
            print(f"[*] Clicking CREATE EVENT button for batch item {idx+1}...")
            create_btn = page.locator("#createbutton, button:has-text('CREATE EVENT')").first
            await create_btn.scroll_into_view_if_needed()
            await create_btn.click()
            await page.wait_for_timeout(4000)

            # Dismiss error popup if any
            try:
                ok_btn = page.locator("button:has-text('OK'), .v-btn:has-text('OK')").first
                if await ok_btn.count() > 0 and await ok_btn.is_visible():
                    await ok_btn.click()
                    await page.wait_for_timeout(500)
            except Exception:
                pass

            # Navigate to events list to extract UUID from table row
            await page.goto(SMARTWAIVER_EVENTS_URL, wait_until="domcontentloaded")
            await page.wait_for_timeout(2500)

            # Extract Event UUID
            event_uuid = captured_uuid.get("uuid")
            if not event_uuid:
                extracted_info = await page.evaluate("""(nameToFind) => {
                    const rows = Array.from(document.querySelectorAll('table tbody tr, tr.v-data-table__tr'));
                    for (const row of rows) {
                        const text = (row.innerText || '').toLowerCase();
                        if (text.includes(nameToFind.substring(0, 15).toLowerCase())) {
                            const a = row.querySelector('a[href*="/events/detail/"]');
                            if (a) {
                                const parts = (a.getAttribute('href') || a.href).split('/events/detail/');
                                if (parts.length > 1) return { uuid: parts[1].split('?')[0].split('#')[0] };
                            }
                        }
                    }
                    const firstAnchor = document.querySelector('table tbody tr a[href*="/events/detail/"]');
                    if (firstAnchor) {
                        const parts = (firstAnchor.getAttribute('href') || firstAnchor.href).split('/events/detail/');
                        if (parts.length > 1) return { uuid: parts[1].split('?')[0].split('#')[0] };
                    }
                    return { uuid: null };
                }""", sanitized_name)
                event_uuid = extracted_info.get("uuid")

            actions_link = f"https://waiver.smartwaiver.com/e/{event_uuid}/web/" if event_uuid else None
            console_link = f"https://app.smartwaiver.com/events/detail/{event_uuid}" if event_uuid else None

            item_result = {
                "success": (actions_link is not None),
                "event_name": original_title,
                "sanitized_name": sanitized_name,
                "event_description": event_description,
                "actions_link": actions_link,
                "console_link": console_link,
                "event_url": actions_link
            }

            # Remove response listener so it doesn't accumulate across batch items
            page.remove_listener("response", handle_response)

            print(f"[+] BATCH EVENT {idx+1} COMPLETED: {actions_link}")
            yield item_result

        # Close browser ONCE after full batch is finished!
        print("\n[*] Event batch complete! Closing browser session...")
        try:
            if page and not page.is_closed():
                await page.close()
            if browser:
                await browser.close()
            elif context:
                await context.close()
        except Exception:
            pass

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fill Event & Copy Link from Actions Column")
    parser.add_argument("--name", type=str, default="(Complete-Guide) How do I cancel my subscription to TotalAdblock? (SUPPORT USA)", help="Event Name")
    args = parser.parse_args()

    asyncio.run(fill_and_create_event(event_name=args.name))
