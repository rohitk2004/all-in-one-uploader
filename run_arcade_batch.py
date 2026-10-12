import asyncio
import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from proboards_bot import create_proboards_thread, safe_print

TITLES = [
    "[Instant~Guide-]USA How to Cancel ccleaner Subscription Stop Auto Renewal",
    "[Instant~Guide-]USA How to Cancel surfshark Subscription Stop Auto Renewal",
    "[Instant~Guide-]USA How to Cancel webroot Subscription Stop Auto Renewal",
    "[Instant~Guide-]USA How to Cancel norton Subscription Stop Auto Renewal",
    "[Instant~Guide-]USA How to Cancel mcafee Subscription Stop Auto Renewal",
    "[Instant~Guide-]USA How to Cancel total drive Subscription Stop Auto Renewal",
    "[Instant~Guide-]USA How to Cancel avast Subscription Stop Auto Renewal",
    "[Instant~Guide-]USA How to Cancel total adware Subscription Stop Auto Renewal",
    "[Instant~Guide-]USA How to Cancel express vpn Subscription Stop Auto Renewal",
    "[Instant~Guide-]USA How to Cancel At&t Subscription Stop Auto Renewal",
    "[Instant~Guide-]USA How to Cancel norton360 Subscription Stop Auto Renewal",
    "FaQ\"S How to cancel Total adblock Subscription Quickly Complete Cancelling Guide",
    "FaQ\"S How to cancel ccleaner Subscription Quickly Complete Cancelling Guide",
    "FaQ\"S How to cancel surfshark Subscription Quickly Complete Cancelling Guide",
    "FaQ\"S How to cancel norton Subscription Quickly Complete Cancelling Guide",
    "FaQ\"S How to cancel mcafee Subscription Quickly Complete Cancelling Guide",
    "FaQ\"S How to cancel totalav Subscription Quickly Complete Cancelling Guide"
]

async def main():
    login_url = "https://login.proboards.com/login/3425386/1"
    username = "leomendis"
    password = "Rohit@123321"
    target_url = "https://arcadegamedesigner.proboards.com/thread/new/4"
    
    total = len(TITLES)
    safe_print(f"🚀 Starting Arcade Game Designer batch run for {total} titles...")

    for idx, t_title in enumerate(TITLES, 1):
        safe_print("="*60)
        safe_print(f"[*] Thread {idx}/{total}: {t_title}")
        safe_print("="*60)

        res = await create_proboards_thread(
            guest_name="Leo Mendis",
            subject=t_title,
            content=None, # Groq AI generated content
            login_url=login_url,
            username=username,
            password=password,
            target_url=target_url,
            timeout_sec=180
        )

        if res.get("success") and res.get("url"):
            link = res["url"]
            safe_print(f"[SUCCESS {idx}/{total}] {t_title} -> {link}")
            with open("arcade_threads.txt", "a", encoding="utf-8") as f:
                f.write(f"{link}\n")
        else:
            safe_print(f"[FAILED {idx}/{total}] {t_title} -> Error: {res.get('error')}")

if __name__ == "__main__":
    asyncio.run(main())
