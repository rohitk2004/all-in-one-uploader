"""
Flyx ProBoards Automated Thread Creator & Batch Poster Bot
- Login URL   : https://login.proboards.com/login/7489843/1
- Login ID    : leomendis5
- Target Board: https://flyx.proboards.com/thread/new/1 (General Discussion)
- Session     : ONE-TIME Login (Browser window remains open)
- Cooldown    : 10 - 15 seconds random delay between posts
- Output File : flyx_threads.txt
"""

import asyncio
import os
import sys
import argparse

current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from proboards_bot import batch_post_proboards_threads, safe_print, DEFAULT_GROQ_KEY

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

def main():
    parser = argparse.ArgumentParser(description="Flyx ProBoards Automated Thread Creator Bot (Single-Session Posting)")
    parser.add_argument("--file", "-f", help="Path to .txt file containing thread titles (one per line)")
    parser.add_argument("--title", "-t", help="Single thread title to post")
    parser.add_argument("--login-url", default=DEFAULT_LOGIN_URL, help="ProBoards Login URL")
    parser.add_argument("--username", "-u", default=DEFAULT_USERNAME, help="ProBoards Username / ID")
    parser.add_argument("--password", "-p", default=DEFAULT_PASSWORD, help="ProBoards Password")
    parser.add_argument("--target-url", default=DEFAULT_TARGET_URL, help="Target new thread URL")
    parser.add_argument("--phone", default="+1 888 308 7172", help="Phone tag for content interleaving")
    parser.add_argument("--min-delay", type=float, default=10.0, help="Minimum delay between posts (seconds)")
    parser.add_argument("--max-delay", type=float, default=15.0, help="Maximum delay between posts (seconds)")
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

    unique_titles = list(dict.fromkeys([t.strip() for t in titles_to_run if t.strip()]))

    already_posted = 0
    if os.path.exists(args.output):
        try:
            with open(args.output, "r", encoding="utf-8") as f:
                already_posted = len([line for line in f if line.strip() and "/thread/" in line and "/thread/new/" not in line])
        except Exception:
            already_posted = 0

    remaining_titles = unique_titles[already_posted:]
    if not remaining_titles:
        safe_print(f"[!] All {len(unique_titles)} titles have already been posted according to {args.output}!")
        return

    safe_print("\n" + "=" * 70)
    safe_print("🚀 [FLYX PROBOARDS AUTOMATION BOT]")
    safe_print(f"🔑 Account    : {args.username} (One-Time Login)")
    safe_print(f"🌐 Login URL  : {args.login_url}")
    safe_print(f"📝 Target URL : {args.target_url}")
    safe_print(f"📊 Titles     : {len(remaining_titles)} remaining out of {len(unique_titles)}")
    safe_print(f"⏱️ Delay      : {args.min_delay}s - {args.max_delay}s random between posts")
    safe_print("=" * 70 + "\n")

    results = asyncio.run(batch_post_proboards_threads(
        titles=remaining_titles,
        guest_name="Leo Mendis",
        login_url=args.login_url,
        username=args.username,
        password=args.password,
        target_url=args.target_url,
        timeout_sec=args.timeout,
        groq_api_key=DEFAULT_GROQ_KEY,
        phone=args.phone,
        min_delay_sec=args.min_delay,
        max_delay_sec=args.max_delay,
        output_file=args.output
    ))

    successes = [r['url'] for r in results if r.get('success') and r.get('url')]
    safe_print("\n" + "=" * 70)
    safe_print(f"🎉 Flyx Run Complete: Successfully posted {len(successes)}/{len(remaining_titles)} threads!")
    safe_print(f"📁 All links saved in: {args.output}")
    safe_print("=" * 70 + "\n")

if __name__ == "__main__":
    main()
