import asyncio
import os
import sys
import time
import re
from playwright.async_api import async_playwright

env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
if os.path.exists(env_path):
    try:
        with open(env_path, "r", encoding="utf-8") as _ef:
            for _line in _ef:
                _line = _line.strip()
                if _line and not _line.startswith("#") and "=" in _line:
                    _k, _v = _line.split("=", 1)
                    if _k.strip() not in os.environ:
                        os.environ[_k.strip()] = _v.strip()
    except Exception:
        pass

def safe_print(*args, **kwargs):
    try:
        flush = kwargs.pop("flush", True)
        msg = " ".join(str(a) for a in args)
        clean_msg = msg.encode("ascii", errors="replace").decode("ascii")
        sys.stdout.write(clean_msg + "\n")
        if flush:
            sys.stdout.flush()
    except Exception:
        pass

print = safe_print

URL = os.environ.get("PROBOARDS_TARGET_URL", "https://youtubetvsupport.proboards.com/thread/new/1")
DEFAULT_LOGIN_URL = os.environ.get("PROBOARDS_LOGIN_URL", "https://login.proboards.com/login/7489353/1")
DEFAULT_USERNAME = os.environ.get("PROBOARDS_USERNAME", "zorvik@cheapermail.com")
DEFAULT_PASSWORD = os.environ.get("PROBOARDS_PASSWORD", "Rohit@123321#")
DEFAULT_GROQ_KEY = os.environ.get("GROQ_API_KEY", "")
DEFAULT_PHONE = "+1 888 308 7172"

def extract_phone_tag(title: str, default_phone: str = DEFAULT_PHONE) -> str:
    m = re.search(r'(\+?1[\s\^\-_.]*\(?\d{3}\)?[\s\^\-_.]*\d{3}[\s\^\-_.]*\d{4})', title)
    raw = m.group(1).strip() if m else default_phone
    # Standardize to 1 888 308 7172(USA/CA)
    digits = re.sub(r'\D', '', raw)
    if len(digits) == 11 and digits.startswith('1'):
        formatted = f"1 {digits[1:4]} {digits[4:7]} {digits[7:]}"
    elif len(digits) == 10:
        formatted = f"1 {digits[0:3]} {digits[3:6]} {digits[6:]}"
    else:
        formatted = "1 888 308 7172"
    return f"{formatted}(USA/CA)"

def extract_phone_from_title(title: str, default_phone: str = DEFAULT_PHONE) -> str:
    return extract_phone_tag(title, default_phone)

FORMAT_BLUEPRINTS = [
    {
        "style_name": "OPERATIONAL TROUBLESHOOTING & ACCOUNT TRIAGE",
        "sections": [
            "SECTION 1: COMPREHENSIVE ARCHITECTURAL OVERVIEW AND DIAGNOSTIC TRIAGE. Explain the exact mechanism of billing, why users experience unexpected recurring holds or difficulty canceling, and deep technical context. Write approximately 750 words in plain text with absolutely NO asterisks or markdown.",
            "SECTION 2: COMPLETE STEP-BY-STEP ADMINISTRATIVE RESOLUTION. Provide exhaustive, step-by-step procedures covering web browser portal settings, desktop application menus, and mobile device settings. Write approximately 750 words in plain text with absolutely NO asterisks or markdown.",
            "SECTION 3: ERROR HANDLING, MERCHANT REFUND STANDARDS, AND INVOICE RECONCILIATION. Cover edge cases, refund eligibility windows, credit card charge disputes, and transaction reference numbers. Write approximately 750 words in plain text with absolutely NO asterisks or markdown.",
            "SECTION 4: VERIFICATION AUDIT AND PERMANENT SECURITY HARDENING. Detail how to confirm the subscription is officially canceled, purging cached browser tokens, and ongoing protection. Write approximately 750 words in plain text with absolutely NO asterisks or markdown."
        ]
    },
    {
        "style_name": "EXECUTIVE FIELD DIRECTIVE & BILLING REMEDIATION",
        "sections": [
            "PHASE 1: INCIDENT SCOPE AND INITIAL DIAGNOSTIC AUDITING. Deep-dive into account authorization states, license renewal schedules, and root causes of subscription locking. Write approximately 750 words in plain text with absolutely NO asterisks or markdown.",
            "PHASE 2: DIRECT MANUAL DEACTIVATION PROTOCOLS. Detail explicit button clicks, account management navigation, email verification routines, and credential troubleshooting. Write approximately 750 words in plain text with absolutely NO asterisks or markdown.",
            "PHASE 3: TRANSACTION CHARGE DISPUTES AND REFUND RESOLUTION. Provide detailed guidance on bank charge disputes, vendor contact escalation, and resolving recurring payment agreements. Write approximately 750 words in plain text with absolutely NO asterisks or markdown.",
            "PHASE 4: POST-RESOLUTION VERIFICATION AND PERMANENT DEACTIVATION. Guide users through verifying their zero balance status, removing stored billing cards, and final system cleanup. Write approximately 750 words in plain text with absolutely NO asterisks or markdown."
        ]
    },
    {
        "style_name": "TECHNICAL KNOWLEDGEBASE COMPENDIUM",
        "sections": [
            "MODULE 1: SERVICE FOUNDATIONS AND USER ACCESSIBILITY CONTEXT. Provide deep technical and operational background for the topic, analyzing software licenses and subscriber dashboards. Write approximately 750 words in plain text with absolutely NO asterisks or markdown.",
            "MODULE 2: EXHAUSTIVE STEP-BY-STEP ACTIONABLE PROCEDURES. Provide comprehensive sequential instructions for modifying plan settings, disabling recurring renewals, and closing accounts. Write approximately 750 words in plain text with absolutely NO asterisks or markdown.",
            "MODULE 3: FREQUENTLY ENCOUNTERED IMPEDIMENTS AND ADVANCED TROUBLESHOOTING. Answer common user concerns, address missing cancellation links, and resolve payment gateway blocks. Write approximately 750 words in plain text with absolutely NO asterisks or markdown.",
            "MODULE 4: COMPLIANCE CONFIRMATION AND ESCALATION SUPPORT. Explain how to document transaction receipts, verify final termination emails, and contact customer assistance. Write approximately 750 words in plain text with absolutely NO asterisks or markdown."
        ]
    },
    {
        "style_name": "SUBSCRIBER SELF-SERVICE RESOLUTION PLAYBOOK",
        "sections": [
            "CHAPTER 1: SYSTEM ENVIRONMENT AUDIT AND ENTITLEMENT MAPPING. Provide a thorough initial assessment of the user profile, active software packages, and subscription renewal cycles. Write approximately 750 words in plain text with absolutely NO asterisks or markdown.",
            "CHAPTER 2: END-TO-END DE-ENROLLMENT AND SETTINGS ADJUSTMENT. Detail comprehensive steps across mobile applications, web portals, and third-party app stores to revoke access and turn off automatic billing. Write approximately 750 words in plain text with absolutely NO asterisks or markdown.",
            "CHAPTER 3: EDGE CASE RESOLUTION AND DISPUTE REMEDIATION. Address account lockout issues, forgotten credentials, two-factor authentication roadblocks, and banking charge reversals. Write approximately 750 words in plain text with absolutely NO asterisks or markdown.",
            "CHAPTER 4: FINAL AUDIT, DOCUMENTATION RETENTION, AND AUDIT TRAIL. Explain how to capture proof of cancellation, confirm no secondary charges occur, and secure related accounts. Write approximately 750 words in plain text with absolutely NO asterisks or markdown."
        ]
    },
    {
        "style_name": "ENTERPRISE LICENSING & SERVICE DECOMMISSION PROTOCOL",
        "sections": [
            "STAGE 1: ASSET INVENTORY AND CONTRACTUAL BOUNDARY REVIEW. Detail the technical scope of the service agreement, recurring payment terms, and vendor provisioning channels. Write approximately 750 words in plain text with absolutely NO asterisks or markdown.",
            "STAGE 2: SYSTEMATIC DECOMMISSIONING AND LICENSE REVOCATION. Provide complete manual configuration procedures to safely disable active seats, unlink payment methods, and terminate automatic renewals. Write approximately 750 words in plain text with absolutely NO asterisks or markdown.",
            "STAGE 3: FINANCIAL RECONCILIATION AND REFUND DISPUTES. Provide actionable instructions for requesting prorated refunds, filing merchant charge disputes, and handling unresponsive support tickets. Write approximately 750 words in plain text with absolutely NO asterisks or markdown.",
            "STAGE 4: TERMINATION VERIFICATION AND OPERATIONAL HYGIENE. Outline post-cancellation checks, confirming account zero balance status, and cleaning device registry entries. Write approximately 750 words in plain text with absolutely NO asterisks or markdown."
        ]
    },
    {
        "style_name": "CUSTOMER ADVOCACY & BILLING AUDIT DOSSIER",
        "sections": [
            "PART 1: CASE EVALUATION AND BILLING CYCLE ANATOMY. Analyze recurring fee structures, subscription terms of service, and why unauthorized or unexpected renewal fees occur. Write approximately 750 words in plain text with absolutely NO asterisks or markdown.",
            "PART 2: ACTIONABLE ACCOUNT CLOSURE WORKFLOW. Offer an exhaustive, step-by-step navigational manual to locate hidden deactivation toggles, cancel subscriptions, and close billing profiles. Write approximately 750 words in plain text with absolutely NO asterisks or markdown.",
            "PART 3: ADVANCED DISPUTE ESCALATION AND CHARGEBACK STRATEGY. Guide the user through payment provider escalation, credit card charge dispute procedures, and consumer advocacy protocols. Write approximately 750 words in plain text with absolutely NO asterisks or markdown.",
            "PART 4: PERMANENT TERMINATION CHECKLIST AND IDENTITY PROTECTION. Provide a rigorous closing checklist ensuring all data is erased, tokens are cleared, and no further billing attempts can succeed. Write approximately 750 words in plain text with absolutely NO asterisks or markdown."
        ]
    }
]

def interleave_phone_every_8_words(text: str, phone_tag: str) -> str:
    """Interleaves the exact phone tag every 8 words across all body paragraphs."""
    lines = text.split("\n")
    out_lines = []
    
    for line in lines:
        stripped = line.strip()
        # Keep section headers clean without phone stuffing
        if not stripped or stripped.startswith("SECTION") or stripped.startswith("PHASE") or stripped.startswith("MODULE") or stripped.startswith("PART") or stripped.isupper():
            out_lines.append(line)
            continue
            
        words = line.split()
        if len(words) < 4:
            out_lines.append(line)
            continue
            
        res_words = []
        for i, w in enumerate(words, 1):
            res_words.append(w)
            if i % 8 == 0:
                res_words.append(phone_tag)
        out_lines.append(" ".join(res_words))
        
    return "\n\n".join(out_lines)

def generate_proboards_content(
    title: str,
    phone: str = None,
    groq_api_key: str = DEFAULT_GROQ_KEY,
    on_progress = None
) -> str:
    """
    Generates 3000+ words of 100% unique, dynamic-format content using Groq AI.
    - Strictly NO markdown asterisks (**) anywhere.
    - Dynamic architecture (different styles/headings per title).
    - Interleaves exact phone tag (e.g. '1 888 308 7172(USA/CA)') after every 8 words.
    - Optimized for high-speed generation with real-time progress callbacks.
    """
    import random
    phone_tag = extract_phone_tag(title, default_phone=phone or DEFAULT_PHONE)
    blueprint = random.choice(FORMAT_BLUEPRINTS)
    
    print(f"\n[*] Content Architecture Selected: {blueprint['style_name']}", flush=True)
    print(f"[*] Phone Tag for Interleaving: {phone_tag}", flush=True)
    
    section_texts = []
    total_sections = len(blueprint["sections"])
    if groq_api_key:
        try:
            import groq
            client = groq.Groq(api_key=groq_api_key)
            
            for s_idx, sec_prompt in enumerate(blueprint["sections"], 1):
                if on_progress:
                    try:
                        on_progress(s_idx, total_sections, f"Writing Part {s_idx}/{total_sections}...")
                    except Exception:
                        pass
                print(f"[*] Generating Part {s_idx}/{total_sections} with Groq AI...", flush=True)
                system_prompt = (
                    "You are a principal technical author and systems architect. "
                    "Write exhaustive, highly authentic, deep technical and instructional prose. "
                    "STRICT FORMATTING RULE: Write ONLY plain text. Absolutely NEVER use asterisks (** or *), "
                    "never use markdown bold or italics, never use hashtags. Format headings with pure uppercase text."
                )
                user_msg = (
                    f"Topic Title: {title}\n"
                    f"Task: {sec_prompt}\n"
                    f"Include deep, realistic step-by-step guidance, button names, menus, troubleshooting tips, and realistic technical insights. "
                    f"Write approximately 700 to 750 words for this section."
                )
                
                # Attempt primary fast generation with max_tokens cap to prevent runaway token delays
                try:
                    resp = client.chat.completions.create(
                        model="openai/gpt-oss-120b",
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_msg}
                        ],
                        max_tokens=950,
                        temperature=0.82
                    )
                    raw_sec = resp.choices[0].message.content.strip()
                except Exception as api_err:
                    print(f"[!] Groq primary error, retrying with fallback model: {api_err}", flush=True)
                    time.sleep(1)
                    resp = client.chat.completions.create(
                        model="openai/gpt-oss-20b",
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_msg}
                        ],
                        max_tokens=950,
                        temperature=0.82
                    )
                    raw_sec = resp.choices[0].message.content.strip()

                # Strip any stray asterisks or markdown syntax
                clean_sec = re.sub(r'[\*#_`]', '', raw_sec)
                section_texts.append(clean_sec)
                
        except Exception as ge:
            print(f"[!] Groq generation note: {ge}", flush=True)

    if not section_texts:
        # Fallback to local structured generator
        print("[!] Generating via fallback expanded generator...", flush=True)
        from unique_content_engine import generate_unique_description
        base = generate_unique_description(title=title, tfn=phone_tag)
        section_texts = [re.sub(r'[\*#_`]', '', base)]

    combined_text = "\n\n".join(section_texts)
    # Strictly strip all asterisks and markdown symbols
    clean_combined = re.sub(r'[\*#_`]', '', combined_text)
    # Normalize unicode punctuation
    clean_combined = clean_combined.replace('\u2011', '-').replace('\u2013', '-').replace('\u2014', '-').replace('\u2018', "'").replace('\u2019', "'").replace('\u201c', '"').replace('\u201d', '"')
    
    # Interleave phone tag every 8 words
    final_content = interleave_phone_every_8_words(clean_combined, phone_tag)
    
    total_words = len(final_content.split())
    print(f"[+] Generated 100% Unique Content: {total_words} words, NO asterisks, phone interleaved every 8 words!\n", flush=True)
    return final_content

async def create_proboards_thread(
    guest_name: str = "Alex Parker",
    subject: str = "Inspirational Stories and Daily Motivation for Teens",
    content: str = None,
    login_url: str = DEFAULT_LOGIN_URL,
    username: str = DEFAULT_USERNAME,
    password: str = DEFAULT_PASSWORD,
    target_url: str = URL,
    timeout_sec: int = 180,
    groq_api_key: str = DEFAULT_GROQ_KEY
) -> dict:
    """
    Opens a visible browser window, logs into ProBoards if credentials provided,
    fills Subject and AI Content, clicks Create Thread, auto-checks TOS/captcha,
    and waits for publication. Returns dict with success status and thread url.
    """
    if not content:
        print("[*] Generating unique content via Groq AI...", flush=True)
        content = generate_proboards_content(title=subject, groq_api_key=groq_api_key)

    print("\n" + "="*60, flush=True)
    print("🚀 [PROBOARDS BOT] Launching visible browser...", flush=True)
    if username and password:
        print(f"🔑 Account    : {username}", flush=True)
        print(f"🌐 Login URL  : {login_url}", flush=True)
    else:
        print(f"👤 Guest Name : {guest_name}", flush=True)
    print(f"📝 Target URL : {target_url}", flush=True)
    print(f"📌 Subject    : {subject}", flush=True)
    print("="*60 + "\n", flush=True)

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
            viewport=None,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        try:
            # 1. Login if credentials are provided
            if login_url and username and password:
                print(f"[*] Navigating to Login Page: {login_url}...", flush=True)
                await page.goto(login_url, wait_until="commit", timeout=60000)
                await page.wait_for_timeout(3000)

                email_input = page.locator("input[name='email']")
                if await email_input.count() > 0:
                    print("[*] Entering credentials...", flush=True)
                    await email_input.fill("")
                    await email_input.type(username, delay=35)
                    await page.wait_for_timeout(400)

                    pass_input = page.locator("input[name='password']")
                    await pass_input.fill("")
                    await pass_input.type(password, delay=35)
                    await page.wait_for_timeout(400)

                    print("[*] Submitting login...", flush=True)
                    submit_login = page.locator("input[type='submit'], button[type='submit'], input[name='continue']").first
                    await submit_login.click()
                    await page.wait_for_timeout(4000)
                    print(f"[+] Login redirect completed. Current URL: {page.url}", flush=True)

            # 2. Navigate to Target Thread Page
            print(f"[*] Navigating to {target_url}...", flush=True)
            await page.goto(target_url, wait_until="commit", timeout=60000)
            await page.wait_for_timeout(3000)

            # 3. Fill Guest Name if input is present and visible
            guest_input = page.locator("input[name='created_by_guest_name']")
            if await guest_input.count() > 0 and await guest_input.is_visible():
                await guest_input.click()
                await page.wait_for_timeout(300)
                await guest_input.fill("")
                await guest_input.type(guest_name, delay=40)
                print(f"[+] Guest Name filled: {guest_name}", flush=True)
                await page.wait_for_timeout(1000)

            # 4. Fill Subject with human typing pace
            subject_input = page.locator("input[name='subject']")
            await subject_input.wait_for(state="visible", timeout=20000)
            await subject_input.click()
            await page.wait_for_timeout(500)
            await subject_input.fill("")
            await subject_input.type(subject, delay=25)
            print(f"[+] Subject filled: {subject}", flush=True)
            await page.wait_for_timeout(1500)

            # 5. Fill Content in Visual Editor / Textarea
            content_html = "<p>" + content.replace("\n", "<br>") + "</p>"
            await page.evaluate(f"""() => {{
                // Set iframe body
                const iframe = document.querySelector('.editor.visual-editor iframe');
                if (iframe) {{
                    const doc = iframe.contentDocument || iframe.contentWindow.document;
                    doc.body.innerHTML = {repr(content_html)};
                    doc.body.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    doc.body.dispatchEvent(new Event('change', {{ bubbles: true }}));
                }}
                // Set textarea
                const ta = document.querySelector('textarea.wysiwyg-textarea');
                if (ta) {{
                    ta.value = {repr(content)};
                    ta.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    ta.dispatchEvent(new Event('change', {{ bubbles: true }}));
                }}
            }}""")
            print("[+] Content filled in editor!", flush=True)
            
            # Pause 2 seconds so user can see filled form
            print("[*] Form filled. Waiting 2 seconds before clicking Create Thread...", flush=True)
            await page.wait_for_timeout(2500)

            # 6. Click Create Thread
            print("[*] Clicking 'Create Thread'...", flush=True)
            submit_btn = page.locator("input[type='submit'][value='Create Thread'], input[name='post']").first
            await submit_btn.click()

            # 7. Check for Human Verification dialog if present
            try:
                dialog = page.locator(".ui-dialog:has-text('Please prove you are human')")
                if await dialog.count() > 0:
                    await dialog.wait_for(state="visible", timeout=10000)
                    print("[+] Human verification dialog popped up!", flush=True)
                    await page.wait_for_timeout(1000)

                    tos_cb = dialog.locator("input[name='tos_checkbox']")
                    if await tos_cb.count() > 0:
                        await tos_cb.check()
                        print("[+] Checked Terms of Service automatically!", flush=True)
                    await page.wait_for_timeout(1000)

                    try:
                        recaptcha_frame = page.frame_locator("iframe[title='reCAPTCHA']")
                        anchor = recaptcha_frame.locator("#recaptcha-anchor")
                        if await anchor.count() > 0:
                            await anchor.click()
                            print("[+] Clicked reCAPTCHA checkbox automatically!", flush=True)
                    except Exception as e:
                        print(f"[!] Captcha frame click note: {e}", flush=True)
            except Exception as de:
                print(f"[*] Verification dialog note: {de}", flush=True)

            print("\n" + "*"*60, flush=True)
            print("👉 [ARAM SE KIJIYE] Browser open hai. Captcha solve karein agar hai aur Submit dabayein.", flush=True)
            print(f"👉 Bot araam se wait kar raha hai (Max timeout: {timeout_sec}s).", flush=True)
            print("*"*60 + "\n", flush=True)

            created_url = None

            # Polling loop: plenty of time for human solving/redirect
            for second in range(timeout_sec):
                await page.wait_for_timeout(1000)

                # Check if URL transitioned to thread
                curr_url = page.url
                if "/thread/" in curr_url and "/thread/new/" not in curr_url:
                    created_url = curr_url
                    print(f"\n[SUCCESS] Thread Created! URL: {created_url}", flush=True)
                    break

                if second % 15 == 0 and second > 0:
                    print(f"[*] Waiting for captcha / publish... ({second}/{timeout_sec}s)", flush=True)

            if not created_url and "/thread/" in page.url and "/thread/new/" not in page.url:
                created_url = page.url

            if created_url:
                with open("proboards_threads.txt", "a", encoding="utf-8") as f:
                    f.write(f"{created_url}\n")
                print("\n" + "="*60, flush=True)
                print(f"✅ THREAD CREATED SUCCESSFULLY: {created_url}", flush=True)
                print("="*60 + "\n", flush=True)
                print("[*] Thread published! Keeping window visible for 6 seconds...", flush=True)
                await page.wait_for_timeout(6000)
                await browser.close()
                return {"success": True, "url": created_url}
            else:
                print(f"[!] Timeout reached or thread not published. Current URL: {page.url}", flush=True)
                await browser.close()
                return {"success": False, "url": page.url, "error": "Timeout or not published"}

        except Exception as err:
            print(f"[!] Error: {err}", flush=True)
            try:
                await browser.close()
            except Exception:
                pass
            return {"success": False, "error": str(err)}

def run_proboards_sync(
    guest_name: str = "Alex Parker",
    subject: str = "Inspirational Stories and Daily Motivation for Teens",
    content: str = None,
    login_url: str = DEFAULT_LOGIN_URL,
    username: str = DEFAULT_USERNAME,
    password: str = DEFAULT_PASSWORD,
    target_url: str = URL,
    timeout_sec: int = 180,
    groq_api_key: str = DEFAULT_GROQ_KEY
) -> dict:
    """Synchronous helper for calling from Streamlit or scripts"""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                return pool.submit(asyncio.run, create_proboards_thread(
                    guest_name, subject, content, login_url, username, password, target_url, timeout_sec, groq_api_key
                )).result()
        else:
            return loop.run_until_complete(create_proboards_thread(
                guest_name, subject, content, login_url, username, password, target_url, timeout_sec, groq_api_key
            ))
    except Exception:
        return asyncio.run(create_proboards_thread(
            guest_name, subject, content, login_url, username, password, target_url, timeout_sec, groq_api_key
        ))

async def batch_post_proboards_threads(
    titles: list,
    guest_name: str = "Leo Mendis",
    login_url: str = DEFAULT_LOGIN_URL,
    username: str = DEFAULT_USERNAME,
    password: str = DEFAULT_PASSWORD,
    target_url: str = URL,
    timeout_sec: int = 180,
    groq_api_key: str = DEFAULT_GROQ_KEY,
    phone: str = DEFAULT_PHONE,
    min_delay_sec: float = 10.0,
    max_delay_sec: float = 15.0,
    output_file: str = "proboards_threads.txt",
    on_progress = None
) -> list:
    """
    Opens browser ONCE, logs into ProBoards ONCE, and posts all titles sequentially
    in the same browser session with a random 10-15s delay between posts.
    """
    import random
    unique_titles = list(dict.fromkeys([t.strip() for t in titles if t.strip()]))
    total = len(unique_titles)
    results = []

    if total == 0:
        return results

    print("\n" + "="*60, flush=True)
    print(f"🚀 [PROBOARDS BATCH RUNNER] Starting single-session posting for {total} title(s)...", flush=True)
    if username and password:
        print(f"🔑 Account    : {username} (One-Time Login)", flush=True)
        print(f"🌐 Login URL  : {login_url}", flush=True)
    print(f"📝 Target URL : {target_url}", flush=True)
    print(f"⏱️ Inter-post delay: {min_delay_sec}s - {max_delay_sec}s", flush=True)
    print("="*60 + "\n", flush=True)

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
            viewport=None,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        try:
            # 1. ONE-TIME LOGIN
            if login_url and username and password:
                print(f"[*] [ONE-TIME LOGIN] Navigating to Login Page: {login_url}...", flush=True)
                await page.goto(login_url, wait_until="commit", timeout=60000)
                await page.wait_for_timeout(3000)

                email_input = page.locator("input[name='email']")
                if await email_input.count() > 0:
                    print(f"[*] Entering credentials for {username}...", flush=True)
                    await email_input.fill("")
                    await email_input.type(username, delay=35)
                    await page.wait_for_timeout(400)

                    pass_input = page.locator("input[name='password']")
                    await pass_input.fill("")
                    await pass_input.type(password, delay=35)
                    await page.wait_for_timeout(400)

                    print("[*] Submitting login form...", flush=True)
                    submit_login = page.locator("input[type='submit'], button[type='submit'], input[name='continue']").first
                    await submit_login.click()
                    await page.wait_for_timeout(5000)
                    print(f"[+] One-time login completed! Logged-in URL: {page.url}\n", flush=True)

            # 2. SEQUENTIAL POSTING IN THE SAME BROWSER SESSION
            for idx, title in enumerate(unique_titles, start=1):
                print("="*60, flush=True)
                print(f"📌 [{idx}/{total}] Processing Title: {title}", flush=True)
                print("="*60, flush=True)

                if on_progress:
                    try:
                        on_progress(idx, total, title, "generating_content", None)
                    except Exception:
                        pass

                # Generate unique content with Groq AI
                print("[*] Generating unique 2500+ word content with Groq AI...", flush=True)
                try:
                    content = generate_proboards_content(title=title, phone=phone, groq_api_key=groq_api_key)
                except Exception as ce:
                    print(f"[!] Content gen error, using structured fallback: {ce}", flush=True)
                    content = f"Hello everyone,\n\nI wanted to open a detailed discussion regarding '{title}'. For immediate support call {phone}."

                if on_progress:
                    try:
                        on_progress(idx, total, title, "opening_form", None)
                    except Exception:
                        pass

                # Navigate directly to target new thread URL
                print(f"[*] Navigating to new thread form: {target_url}...", flush=True)
                await page.goto(target_url, wait_until="commit", timeout=60000)
                await page.wait_for_timeout(2500)

                # Fill Guest Name if visible
                guest_input = page.locator("input[name='created_by_guest_name']")
                if await guest_input.count() > 0 and await guest_input.is_visible():
                    await guest_input.click()
                    await page.wait_for_timeout(200)
                    await guest_input.fill("")
                    await guest_input.type(guest_name, delay=35)
                    await page.wait_for_timeout(500)

                # Fill Subject
                subject_input = page.locator("input[name='subject']")
                await subject_input.wait_for(state="visible", timeout=20000)
                await subject_input.click()
                await page.wait_for_timeout(300)
                await subject_input.fill("")
                await subject_input.type(title, delay=25)
                print(f"[+] Subject filled: {title}", flush=True)
                await page.wait_for_timeout(1000)

                # Fill Content in Visual Editor / Textarea
                content_html = "<p>" + content.replace("\n", "<br>") + "</p>"
                await page.evaluate(f"""() => {{
                    const iframe = document.querySelector('.editor.visual-editor iframe');
                    if (iframe) {{
                        const doc = iframe.contentDocument || iframe.contentWindow.document;
                        doc.body.innerHTML = {repr(content_html)};
                        doc.body.dispatchEvent(new Event('input', {{ bubbles: true }}));
                        doc.body.dispatchEvent(new Event('change', {{ bubbles: true }}));
                    }}
                    const ta = document.querySelector('textarea.wysiwyg-textarea');
                    if (ta) {{
                        ta.value = {repr(content)};
                        ta.dispatchEvent(new Event('input', {{ bubbles: true }}));
                        ta.dispatchEvent(new Event('change', {{ bubbles: true }}));
                    }}
                }}""")
                print("[+] Content filled into editor!", flush=True)
                await page.wait_for_timeout(2000)

                # Click Create Thread
                print("[*] Clicking 'Create Thread'...", flush=True)
                submit_btn = page.locator("input[type='submit'][value='Create Thread'], input[name='post']").first
                await submit_btn.click()

                # Check for Human Verification dialog if present
                try:
                    dialog = page.locator(".ui-dialog:has-text('Please prove you are human')")
                    if await dialog.count() > 0:
                        await dialog.wait_for(state="visible", timeout=10000)
                        print("[+] Human verification dialog popped up!", flush=True)
                        await page.wait_for_timeout(1000)
                        tos_cb = dialog.locator("input[name='tos_checkbox']")
                        if await tos_cb.count() > 0:
                            await tos_cb.check()
                            print("[+] Checked Terms of Service automatically!", flush=True)
                        await page.wait_for_timeout(1000)
                        try:
                            recaptcha_frame = page.frame_locator("iframe[title='reCAPTCHA']")
                            anchor = recaptcha_frame.locator("#recaptcha-anchor")
                            if await anchor.count() > 0:
                                await anchor.click()
                                print("[+] Clicked reCAPTCHA checkbox automatically!", flush=True)
                        except Exception as e:
                            pass
                except Exception:
                    pass

                print(f"[*] Waiting for thread publish... (Timeout: {timeout_sec}s)", flush=True)
                created_url = None
                for second in range(timeout_sec):
                    await page.wait_for_timeout(1000)
                    curr_url = page.url
                    if "/thread/" in curr_url and "/thread/new/" not in curr_url:
                        created_url = curr_url
                        break
                    if second % 15 == 0 and second > 0:
                        print(f"[*] Polling publish status... ({second}/{timeout_sec}s)", flush=True)

                if created_url:
                    print(f"✅ [SUCCESS {idx}/{total}] Thread Created: {created_url}\n", flush=True)
                    if output_file:
                        try:
                            with open(output_file, "a", encoding="utf-8") as out_f:
                                out_f.write(f"{created_url}\n")
                        except Exception:
                            pass
                    results.append({"title": title, "success": True, "url": created_url})
                    if on_progress:
                        try:
                            on_progress(idx, total, title, "success", created_url)
                        except Exception:
                            pass
                else:
                    print(f"❌ [FAILED {idx}/{total}] Could not publish: {page.url}\n", flush=True)
                    results.append({"title": title, "success": False, "error": "Timeout or not published", "url": page.url})
                    if on_progress:
                        try:
                            on_progress(idx, total, title, "failed", None)
                        except Exception:
                            pass

                # If there are more titles to post, wait a random 10 to 15 seconds!
                if idx < total:
                    delay = random.uniform(min_delay_sec, max_delay_sec)
                    print(f"⏳ [COOLDOWN] Waiting {delay:.1f}s before next post in the same session...\n", flush=True)
                    if on_progress:
                        try:
                            on_progress(idx, total, title, "cooldown", delay)
                        except Exception:
                            pass
                    await page.wait_for_timeout(int(delay * 1000))

            print("\n" + "="*60, flush=True)
            print(f"🎉 All {total} threads processed! Closing browser session.", flush=True)
            print("="*60 + "\n", flush=True)
            await page.wait_for_timeout(2000)

        finally:
            await browser.close()

    return results

def run_proboards_batch_sync(
    titles: list,
    guest_name: str = "Leo Mendis",
    login_url: str = DEFAULT_LOGIN_URL,
    username: str = DEFAULT_USERNAME,
    password: str = DEFAULT_PASSWORD,
    target_url: str = URL,
    timeout_sec: int = 180,
    groq_api_key: str = DEFAULT_GROQ_KEY,
    phone: str = DEFAULT_PHONE,
    min_delay_sec: float = 10.0,
    max_delay_sec: float = 15.0,
    output_file: str = "proboards_threads.txt",
    on_progress = None
) -> list:
    """Synchronous wrapper for batch_post_proboards_threads"""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                return pool.submit(asyncio.run, batch_post_proboards_threads(
                    titles, guest_name, login_url, username, password, target_url, timeout_sec, groq_api_key, phone, min_delay_sec, max_delay_sec, output_file, on_progress
                )).result()
        else:
            return loop.run_until_complete(batch_post_proboards_threads(
                titles, guest_name, login_url, username, password, target_url, timeout_sec, groq_api_key, phone, min_delay_sec, max_delay_sec, output_file, on_progress
            ))
    except Exception:
        return asyncio.run(batch_post_proboards_threads(
            titles, guest_name, login_url, username, password, target_url, timeout_sec, groq_api_key, phone, min_delay_sec, max_delay_sec, output_file, on_progress
        ))

if __name__ == "__main__":
    g_name = sys.argv[1] if len(sys.argv) > 1 else "Alex Parker"
    subj = sys.argv[2] if len(sys.argv) > 2 else "Inspirational Stories and Daily Motivation for Shinobi"
    msg = sys.argv[3] if len(sys.argv) > 3 else None
    asyncio.run(create_proboards_thread(guest_name=g_name, subject=subj, content=msg))

