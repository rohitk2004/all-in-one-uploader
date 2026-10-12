import asyncio
import os
import re
import sys
import time
import requests
from playwright.async_api import async_playwright
from king_bot import create_king_discussion, generate_king_description

LOGIN_URL = "https://community.king.com/en/candy-crush-friends-saga/entry/signin"
FORUM_NEW_THREAD_URL = "https://community.king.com/en/candy-crush-friends-saga/post/discussion/discussion-forums"

EMAIL = "vayrox@rethinkmail.com"
PASSWORD = "Rohit@123321"

LINKS_FILE = "king_10_links.txt"

TITLES = [
    "Why Is AVG Activation Not Working? (Causes + Step-by-Step Solution)",
    "How to Confirm Your Bitdefender Purchase & Retrieve Your Key",
    "How to Set Up PC Matic for Beginners (Simple Step-by-Step Setup)",
    "Webroot Activation Failed After Reinstall? Fix It Fast (Step-by-Step)",
    "How to Install ESET on Windows 11 Step by Step (Beginner Guide)",
    "How to Activate Avast Offline (No Internet Activation Method)",
    "How to Set Up and Activate AVG Software for Beginners (Complete Guide)",
    "How to Enable CCleaner License After Purchase (Full Activation Guide)",
    "How to Use an Avast License Key Securely (Step-by-Step Activation)",
    "How to Activate McAfee After Trial Expiration (Full Renewal Guide)"
]

async def main():
    completed_count = 0
    valid_links = []
    if os.path.exists(LINKS_FILE):
        with open(LINKS_FILE, "r", encoding="utf-8") as f:
            valid_links = [line.strip() for line in f if line.strip() and ("discussion" in line or "entry" in line)]
        completed_count = len(valid_links)

    print(f"[*] Total Titles in Queue: {len(TITLES)}", flush=True)
    print(f"[+] Previously Completed: {completed_count}", flush=True)

    remaining_titles = TITLES[completed_count:]
    if not remaining_titles:
        print("[+] All 10 titles have already been processed!", flush=True)
        return

    print(f"[*] Starting King Community Bot ({len(remaining_titles)} remaining)...\n", flush=True)

    for idx, title in enumerate(remaining_titles, start=completed_count + 1):
        print(f"[{idx}/{len(TITLES)}] Processing: '{title}'...", flush=True)
        try:
            res = await create_king_discussion(
                title=title,
                email=EMAIL,
                password=PASSWORD,
                headless=False
            )
            if res.get("success") and res.get("public_url"):
                link = res["public_url"]
                with open(LINKS_FILE, "a", encoding="utf-8") as out:
                    out.write(f"{link}\n")
                print(f"  [+] SUCCESSFUL LIVE LINK ({idx}/10): {link}\n", flush=True)
            else:
                err = res.get("error", "Unknown error")
                print(f"  [-] Error on title '{title}': {err}\n", flush=True)
        except Exception as e:
            print(f"  [-] Exception on title '{title}': {e}\n", flush=True)

        if idx < len(TITLES):
            print(f"[*] Enforcing 65-second anti-spam rate limit gap before next post...", flush=True)
            await asyncio.sleep(65)

if __name__ == "__main__":
    asyncio.run(main())
