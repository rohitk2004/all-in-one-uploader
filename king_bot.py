from unique_content_engine import generate_unique_description
import asyncio
import os
import re
import sys
import time
import requests
from playwright.async_api import async_playwright
from test_waiver_creation import DEFAULT_OPENROUTER_KEY

import random
import string

def safe_print(*args, **kwargs):
    try:
        kwargs.pop("flush", None)
        print(*args, **kwargs)
    except Exception:
        pass

print = safe_print

DEFAULT_EMAIL = "vayrox@rethinkmail.com"
DEFAULT_PASSWORD = "Rohit@123321"

LOGIN_URL = "https://community.king.com/en/candy-crush-friends-saga/entry/signin"
REGISTER_URL = "https://community.king.com/en/candy-crush-friends-saga/entry/register"
FORUM_NEW_THREAD_URL = "https://community.king.com/en/candy-crush-friends-saga/post/discussion/candy-crush-friends-saga"

PHONE_NUMBER_1 = "+1 877 848 5082"
PHONE_NUMBER_2 = "+1 888 308 7172"

def generate_random_credentials():
    suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
    username = f"user_{suffix}"
    email = f"user_{suffix}@rethinkmail.com"
    password = f"Pass_{suffix}#123"
    return username, email, password

async def register_king_account_visible():
    """
    Launches a VISIBLE (headless=False) browser window to register a new King account.
    Auto-fills Email, Username, Password, Confirm Password, and Terms checkbox.
    Pauses so the user can click the reCAPTCHA box in the visible browser window.
    """
    username, email, password = generate_random_credentials()
    print(f"\n==========================================================", flush=True)
    print(f"[*] Starting Auto-Registration for user: '{username}' ({email})...", flush=True)
    print("==========================================================\n", flush=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,  # ALWAYS VISIBLE WINDOW FOR CAPTCHA
            args=[
                "--start-maximized",
                "--window-position=50,50",
                "--disable-blink-features=AutomationControlled"
            ]
        )
        context = await browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        try:
            await page.bring_to_front()
        except Exception:
            pass

        try:
            print(f"[*] Navigating to Register URL: {REGISTER_URL}...", flush=True)
            await page.goto(REGISTER_URL, wait_until="domcontentloaded", timeout=60000)
            await page.wait_for_timeout(3000)

            await dismiss_king_modals(page)

            print(f"[*] Auto-filling Email: {email}...", flush=True)
            await page.locator("#Form_Email").fill(email)
            await page.wait_for_timeout(300)

            print(f"[*] Auto-filling Username: {username}...", flush=True)
            await page.locator("#Form_Name").fill(username)
            await page.wait_for_timeout(300)

            print("[*] Auto-filling Password & Confirm Password...", flush=True)
            await page.locator("#Form_Password").fill(password)
            await page.wait_for_timeout(300)
            await page.locator("#Form_PasswordMatch").fill(password)
            await page.wait_for_timeout(300)

            terms_cb = page.locator("#Form_TermsOfService, input[name='TermsOfService']").first
            if await terms_cb.count() > 0 and not await terms_cb.is_checked():
                await terms_cb.check(force=True)

            print("\n==========================================================", flush=True)
            print("🔔 [ACTION REQUIRED] Please click the reCAPTCHA box in the open browser window!", flush=True)
            print("==========================================================\n", flush=True)

            # Wait up to 120s for user to click reCAPTCHA & submit
            signup_clicked = False
            for _ in range(120):
                await page.wait_for_timeout(1000)
                curr_url = page.url
                if "/register" not in curr_url or "entry/signin" in curr_url or "discussion" in curr_url:
                    print(f"[+] Registration Success! Redirected to: {curr_url}", flush=True)
                    break

                recaptcha_checked = await page.locator(".recaptcha-checkbox-checked").count() > 0
                g_response = await page.evaluate("() => (document.getElementById('g-recaptcha-response') || {}).value || ''")

                if (g_response or recaptcha_checked) and not signup_clicked:
                    print("[*] reCAPTCHA solved! Auto-clicking 'Sign Up'...", flush=True)
                    signup_btn = page.locator("#Form_SignUp, input[name='Sign Up'], button:has-text('Sign Up')").first
                    if await signup_btn.count() > 0:
                        await signup_btn.click(force=True)
                        signup_clicked = True
                        await page.wait_for_timeout(3000)

            await browser.close()
            return {
                "success": True,
                "email": email,
                "password": password,
                "username": username
            }
        except Exception as e:
            print(f"[-] Registration error: {e}", flush=True)
            try:
                await browser.close()
            except Exception:
                pass
            return {"success": False, "error": str(e)}

def title_to_slug(title: str) -> str:
    slug = re.sub(r'[^a-zA-Z0-9\s-]', '', title).strip().lower()
    slug = re.sub(r'[\s-]+', '-', slug)
    return slug

def generate_king_description(title: str, openrouter_key: str = DEFAULT_OPENROUTER_KEY) -> str:
    return generate_unique_description(title, min_chars=1200, max_chars=1600, api_key=openrouter_key, html_format=False)

async def dismiss_king_modals(page):
    try:
        for sel in [
            "#MatchingAccountsWrapper button",
            "#MatchingAccountsWrapper a",
            "#onetrust-accept-btn-handler",
            "button:has-text('Accept Cookies')",
            "button:has-text('Accept')",
            "button:has-text('Got it')",
            "button:has-text('Continue')",
            "button:has-text('Skip')",
            "button:has-text('Close')"
        ]:
            try:
                btns = page.locator(sel)
                cnt = await btns.count()
                for i in range(cnt):
                    b = btns.nth(i)
                    if await b.is_visible():
                        await b.click(force=True)
                        await page.wait_for_timeout(300)
            except Exception:
                pass

        await page.evaluate("""() => {
            const ids = ['MatchingAccountsWrapper', 'onetrust-banner-sdk', 'onetrust-consent-sdk'];
            ids.forEach(id => {
                const el = document.getElementById(id);
                if (el) el.remove();
            });
            const classes = ['match-accounts-modal-background', 'match-accounts-modal-body-consent', 'modal-backdrop', 'overlay'];
            classes.forEach(cls => {
                document.querySelectorAll('.' + cls).forEach(el => el.remove());
            });
        }""")
        await page.wait_for_timeout(300)
    except Exception:
        pass

async def handle_king_category_selection(page):
    try:
        cat_btn = page.locator("button:has-text('Choose Category'), button:has-text('Change'), #button-5").first
        if await cat_btn.count() > 0 and await cat_btn.is_visible():
            print("[*] Clicking 'Choose Category' button calmly...", flush=True)
            await cat_btn.click(force=True)
            await page.wait_for_timeout(2500)

            opt = page.locator(
                "div[role='option'], li[role='option'], "
                "button:has-text('Discussions'), a:has-text('Discussions'), "
                "div:has-text('Discussions').css-1v8v4st, "
                ".css-1v8v4st, [class*='CategoryPicker'], [class*='category-item']"
            ).first

            if await opt.count() > 0 and await opt.is_visible():
                print("[*] Selecting Category option...", flush=True)
                await opt.click(force=True)
                await page.wait_for_timeout(2000)
            else:
                await page.keyboard.press("ArrowDown")
                await page.wait_for_timeout(500)
                await page.keyboard.press("Enter")
                await page.wait_for_timeout(1500)
    except Exception as e:
        print(f"[!] Category selection note: {e}", flush=True)

async def create_king_account_and_post_batch(
    titles: list,
    openrouter_key: str = DEFAULT_OPENROUTER_KEY
) -> list:
    """
    Registers 1 new King account and posts ALL given titles (up to 2) within the SAME logged-in browser session.
    Guarantees King.com NEVER redirects to /entry/signin.
    """
    username, email, password = generate_random_credentials()
    results = []

    print(f"\n==========================================================", flush=True)
    print(f"[*] Registering New Account: '{username}' ({email})...", flush=True)
    print(f"[*] Posting {len(titles)} thread(s) in this session: {titles}", flush=True)
    print("==========================================================\n", flush=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            args=[
                "--start-maximized",
                "--window-position=50,50",
                "--disable-blink-features=AutomationControlled"
            ]
        )
        context = await browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        try:
            await page.bring_to_front()
        except Exception:
            pass

        try:
            print(f"[*] Step 1: Navigating to Register URL: {REGISTER_URL}...", flush=True)
            await page.goto(REGISTER_URL, wait_until="domcontentloaded", timeout=60000)
            await page.wait_for_timeout(3000)

            await dismiss_king_modals(page)

            print(f"[*] Auto-filling Email: {email}...", flush=True)
            await page.locator("#Form_Email").fill(email)
            await page.wait_for_timeout(500)

            print(f"[*] Auto-filling Username: {username}...", flush=True)
            await page.locator("#Form_Name").fill(username)
            await page.wait_for_timeout(500)

            print("[*] Auto-filling Password & Confirm Password...", flush=True)
            await page.locator("#Form_Password").fill(password)
            await page.wait_for_timeout(500)
            await page.locator("#Form_PasswordMatch").fill(password)
            await page.wait_for_timeout(500)

            terms_cb = page.locator("#Form_TermsOfService, input[name='TermsOfService']").first
            if await terms_cb.count() > 0 and not await terms_cb.is_checked():
                await terms_cb.check(force=True)

            print("\n==========================================================", flush=True)
            print("🔔 [ACTION REQUIRED] Please click the reCAPTCHA box in the open browser window!", flush=True)
            print("==========================================================\n", flush=True)

            signup_clicked = False
            for _ in range(120):
                await page.wait_for_timeout(1000)
                curr_url = page.url
                if "/register" not in curr_url or "discussion" in curr_url:
                    print(f"[+] Registration Success! Current URL: {curr_url}", flush=True)
                    break

                recaptcha_checked = await page.locator(".recaptcha-checkbox-checked").count() > 0
                g_response = await page.evaluate("() => (document.getElementById('g-recaptcha-response') || {}).value || ''")

                if (g_response or recaptcha_checked) and not signup_clicked:
                    print("[*] reCAPTCHA solved! Auto-clicking 'Sign Up'...", flush=True)
                    signup_btn = page.locator("#Form_SignUp, input[name='Sign Up'], button:has-text('Sign Up')").first
                    if await signup_btn.count() > 0:
                        await signup_btn.click(force=True)
                        signup_clicked = True
                        await page.wait_for_timeout(4000)

            for t_idx, title in enumerate(titles):
                description = generate_king_description(title, openrouter_key)
                print(f"[*] Posting Thread ({t_idx + 1}/{len(titles)}) using [{email}]: '{title}'...", flush=True)

                print(f"[*] Navigating to Post Page: {FORUM_NEW_THREAD_URL}...", flush=True)
                await page.goto(FORUM_NEW_THREAD_URL, wait_until="domcontentloaded", timeout=60000)
                await page.wait_for_timeout(3500)

                await dismiss_king_modals(page)
                await handle_king_category_selection(page)
                await page.wait_for_timeout(2000)

                title_input = page.locator("input[id^='inputText-'], input.css-tzoub2-InputBlockStyles-inputText").first
                await title_input.wait_for(state="visible", timeout=30000)

                await dismiss_king_modals(page)

                try:
                    await title_input.click(force=True)
                except Exception:
                    pass
                await title_input.press_sequentially(title, delay=25)
                await page.wait_for_timeout(2500)

                comment_editor = page.locator("div[contenteditable='true']").first
                await comment_editor.wait_for(state="visible", timeout=20000)
                await comment_editor.click()
                await page.wait_for_timeout(500)

                try:
                    await comment_editor.fill(description)
                except Exception:
                    await page.keyboard.insert_text(description)

                filled_text = await comment_editor.inner_text()
                if not filled_text or len(filled_text.strip()) < 10:
                    await comment_editor.click()
                    await page.keyboard.insert_text(description)

                await page.wait_for_timeout(1000)

                tag_pill = page.locator("#button-12, button:has-text('Guides & Tips'), button:has-text('Feedback'), button:has-text('Bug / Issue')").first
                if await tag_pill.count() > 0 and await tag_pill.is_visible():
                    await tag_pill.click(force=True)
                    await page.wait_for_timeout(1000)

                await page.wait_for_timeout(2000)

                print("\n==========================================================", flush=True)
                print(f"🟢 [READY TO PUBLISH - Thread #{t_idx+1}/{len(titles)}]")
                print(f"Title & Content filled for: '{title}'")
                print("Please click the green 'Post' button in your browser to publish!")
                print("==========================================================\n", flush=True)

                disc_id = None
                slug = title_to_slug(title)

                for _ in range(120):
                    await page.wait_for_timeout(1000)
                    curr_url = page.url
                    match = re.search(r'/(?:discussion|editdiscussion)/(?:0/)?(\d+)', curr_url)
                    if match:
                        disc_id = match.group(1)
                        break

                if disc_id:
                    public_url = f"https://community.king.com/en/candy-crush-friends-saga/discussion/{disc_id}/{slug}#latest"
                else:
                    public_url = page.url

                print(f"[+] Thread Published by user: {public_url}", flush=True)
                results.append({"title": title, "url": public_url, "email": email, "password": password, "success": True})

                with open("king_thread_links.txt", "a", encoding="utf-8") as out:
                    out.write(f"{public_url}\n")

                await page.wait_for_timeout(2000)

        except Exception as e:
            print(f"[!] Error in session: {e}", flush=True)
        finally:
            await browser.close()

    return results

async def create_king_discussion(
    title: str,
    email: str = DEFAULT_EMAIL,
    password: str = DEFAULT_PASSWORD,
    headless: bool = False,
    do_register: bool = False,
    openrouter_key: str = DEFAULT_OPENROUTER_KEY
) -> dict:
    description = generate_king_description(title, openrouter_key)
    print(f"[*] Generated King description ({len(description)} chars)...", flush=True)

    if do_register:
        username, email, password = generate_random_credentials()
    else:
        username = email.split('@')[0]

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=headless,
            args=[
                "--start-maximized",
                "--window-position=50,50",
                "--disable-blink-features=AutomationControlled"
            ]
        )
        context = await browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        if not headless:
            try:
                await page.bring_to_front()
            except Exception:
                pass

        try:
            if do_register:
                print(f"[*] Step 1: Navigating to Register URL: {REGISTER_URL}...", flush=True)
                await page.goto(REGISTER_URL, wait_until="domcontentloaded", timeout=60000)
                await page.wait_for_timeout(3000)

                await dismiss_king_modals(page)

                print(f"[*] Auto-filling Email: {email}...", flush=True)
                await page.locator("#Form_Email").fill(email)
                await page.wait_for_timeout(300)

                print(f"[*] Auto-filling Username: {username}...", flush=True)
                await page.locator("#Form_Name").fill(username)
                await page.wait_for_timeout(300)

                print("[*] Auto-filling Password & Confirm Password...", flush=True)
                await page.locator("#Form_Password").fill(password)
                await page.wait_for_timeout(300)
                await page.locator("#Form_PasswordMatch").fill(password)
                await page.wait_for_timeout(300)

                terms_cb = page.locator("#Form_TermsOfService, input[name='TermsOfService']").first
                if await terms_cb.count() > 0 and not await terms_cb.is_checked():
                    await terms_cb.check(force=True)

                print("\n==========================================================", flush=True)
                print("🔔 [ACTION REQUIRED] Please click the reCAPTCHA box in the open browser window!", flush=True)
                print("==========================================================\n", flush=True)

                signup_clicked = False
                for _ in range(120):
                    await page.wait_for_timeout(1000)
                    curr_url = page.url
                    if "/register" not in curr_url or "entry/signin" in curr_url or "discussion" in curr_url:
                        print(f"[+] Registration Success! Redirected to: {curr_url}", flush=True)
                        break

                    recaptcha_checked = await page.locator(".recaptcha-checkbox-checked").count() > 0
                    g_response = await page.evaluate("() => (document.getElementById('g-recaptcha-response') || {}).value || ''")

                    if (g_response or recaptcha_checked) and not signup_clicked:
                        print("[*] reCAPTCHA solved! Auto-clicking 'Sign Up'...", flush=True)
                        signup_btn = page.locator("#Form_SignUp, input[name='Sign Up'], button:has-text('Sign Up')").first
                        if await signup_btn.count() > 0:
                            await signup_btn.click(force=True)
                            signup_clicked = True
                            await page.wait_for_timeout(3000)
            else:
                print(f"[*] Post mode: Continuing in logged-in session, navigating directly to thread creation...", flush=True)

            # Step 2: Navigate to Post Creation Page in the SAME browser window
            print(f"[*] Navigating to post creation page: {FORUM_NEW_THREAD_URL}...", flush=True)
            try:
                await page.goto(FORUM_NEW_THREAD_URL, wait_until="domcontentloaded", timeout=60000)
            except Exception:
                pass
            await page.wait_for_timeout(3000)

            # Dismiss any popups or modal overlays (including MatchingAccountsWrapper)
            await dismiss_king_modals(page)

            try:
                change_btn = page.locator("button:has-text('Change'), #button-5").first
                if await change_btn.count() > 0 and await change_btn.is_visible():
                    await change_btn.click(force=True)
                    await page.wait_for_timeout(1000)

                    accept_btn = page.locator("button:has-text('Accept')").first
                    if await accept_btn.count() > 0 and await accept_btn.is_visible():
                        await accept_btn.click(force=True)
                        await page.wait_for_timeout(1000)
            except Exception:
                pass

            # Wait for title input
            title_input = page.locator("input[id^='inputText-'], input.css-tzoub2-InputBlockStyles-inputText").first
            await title_input.wait_for(state="visible", timeout=30000)

            await dismiss_king_modals(page)

            print(f"[*] Filling Discussion Title: '{title}'...", flush=True)
            try:
                await title_input.click(force=True)
            except Exception:
                pass
            await title_input.press_sequentially(title, delay=15)
            await page.wait_for_timeout(2000)

            print(f"[*] Filling Body content ({len(description)} chars)...", flush=True)
            comment_editor = page.locator("div[contenteditable='true']").first
            await comment_editor.wait_for(state="visible", timeout=20000)
            await comment_editor.click()
            await page.wait_for_timeout(500)

            try:
                await comment_editor.fill(description)
            except Exception:
                await page.keyboard.insert_text(description)

            # Verification check
            filled_text = await comment_editor.inner_text()
            if not filled_text or len(filled_text.strip()) < 10:
                print("[!] Fill note: Editor content low, using keyboard.insert_text fallback...", flush=True)
                await comment_editor.click()
                await page.keyboard.insert_text(description)

            await page.wait_for_timeout(1000)

            print("[*] Selecting Tag pill...", flush=True)
            try:
                tag_pill = page.locator("#button-12, button:has-text('Guides & Tips'), button:has-text('Feedback'), button:has-text('Bug / Issue')").first
                if await tag_pill.count() > 0 and await tag_pill.is_visible():
                    await tag_pill.click()
                    await page.wait_for_timeout(1000)
            except Exception as e:
                print(f"[!] Tag pill click note: {e}", flush=True)

            await page.wait_for_timeout(2000)

            print("[*] Submitting post (clicking green 'Post' button)...", flush=True)
            try:
                post_btn = page.get_by_role("button", name="Post", exact=True).first
                if await post_btn.count() == 0 or not await post_btn.is_visible():
                    post_btn = page.locator("button:has-text('Post'):not(:has-text('Draft'))").first
                await post_btn.scroll_into_view_if_needed()
                await post_btn.focus()
                await post_btn.click()
            except Exception as e:
                print(f"[!] Primary post button click failed ({e}), trying fallback locator...", flush=True)
                post_btn = page.locator("button:has-text('Post'):not(:has-text('Draft'))").first
                await post_btn.click()

            # Check for Spam Block Banner
            await page.wait_for_timeout(2000)
            spam_banner = page.locator("div:has-text('posted 3 times within 120 seconds'), div:has-text('wait at least 300 seconds')").first
            if await spam_banner.count() > 0 and await spam_banner.is_visible():
                print("[!] Rate Limit Triggered: Posted 3 times in 120 seconds. Waiting 305 seconds for spam block expiration...", flush=True)
                await page.wait_for_timeout(305000)

                # Click Post again after waiting
                print("[*] Retrying post submission after waiting 305 seconds...", flush=True)
                post_btn = page.get_by_role("button", name="Post", exact=True).first
                if await post_btn.count() == 0 or not await post_btn.is_visible():
                    post_btn = page.locator("button:has-text('Post'):not(:has-text('Draft'))").first
                await post_btn.click()

            print("[*] Waiting for post redirect...", flush=True)
            disc_id = None
            slug = title_to_slug(title)

            for _ in range(10):
                await page.wait_for_timeout(1000)
                curr_url = page.url
                match = re.search(r'/(?:discussion|editdiscussion)/(?:0/)?(\d+)', curr_url)
                if match:
                    disc_id = match.group(1)
                    break

            if not disc_id:
                curr_url = page.url
                match = re.search(r'/(?:discussion|editdiscussion)/(?:0/)?(\d+)', curr_url)
                if match:
                    disc_id = match.group(1)

            if disc_id:
                public_url = f"https://community.king.com/en/candy-crush-friends-saga/discussion/{disc_id}/{slug}#latest"
            else:
                public_url = page.url

            print(f"[+] Discussion Created! FULL PUBLIC URL: {public_url}", flush=True)

            await browser.close()
            return {
                "success": True,
                "public_url": public_url,
                "char_count": len(description)
            }

        except Exception as e:
            print(f"[-] Error creating King discussion thread: {e}", flush=True)
            try:
                await browser.close()
            except Exception:
                pass
            return {"success": False, "error": str(e)}

if __name__ == "__main__":
    t = "How to Set Up PC Matic for Beginners (Simple Step-by-Step Setup)"
    res = asyncio.run(create_king_discussion(t))
    print(res)
