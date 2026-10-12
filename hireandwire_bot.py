"""
Hire & Wire Account Creator & Profile Generator Bot
==================================================
Target URLs:
  Register: https://hireandwire.com/login-register/
  Profile:  https://hireandwire.com/profile/
  Public:   https://hireandwire.com/candidate/<username>/

Workflow per profile:
  1. GET login-register page to fetch fresh nonce.
  2. Register a new candidate account via AJAX.
  3. GET profile page to fetch candidate object_id and CMB nonce.
  4. Generate rich description using OpenRouter API based on Job Title.
  5. POST profile update (_candidate_job_title and _candidate_description).
  6. Return public candidate profile URL.
  7. Logout session cleanly before the next profile creation.
"""

import os
import re
import time
import random
import string
import requests
from typing import Generator, List, Dict
from test_waiver_creation import generate_waiver_body_content, DEFAULT_OPENROUTER_KEY

SITE_URL = "https://hireandwire.com"
LOGIN_REGISTER_URL = f"{SITE_URL}/login-register/"
REGISTER_ENDPOINT = f"{SITE_URL}/?wjb-ajax=wp_job_board_ajax_register&action=wp_job_board_ajax_register"
PROFILE_URL = f"{SITE_URL}/profile/"
LOGOUT_URL = f"{SITE_URL}/login-register/?action=logout"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/126.0.0.0 Safari/537.36"
    ),
    "Referer": LOGIN_REGISTER_URL,
    "Origin": SITE_URL,
}

def create_single_profile(job_title: str, openrouter_key: str = DEFAULT_OPENROUTER_KEY) -> dict:
    """
    Creates a new account, fills job title and OpenRouter-generated description on profile,
    returns profile URL and logs out.
    """
    session = requests.Session()
    
    try:
        # 1. GET login-register page for nonce (with 3 retries & 60s timeout for slow server)
        print(f"[*] [1/5] Fetching registration page...")
        r = None
        for attempt in range(1, 4):
            try:
                r = session.get(LOGIN_REGISTER_URL, headers=HEADERS, timeout=60)
                if r.status_code == 200:
                    break
            except Exception as e:
                print(f"[!] Attempt {attempt} GET register page failed: {e}")
                time.sleep(2)

        if not r or r.status_code != 200:
            return {"success": False, "job_title": job_title, "error": "Server slow/unreachable on registration page"}

        nonce_m = re.search(r'name=["\']security_register["\']\s+value=["\']([^"\']+)["\']', r.text)
        if not nonce_m:
            nonce_m = re.search(r'id=["\']security_register["\']\s+value=["\']([^"\']+)["\']', r.text)
        nonce = nonce_m.group(1) if nonce_m else ""

        rand_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
        username = f"hiredev_{rand_str}"
        email = f"hiredev_{rand_str}@gmail.com"
        password = f"Pass_{rand_str}#99"

        print(f"[*] [2/5] Registering account '{username}' ({email})...")

        # 2. Register candidate (with retries)
        reg_data = {
            "role": (None, "wp_job_board_candidate"),
            "username": (None, username),
            "email": (None, email),
            "password": (None, password),
            "confirmpassword": (None, password),
            "company_name": (None, ""),
            "phone": (None, ""),
            "security_register": (None, nonce),
            "_wp_http_referer": (None, "/login-register/"),
            "terms_and_conditions": (None, "on"),
        }
        
        reg_resp = None
        for attempt in range(1, 4):
            try:
                reg_resp = session.post(REGISTER_ENDPOINT, files=reg_data, headers=HEADERS, timeout=60)
                if reg_resp.status_code == 200:
                    break
            except Exception as e:
                print(f"[!] Attempt {attempt} POST register failed: {e}")
                time.sleep(2)

        if not reg_resp:
            return {"success": False, "job_title": job_title, "error": "Server timeout on registration POST"}

        try:
            reg_json = reg_resp.json()
        except:
            reg_json = {}

        if not reg_json.get("status"):
            err = reg_json.get("msg") or f"HTTP {reg_resp.status_code}"
            return {"success": False, "job_title": job_title, "error": f"Registration failed: {err}"}

        print(f"[+] [3/5] Registered! Fetching candidate profile...")

        # 3. GET Profile page to extract object_id & CMB nonce
        prof_r = None
        for attempt in range(1, 4):
            try:
                prof_r = session.get(PROFILE_URL, headers=HEADERS, timeout=60)
                if prof_r.status_code == 200:
                    break
            except Exception as e:
                print(f"[!] Attempt {attempt} GET profile page failed: {e}")
                time.sleep(2)

        if not prof_r or prof_r.status_code != 200:
            return {"success": False, "job_title": job_title, "error": "Server timeout fetching profile page"}
        
        obj_m = re.search(r'name=["\']object_id["\']\s+value=["\']([^"\']+)["\']', prof_r.text)
        object_id = obj_m.group(1) if obj_m else ""

        cmb_m = re.search(r'name=["\']nonce_CMB2php_candidate_front["\']\s+value=["\']([^"\']+)["\']', prof_r.text)
        cmb_nonce = cmb_m.group(1) if cmb_m else ""

        cand_link_m = re.search(r'https?://[^\s"\'<>]*candidate/[^\s"\'<>]+', prof_r.text)
        if cand_link_m:
            public_profile_url = cand_link_m.group(0).rstrip('/') + '/'
        else:
            public_profile_url = f"{SITE_URL}/candidate/{username}/"

        # 4. Generate description via OpenRouter (Bulk Waiver Titles format)
        print(f"[*] [4/5] Generating profile description via OpenRouter API...")
        raw_content = generate_waiver_body_content(job_title, api_key=openrouter_key)
        
        # Format description matching Image 2: clean paragraphs + Image 2 phone number style
        clean_desc = re.sub(r'<p[^>]*>', '', raw_content).replace('</p>', '\n\n').strip()
        clean_desc = re.sub(r'\+1\s*877\s*848\s*5082', '+1 877-848-5082', clean_desc)
        clean_desc = re.sub(r'\+1\s*888\s*308\s*7172', '+1 888 308 7172', clean_desc)
        phone_fmt = "(+1 877-848-5082 [US/OT] and +1 888 308 7172 [US/OT] )"
        description_content = clean_desc.replace("+1 877-848-5082", phone_fmt).replace("+1 888 308 7172", phone_fmt)
        description_content = re.sub(r'(\(\+1 877-848-5082 \[US/OT\] and \+1 888 308 7172 \[US/OT\] \)\s*)+', r'\1 ', description_content)

        # Wrap paragraphs in clean HTML <p> tags for WordPress CMB2 saver
        html_description = "<p>" + description_content.replace("\n\n", "</p><p>") + "</p>"

        # 5. Save Profile (Setting _candidate_title = job_title to match Image 2 top title heading!)
        print(f"[*] [5/5] Saving Job Title & Description on profile...")
        prof_data = {
            "object_id": object_id,
            "nonce_CMB2php_candidate_front": cmb_nonce,
            "profile_url_slug": username.replace("_", "-"),
            "_candidate_show_profile": "show",
            "_candidate_title": job_title,        # <-- Candidate Main Header Title (Image 2 match!)
            "_candidate_email": email,
            "_candidate_job_title": job_title,
            "_candidate_description": html_description, # <-- Candidate Description (<p> formatted)
            "_candidate_post_type": "candidate",
            "submit-cmb-profile": "Save Profile"
        }
        
        for attempt in range(1, 4):
            try:
                session.post(PROFILE_URL, data=prof_data, headers=HEADERS, timeout=60)
                break
            except Exception as e:
                print(f"[!] Attempt {attempt} POST profile save failed: {e}")
                time.sleep(2)

        print(f"[+] SUCCESS: Profile created! Public URL: {public_profile_url}")

        return {
            "success": True,
            "username": username,
            "email": email,
            "job_title": job_title,
            "public_profile_url": public_profile_url,
            "description": description_content,
            "error": None
        }

    except Exception as e:
        print(f"[-] Error creating profile for '{job_title}': {e}")
        return {
            "success": False,
            "job_title": job_title,
            "public_profile_url": None,
            "error": str(e)
        }
    finally:
        # Logout / clear session cookies for fresh next run
        try:
            session.get(LOGOUT_URL, headers=HEADERS, timeout=10)
        except:
            pass
        session.close()


def create_single_profile_playwright(job_title: str, openrouter_key: str = DEFAULT_OPENROUTER_KEY) -> dict:
    """
    Creates a new account in a VISIBLE Playwright browser (headless=False)
    without killing or closing any existing user browser windows!
    """
    from playwright.sync_api import sync_playwright

    try:
        with sync_playwright() as p:
            print("[*] Launching VISIBLE browser (headless=False) without closing user's Chrome...")
            browser = p.chromium.launch(headless=False, args=["--start-maximized"])
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
                no_viewport=True
            )
            page = context.new_page()

            print("[*] Navigating to https://hireandwire.com/login-register/...")
            page.goto(LOGIN_REGISTER_URL, wait_until="domcontentloaded", timeout=60000)

            reg_tab = page.locator("a[href='#register'], .register-tab").first
            if reg_tab.count() > 0:
                reg_tab.click()
                page.wait_for_timeout(1000)

            rand_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
            username = f"candidate_{rand_str}"
            email = f"candidate_{rand_str}@gmail.com"
            password = f"Pass_{rand_str}#99"

            print(f"[*] Registering user: {username} ({email})...")
            page.locator("form.register-form input[name='username']").first.fill(username)
            page.locator("form.register-form input[name='email']").first.fill(email)
            page.locator("form.register-form input[name='password']").first.fill(password)
            page.locator("form.register-form input[name='confirmpassword']").first.fill(password)

            terms_cb = page.locator("form.register-form input[name='terms_and_conditions']").first
            if terms_cb.count() > 0:
                terms_cb.check()

            print("[*] Submitting Register form...")
            submit_btn = page.locator("form.register-form input[type='submit'], form.register-form button[type='submit']").first
            submit_btn.click()
            page.wait_for_timeout(4000)

            print("[*] Navigating to https://hireandwire.com/profile/...")
            page.goto(PROFILE_URL, wait_until="domcontentloaded", timeout=60000)

            print(f"[*] Generating content for '{job_title}'...")
            raw_content = generate_waiver_body_content(job_title, api_key=openrouter_key)
            
            clean_desc = re.sub(r'<p[^>]*>', '', raw_content).replace('</p>', '\n\n').strip()
            clean_desc = re.sub(r'\+1\s*877\s*848\s*5082', '+1 877-848-5082', clean_desc)
            clean_desc = re.sub(r'\+1\s*888\s*308\s*7172', '+1 888 308 7172', clean_desc)
            phone_fmt = "(+1 877-848-5082 [US/OT] and +1 888 308 7172 [US/OT] )"
            formatted_desc = clean_desc.replace("+1 877-848-5082", phone_fmt).replace("+1 888 308 7172", phone_fmt)
            formatted_desc = re.sub(r'(\(\+1 877-848-5082 \[US/OT\] and \+1 888 308 7172 \[US/OT\] \)\s*)+', r'\1 ', formatted_desc)

            print(f"[*] Filling Full Name / Header Title field (_candidate_title) with '{job_title}' (Matching Image 2)...")
            title_input = page.locator("input[name='_candidate_title'], input#_candidate_title").first
            if title_input.count() > 0:
                title_input.fill(job_title)

            print(f"[*] Filling Job Title field (_candidate_job_title) with '{job_title}'...")
            job_title_input = page.locator("input[name='_candidate_job_title'], input#_candidate_job_title").first
            if job_title_input.count() > 0:
                job_title_input.fill(job_title)

            print("[*] Filling Description field (_candidate_description) & syncing to TinyMCE editor...")
            desc_area = page.locator("textarea[name='_candidate_description'], textarea#_candidate_description").first
            if desc_area.count() > 0:
                desc_area.fill(formatted_desc)

            # Sync content directly into TinyMCE WYSIWYG Editor iframe
            page.evaluate("""(desc) => {
                if (window.tinymce && window.tinymce.get('_candidate_description')) {
                    window.tinymce.get('_candidate_description').setContent(desc);
                }
                const el = document.querySelector('#_candidate_description');
                if (el) { el.value = desc; }
            }""", formatted_desc)

            page.wait_for_timeout(1000)

            print("[*] Clicking 'Save Profile' button at the bottom of fields...")
            save_btn = page.locator("input[name='submit-cmb-profile'], button:has-text('Save Profile')").first
            if save_btn.count() > 0:
                save_btn.scroll_into_view_if_needed()
                save_btn.click()
                page.wait_for_timeout(5000)

            public_profile_url = f"{SITE_URL}/candidate/{username.replace('_', '-')}/"
            print(f"[+] SUCCESS! Candidate Public Profile URL: {public_profile_url}")

            logout_link = page.locator("a:has-text('Logout'), a[href*='action=logout']").first
            if logout_link.count() > 0:
                logout_link.click()
                page.wait_for_timeout(2000)

            browser.close()
            return {
                "success": True,
                "username": username,
                "email": email,
                "job_title": job_title,
                "public_profile_url": public_profile_url,
                "description": formatted_desc,
                "error": None
            }

    except Exception as e:
        print(f"[-] Playwright Error: {e}")
        return {
            "success": False,
            "job_title": job_title,
            "public_profile_url": None,
            "error": str(e)
        }


def batch_create_profiles(job_titles: List[str], openrouter_key: str = DEFAULT_OPENROUTER_KEY, start_index: int = 1, visible_browser: bool = False) -> Generator[dict, None, None]:
    """
    GENERATOR: Batch creates hireandwire candidate profiles for each job title.
    Supports both visible browser mode (Playwright) and fast API mode.
    Yields each result immediately upon completion for real-time UI streaming.
    Logout is called automatically between runs.
    """
    start_idx = max(1, start_index) - 1
    titles_to_process = job_titles[start_idx:]

    for idx, title in enumerate(titles_to_process, start=start_idx + 1):
        clean_title = title.strip()
        if not clean_title:
            continue
        print(f"\n==================================================")
        print(f"[*] Processing Profile ({idx}/{len(job_titles)}): '{clean_title}'")
        print(f"==================================================")

        if visible_browser:
            res = create_single_profile_playwright(clean_title, openrouter_key=openrouter_key)
        else:
            res = create_single_profile(clean_title, openrouter_key=openrouter_key)

        yield res
        time.sleep(1)

