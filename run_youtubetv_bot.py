import asyncio
import os
import sys
from proboards_bot import (
    create_proboards_thread,
    generate_proboards_content,
    DEFAULT_GROQ_KEY,
    DEFAULT_LOGIN_URL,
    DEFAULT_USERNAME,
    DEFAULT_PASSWORD,
    URL
)

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

DEFAULT_TITLES = [
    "How to Fix YouTube TV Network Error and Connection Issues",
    "YouTube TV Billing and Account Management Complete Guide",
    "How to Reset YouTube TV Password and Recover Account Access"
]

OUTPUT_FILE = "youtubetv_proboards_threads.txt"

async def main():
    print("\n" + "="*70, flush=True)
    print("🚀 [YOUTUBE TV PROBOARDS BOT - AUTOMATED THREAD CREATOR]", flush=True)
    print(f"🔑 Login URL : {DEFAULT_LOGIN_URL}", flush=True)
    print(f"📝 Target URL: {URL}", flush=True)
    print("="*70 + "\n", flush=True)

    titles_to_run = sys.argv[1:] if len(sys.argv) > 1 else DEFAULT_TITLES

    for idx, title in enumerate(titles_to_run, start=1):
        print(f"\n[{idx}/{len(titles_to_run)}] 📌 Title: {title}", flush=True)
        print("[*] Generating content...", flush=True)
        content = generate_proboards_content(title=title, groq_api_key=DEFAULT_GROQ_KEY)
        print(f"[✓] Generated content ({len(content)} characters)", flush=True)

        print("[*] Launching browser for ProBoards submission...", flush=True)
        res = await create_proboards_thread(
            guest_name="YouTube TV Support Agent",
            subject=title,
            content=content,
            login_url=DEFAULT_LOGIN_URL,
            username=DEFAULT_USERNAME,
            password=DEFAULT_PASSWORD,
            target_url=URL,
            timeout_sec=180,
            groq_api_key=DEFAULT_GROQ_KEY
        )

        if res.get("success") and res.get("url"):
            new_url = res["url"]
            print(f"✅ THREAD CREATED! URL: {new_url}\n", flush=True)
            with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
                f.write(f"{new_url}\n")
        else:
            print(f"❌ Creation status/error: {res.get('error', 'Check browser window')}\n", flush=True)

if __name__ == "__main__":
    asyncio.run(main())
