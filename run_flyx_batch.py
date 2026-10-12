"""
Flyx ProBoards Automated Thread Creator & Batch Poster Bot
- Login URL   : https://login.proboards.com/login/7489843/1
- Login ID    : leomendis5
- Target Board: https://flyx.proboards.com/thread/new/1 (General Discussion)
- Output File : flyx_threads.txt
"""

import asyncio
import os
import sys
import argparse

current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from proboards_bot import create_proboards_thread, generate_proboards_content, safe_print, DEFAULT_GROQ_KEY

DEFAULT_LOGIN_URL = "https://login.proboards.com/login/7489843/1"
DEFAULT_USERNAME = "leomendis5"
DEFAULT_PASSWORD = "Rohit@123321#"
DEFAULT_TARGET_URL = "https://flyx.proboards.com/thread/new/1"
OUTPUT_FILE = "flyx_threads.txt"

SAMPLE_TITLES = [
    "《FAQ'S™》1 888 308 7172 How to Cancel Norton Subscription and Manage Auto Renewal",
    "How Do I Confirm Norton Purchase Details and Order Status? (2026 Step-by-Step)",
    "How to Redeem and Activate Norton License Key After Purchase",
    "Why Won't Norton Antivirus Activate and How Can I Fix It?"
]

async def run_flyx_bot(
    titles: list,
    login_url: str = DEFAULT_LOGIN_URL,
    username: str = DEFAULT_USERNAME,
    password: str = DEFAULT_PASSWORD,
    target_url: str = DEFAULT_TARGET_URL,
    groq_api_key: str = DEFAULT_GROQ_KEY,
    phone: str = "+1 888 308 7172",
    timeout_sec: int = 180,
    output_file: str = OUTPUT_FILE
):
    unique_titles = list(dict.fromkeys([t.strip() for t in titles if t.strip()]))
    already_posted = 0
    if os.path.exists(output_file):
        try:
            with open(output_file, "r", encoding="utf-8") as f:
                already_posted = len([line for line in f if line.strip() and "/thread/" in line and "/thread/new/" not in line])
        except Exception:
            already_posted = 0

    total = len(unique_titles)
    safe_print("\n" + "=" * 70)
    safe_print("🚀 [FLYX PROBOARDS AUTOMATION BOT]")
    safe_print(f"🔑 Account    : {username}")
    safe_print(f"🌐 Login URL  : {login_url}")
    safe_print(f"📝 Target URL : {target_url}")
    safe_print(f"📊 Total Titles: {total} (Resuming from index {already_posted + 1})")
    safe_print("=" * 70 + "\n")

    if already_posted >= total:
        safe_print(f"[!] All {total} titles have already been posted according to {output_file}!")
        return

    for idx, title in enumerate(unique_titles[already_posted:], start=already_posted + 1):
        safe_print("=" * 60)
        safe_print(f"[*] Posting ({idx}/{total}): {title}")
        safe_print("=" * 60)

        res = await create_proboards_thread(
            guest_name="Leo Mendis",
            subject=title,
            content=None,  # AI generated content with phone tag
            login_url=login_url,
            username=username,
            password=password,
            target_url=target_url,
            timeout_sec=timeout_sec,
            groq_api_key=groq_api_key
        )

        if res.get("success") and res.get("url"):
            thread_url = res["url"]
            safe_print(f"✅ [SUCCESS {idx}/{total}] {title} -> {thread_url}")
            with open(output_file, "a", encoding="utf-8") as out_f:
                out_f.write(f"{thread_url}\n")
        else:
            err = res.get("error", "Unknown error or timeout")
            safe_print(f"❌ [FAILED {idx}/{total}] {title} -> Error: {err}")

    safe_print(f"\n🎉 Finished Flyx batch run. Links saved to {output_file}!\n")

def main():
    parser = argparse.ArgumentParser(description="Flyx ProBoards Automated Thread Creator Bot")
    parser.add_argument("--file", "-f", help="Path to .txt file containing thread titles (one per line)")
    parser.add_argument("--title", "-t", help="Single thread title to post")
    parser.add_argument("--login-url", default=DEFAULT_LOGIN_URL, help="ProBoards Login URL")
    parser.add_argument("--username", "-u", default=DEFAULT_USERNAME, help="ProBoards Username / ID")
    parser.add_argument("--password", "-p", default=DEFAULT_PASSWORD, help="ProBoards Password")
    parser.add_argument("--target-url", default=DEFAULT_TARGET_URL, help="Target new thread URL")
    parser.add_argument("--timeout", type=int, default=180, help="Wait timeout in seconds")
    parser.add_argument("--output", "-o", default=OUTPUT_FILE, help="Output file for generated links")

    args = parser.parse_args()

    titles_to_run = []
    if args.title:
        titles_to_run.append(args.title)
    elif args.file and os.path.exists(args.file):
        with open(args.file, "r", encoding="utf-8") as f:
            titles_to_run = [line.strip() for line in f if line.strip()]
    else:
        titles_to_run = SAMPLE_TITLES

    asyncio.run(run_flyx_bot(
        titles=titles_to_run,
        login_url=args.login_url,
        username=args.username,
        password=args.password,
        target_url=args.target_url,
        timeout_sec=args.timeout,
        output_file=args.output
    ))

if __name__ == "__main__":
    main()
