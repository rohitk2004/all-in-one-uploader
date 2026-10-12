import asyncio
import os
import sys
from proboards_bot import create_proboards_thread, generate_proboards_content, DEFAULT_GROQ_KEY

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

TITLES = [
    "{[2026~𝐡ē𝐥𝐩]} How to Cancel CCleaner and Manage Your Subscription Settings (2026 Complete Control Guide)",
    "ᶠᵃq Why Does CCleaner Keep Crashing?",
    "[ų℘ɖąɬɛɖ] How Do I Confirm CCleaner Purchase Details?",
    "[ų℘ɖąɬɛɖ] How Do I Use an Activation Code for CCleaner Pro?",
    "[ų℘ɖąɬɛɖ] How Many Times Can I Activate the Same CCleaner License?",
    "[♜ ғα𝐐𝐒] Where Can I Find My CCleaner Activation Code?",
    "[~𝐅ά𝓠𝕤] What Is the Difference Between Installation and Activation in CCleaner?",
    "(𝙎𝙩𝙚𝙥𝙬𝙞𝙨𝙚 ~Guide) What Are the Best Setup Settings for CCleaner?",
    "ᵘᵖᵈᵃᵗᵉᵈ How Do I Configure CCleaner After Installation?",
    "[2026 Updated] What Is an Activation Server in CCleaner?",
    "[@𝘶𝘱𝘥𝘢𝘵𝘦𝘥] Why Is CCleaner Asking for Activation Again?",
    "[~𝐅ά𝓠𝕤] How Do I Install CCleaner on Windows 11?",
    "[♜@ ~𝗙𝗔𝗤'𝘀] How Do I Set Up CCleaner for Beginners?",
    "ᶠᵃq Where Can I Download CCleaner Safely?",
    "ᵘᵖᵈᵃᵗᵉᵈ What Is the Correct Site to Activate CCleaner Pro?",
    "[@𝘶𝘱𝘥𝘢𝘵𝘦𝘥] How Do I Activate CCleaner via Website?",
    "ᶠᵃq How Do I Set Up CCleaner for New Users?",
    "ᵘᵖᵈᵃᵗᵉᵈ* How Do I Install & Set Up CCleaner Step by Step?",
    "{[Cancellation !guide]} How Do I Activate CCleaner with Product Key?",
    "[♜@ ~𝗙𝗔𝗤'𝘀] How Do I Fix CCleaner Setup Failed Error? (2026)",
    "[♜@ ~FAQ's] How Do I Activate CCleaner on PC? (2026 Guide)",
    "[~𝐅ά𝓠𝕤] How Do I Set Up CCleaner for First Time?",
    "1-866 help^!!*How Do I Register CCleaner With a Product Key?",
    "1 (866) 490-O338 ) How Do I Contact CCleaner Support for Activation Issues?",
    "!#CaLL~ +1.866.49O.O338 }} What Is 𝘵𝘩𝘦 CCleaner Software Activation Process? (Complete Step-by-Step Guide)",
    "1-800 number^!!*How Can I Validate My CCleaner License Key ｔｏ Avoid Activation Issues? (Complete Guide 2026)",
    "1-866 faqs^!!*How Do I Fix CCleaner Setup Not Responding? (Complete Troubleshooting Guide 2026)",
    "{✨2025-2026~Guide📞} Can I Customize CCleaner Setup During Installation? (Full Setup Control Guide 2026)",
    "1-800 number^!!*How Do I Upgrade CCleaner from Trial ｔｏ Full Version? (Complete Activation Guide 2026)",
    "1-866 support^!!*Can Antivirus or Firewall Block CCleaner Software Activation? (Full Fix Guide 2026)",
    "1-866 faqs^!!*Can I Deactivate CCleaner ｔｏ Use It on Ano𝘵𝘩𝘦r Device? (Complete Transfer Guide)",
    "1 (866) 490-O338 How Do I Activate CCleaner Software Without an Internet Connection? (Offline Activation Guide)",
    "1-866 help^!!*How Do I Use a License Key ｔｏ Activate CCleaner Securely? (Safe Activation Guide)",
    "{✨2025-2026~Guide📞} How Do I Deactivate and Re-Activate CCleaner Software?",
    "1-800 number^!!*Do I Need Internet ｔｏ Complete CCleaner Setup?",
    "1 (866) 490-O338 ) Why Is CCleaner Activation Not Working After Installation?",
    "1-866 help^!!*Is 𝘵𝘩𝘦 CCleaner Activation Website Safe and Secure?"
]

OUTPUT_FILE = "naruto_threads_batch.txt"

async def main():
    print("\n" + "="*70, flush=True)
    print("[+] [NARUTO PROBOARDS BATCH PUBLISHER - GROQ AI ENGINE]", flush=True)
    print(f"[*] Total Titles in Queue: {len(TITLES)}", flush=True)
    print("="*70 + "\n", flush=True)

    results = []

    for idx, title in enumerate(TITLES, start=1):
        print(f"\n[{idx}/{len(TITLES)}] 📌 Processing Title: {title}", flush=True)
        print("[*] Generating authentic content with Groq AI...", flush=True)
        content = generate_proboards_content(title=title, groq_api_key=DEFAULT_GROQ_KEY)
        print(f"[+] Content ready ({len(content)} chars)!", flush=True)

        print("[*] Launching browser for submission...", flush=True)
        res = await create_proboards_thread(
            subject=title,
            content=content,
            timeout_sec=180,
            groq_api_key=DEFAULT_GROQ_KEY
        )

        if res.get("success") and res.get("url"):
            new_url = res["url"]
            print(f"[🎉 COMPLETED] ({idx}/{len(TITLES)}) Live Link: {new_url}\n", flush=True)
            results.append(f"{title} -> {new_url}")
            with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
                f.write(f"{title} -> {new_url}\n")
            await asyncio.sleep(4)
        else:
            print(f"[❌ FAILED/TIMEOUT] ({idx}/{len(TITLES)}) Error: {res.get('error')}\n", flush=True)

    print("\n" + "="*70, flush=True)
    print("🏁 ALL BATCH TITLES PROCESSED!")
    print(f"Check {OUTPUT_FILE} for saved live links.")
    print("="*70 + "\n", flush=True)

if __name__ == "__main__":
    asyncio.run(main())
