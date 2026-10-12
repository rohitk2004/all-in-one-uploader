import asyncio
import os
import sys
import time
import re
from playwright.async_api import async_playwright

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

DEFAULT_LOGIN_URL = "https://huggingface.co/login"
DEFAULT_USERNAME = "LunarStorm@purelymail.com"
DEFAULT_PASSWORD = "JameswarnertoUsa@321#321$321"
DEFAULT_TARGET_URL = "https://discuss.huggingface.co/c/intermediate/6"
DEFAULT_GROQ_KEY = os.environ.get("GROQ_API_KEY", "")
DEFAULT_PHONE = "+1 888 308 7172"

def extract_phone_tag(title: str, default_phone: str = DEFAULT_PHONE) -> str:
    m = re.search(r'(\+?1[\s\^\-_.]*\(?\d{3}\)?[\s\^\-_.]*\d{3}[\s\^\-_.]*\d{4})', title)
    raw = m.group(1).strip() if m else default_phone
    digits = re.sub(r'\D', '', raw)
    if len(digits) == 11 and digits.startswith('1'):
        formatted = f"1 {digits[1:4]} {digits[4:7]} {digits[7:]}"
    elif len(digits) == 10:
        formatted = f"1 {digits[0:3]} {digits[3:6]} {digits[6:]}"
    else:
        formatted = "1 888 308 7172"
    return f"{formatted}(USA/CA)"

def interleave_phone_every_8_words(text: str, phone_tag: str) -> str:
    """Interleaves the exact phone tag every 8 words across all body paragraphs."""
    lines = text.split("\n")
    out_lines = []
    
    for line in lines:
        stripped = line.strip()
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

def generate_huggingface_content(
    title: str,
    phone: str = None,
    groq_api_key: str = DEFAULT_GROQ_KEY
) -> str:
    """
    Generates ~300 words content with NO URLs/links and phone tag interleaved every 8 words.
    """
    phone_tag = extract_phone_tag(title, default_phone=phone or DEFAULT_PHONE)
    print(f"\n[*] Generating ~300 words content for topic: '{title}'...", flush=True)

    clean_text = ""
    if groq_api_key:
        try:
            import groq
            client = groq.Groq(api_key=groq_api_key)
            system_prompt = (
                "You are a technical community author on Hugging Face Discourse. "
                "Write clear, authentic, highly detailed plain text guidance for technical topics or software troubleshooting. "
                "STRICT FORMATTING RULES: "
                "1. Write plain text without markdown asterisks (**). "
                "2. DO NOT include any website URLs, web links, domain names, http, or https links anywhere in the content. "
                "3. Output approximately 300 words."
            )
            user_msg = (
                f"Topic Title: {title}\n"
                f"Task: Write a detailed discussion post with complete step-by-step instructions and resolution actions. "
                f"Do not include any URLs or links. Keep the word count around 300 words."
            )

            try:
                resp = client.chat.completions.create(
                    model="openai/gpt-oss-120b",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_msg}
                    ],
                    max_tokens=600,
                    temperature=0.8
                )
                raw_text = resp.choices[0].message.content.strip()
            except Exception:
                resp = client.chat.completions.create(
                    model="openai/gpt-oss-20b",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_msg}
                    ],
                    max_tokens=600,
                    temperature=0.8
                )
                raw_text = resp.choices[0].message.content.strip()

            clean_text = re.sub(r'[\*#_`]', '', raw_text)

        except Exception as ge:
            print(f"[!] Groq AI note: {ge}. Using fallback engine...", flush=True)

    if not clean_text:
        clean_text = (
            f"Detailed step-by-step instructions regarding {title}.\n\n"
            f"Managing account settings, auto-renewal options, and subscription details requires accessing your central account dashboard. "
            f"To ensure your service or subscription is updated correctly, begin by logging into your profile using your verified credentials. "
            f"Navigate directly to the Billing or Subscription Management section from your user profile icon in the upper right header.\n\n"
            f"Once inside the subscription overview panel, locate your active plan details. Select the option to turn off auto renewal or cancel recurring payments. "
            f"Follow the on-screen confirmation prompts to finalize the cancellation request. A confirmation notification or receipt email will be dispatched to your registered address. "
            f"Keep this receipt as proof of cancellation for your administrative and financial records.\n\n"
            f"If you face any issues, encounter missing options, or require a billing adjustment, reach out directly to customer support helpline. "
            f"Support representatives can verify your transaction ID, adjust your license entitlement, and ensure no further recurring charges occur."
        )

    # Clean markdown & strip all URLs/links
    clean_text = re.sub(r'[\*#_`]', '', clean_text)
    clean_text = re.sub(r'https?://\S+|www\.\S+', '', clean_text)
    clean_text = clean_text.replace('\u2011', '-').replace('\u2013', '-').replace('\u2014', '-').replace('\u2018', "'").replace('\u2019', "'").replace('\u201c', '"').replace('\u201d', '"')

    # Interleave phone tag every 8 words
    final_content = interleave_phone_every_8_words(clean_text, phone_tag)
    words = final_content.split()
    print(f"[+] Content generated ({len(words)} words, NO URLs) with phone '{phone_tag}' interleaved!", flush=True)
    return final_content

async def run_huggingface_multi_account_batch(
    titles: list,
    accounts: list,
    max_posts_per_account: int = 2,
    output_file: str = "huggingface_batch_links.txt",
    login_url: str = DEFAULT_LOGIN_URL,
    target_url: str = DEFAULT_TARGET_URL,
    groq_api_key: str = DEFAULT_GROQ_KEY
):
    """
    Rotates through multiple user accounts, posting max_posts_per_account per email,
    then logging into the next account to post the next topics!
    """
    unique_titles = list(dict.fromkeys([t.strip() for t in titles if t.strip()]))
    posted_titles = set()
    if os.path.exists(output_file):
        with open(output_file, "r", encoding="utf-8") as f:
            for line in f:
                if " -> " in line:
                    posted_titles.add(line.split(" -> ")[0].strip())

    remaining_titles = [t for t in unique_titles if t not in posted_titles]
    safe_print(f"🚀 Multi-Account Batch Runner started for {len(remaining_titles)} remaining titles across {len(accounts)} accounts (Max {max_posts_per_account} posts per account)...")

    title_idx = 0
    total_titles = len(remaining_titles)

    for acc_i, acc in enumerate(accounts, 1):
        if title_idx >= total_titles:
            safe_print("🎉 All titles have been successfully published!")
            break

        username = acc["email"]
        password = acc["pass"]
        posts_on_this_acc = 0

        safe_print("\n" + "="*70)
        safe_print(f"🔑 ACCOUNT {acc_i}/{len(accounts)}: {username}")
        safe_print("="*70)

        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=False,
                args=["--start-maximized", "--window-position=50,50", "--disable-blink-features=AutomationControlled"]
            )
            context = await browser.new_context(viewport=None)
            page = await context.new_page()

            try:
                # 1. Log into HF central account
                safe_print(f"[*] Navigating to HF Login: {login_url}...")
                await page.goto(login_url, wait_until="commit", timeout=60000)
                await page.wait_for_timeout(2500)

                username_input = page.locator("input[name='username'], input[name='email'], input[type='email']").first
                password_input = page.locator("input[name='password'], input[type='password']").first

                if await username_input.count() > 0 and await username_input.is_visible():
                    await username_input.fill("")
                    await username_input.type(username, delay=25)
                    await page.wait_for_timeout(300)
                    await password_input.fill("")
                    await password_input.type(password, delay=25)
                    await page.wait_for_timeout(300)
                    submit_btn = page.locator("button[type='submit'], input[type='submit']").first
                    await submit_btn.click()
                    await page.wait_for_timeout(4000)

                # 2. Complete SSO on Discourse
                safe_print(f"[*] Navigating to Discourse Category: {target_url}...")
                await page.goto(target_url, wait_until="commit", timeout=60000)
                await page.wait_for_timeout(3500)

                login_btn = page.locator("button.login-button, button:has-text('Log In')").first
                if await login_btn.count() > 0 and await login_btn.is_visible():
                    await login_btn.click()
                    await page.wait_for_timeout(4000)

                await page.goto(target_url, wait_until="commit", timeout=60000)
                await page.wait_for_timeout(3000)

                safe_print(f"✅ Session established for {username}! Posting up to {max_posts_per_account} topics...\n")

                while posts_on_this_acc < max_posts_per_account and title_idx < total_titles:
                    t_title = remaining_titles[title_idx]
                    safe_print(f"[*] Post {posts_on_this_acc + 1}/{max_posts_per_account} on {username} | Topic: {t_title}")

                    try:
                        await page.keyboard.press("Escape")
                        await page.wait_for_timeout(500)

                        if "c/intermediate" not in page.url:
                            await page.goto(target_url, wait_until="commit", timeout=30000)
                            await page.wait_for_timeout(2500)

                        await page.evaluate("""() => {
                            document.querySelectorAll('.dialog-overlay, [data-a11y-dialog-hide]').forEach(el => el.click());
                        }""")
                        await page.wait_for_timeout(500)

                        content = generate_huggingface_content(title=t_title, groq_api_key=groq_api_key)

                        new_topic_btn = page.locator("button#create-topic, button:has-text('New Topic'), .create-topic").first
                        await new_topic_btn.wait_for(state="visible", timeout=6000)
                        await new_topic_btn.click(timeout=6000)
                        await page.wait_for_timeout(1500)

                        title_input = page.locator("input#reply-title, input[placeholder*='Title']").first
                        await title_input.wait_for(state="visible", timeout=3000)
                        await title_input.click(timeout=3000)
                        await title_input.fill("")
                        await title_input.type(t_title, delay=15)
                        await page.wait_for_timeout(600)

                        await page.evaluate(f"""(text) => {{
                            const el = document.querySelector('.ProseMirror.d-editor-input') || 
                                       document.querySelector('.d-editor-input') || 
                                       document.querySelector('textarea.d-editor-input');
                            if (el) {{
                                if (el.tagName === 'TEXTAREA') {{
                                    el.value = text;
                                }} else {{
                                    el.innerText = text;
                                }}
                                el.dispatchEvent(new Event('input', {{ bubbles: true }}));
                                el.dispatchEvent(new Event('change', {{ bubbles: true }}));
                            }}
                        }}""", content)
                        await page.wait_for_timeout(1000)

                        create_btn = page.locator("button.btn-primary.create, button.create, button:has-text('Create Topic')").first
                        await create_btn.click(timeout=6000)
                        await page.wait_for_timeout(1500)

                        try:
                            similar_popover = page.locator(".similar-topics, :has-text('Your topic is similar to')")
                            if await similar_popover.count() > 0 and await similar_popover.is_visible():
                                await page.keyboard.press("Escape")
                                await page.wait_for_timeout(600)
                                if await create_btn.is_visible():
                                    await create_btn.click(timeout=4000)
                        except Exception:
                            pass

                        created_url = None
                        for second in range(25):
                            await page.wait_for_timeout(1000)
                            if "/t/" in page.url:
                                created_url = page.url
                                break

                        if created_url:
                            safe_print(f"🎉 [SUCCESS] {username} -> {t_title} -> {created_url}")
                            with open(output_file, "a", encoding="utf-8") as f:
                                f.write(f"{t_title} -> {created_url}\n")
                            posted_titles.add(t_title)
                            posts_on_this_acc += 1
                            title_idx += 1
                            await page.wait_for_timeout(3000)
                        else:
                            safe_print(f"[!] [SKIPPED] Topic creation timed out or limit reached for {username}. Moving to next title/account...")
                            await page.keyboard.press("Escape")
                            title_idx += 1

                    except Exception as err:
                        safe_print(f"[⚠️ SKIPPED] Error on '{t_title}': {err}. Moving to next title...")
                        await page.keyboard.press("Escape")
                        title_idx += 1

                safe_print(f"[*] Account {username} finished {posts_on_this_acc} posts. Closing session for next account...\n")
                await browser.close()
            except Exception as acc_err:
                safe_print(f"[!] Account {username} session error: {acc_err}")
                try:
                    await browser.close()
                except Exception:
                    pass

async def create_huggingface_topic(
    subject: str = "How do I cancel CCleaner subscription and stop auto renewal?",
    content: str = None,
    login_url: str = DEFAULT_LOGIN_URL,
    username: str = DEFAULT_USERNAME,
    password: str = DEFAULT_PASSWORD,
    target_url: str = DEFAULT_TARGET_URL,
    timeout_sec: int = 180,
    groq_api_key: str = DEFAULT_GROQ_KEY
) -> dict:
    """Single topic poster helper"""
    return await run_huggingface_multi_account_batch(
        titles=[subject],
        accounts=[{"email": username, "pass": password}],
        max_posts_per_account=2,
        login_url=login_url,
        target_url=target_url,
        groq_api_key=groq_api_key
    )

if __name__ == "__main__":
    subj = sys.argv[1] if len(sys.argv) > 1 else "How do I cancel CCleaner subscription and stop auto renewal?"
    asyncio.run(create_huggingface_topic(subject=subj))
