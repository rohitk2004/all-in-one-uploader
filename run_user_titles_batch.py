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

TITLES = [
    "How Do I Know If My ESET Software Is Successfully Activated? (Clear Signs + Quick Checks 2026)",
    "How to Redeem and Activate Avast After Purchase (Complete 2026 Guide)",
    "How Do I Set Up and Activate Malwarebytes Quickly for Full Protection?",
    "How Do I Activate Webroot Trial Versions Without Errors?",
    "How to Activate PC Matic After Trial Expiration (Step-by-Step Renewal Guide)",
    "How Do I Log In and Activate a Malwarebytes Pro License? (Step-by-Step Guide)",
    "How Do I Activate Webroot Software Offline Easily?",
    "Why Do You Need to Activate Kaspersky Antivirus?",
    "How Do I Deactivate and Re-Activate Webroot Software?",
    "How Long Does McAfee Software Stay Activated Exactly?",
    "How Many Times Can I Activate PC Matic License?",
    "What Happens If I Don't Activate Norton?",
    "Glary Utilities Purchased? Here's How to Activate It (2026 Complete Activation Guide)",
    "How to Redeem and Activate Malwarebytes After Purchase (2026 Complete Guide)",
    "How Many Times Can I Activate TotalAV License?",
    "How Do I Check If McAfee Software Is Successfully Activated?",
    "Avira Purchased? Here's How to Activate It (Step-by-Step Guide)",
    "How to Activate NortonLifeLock After Purchase (Step-by-Step Guide 2026)",
    "How Do I Activate VBA32 After Buying It? (2026's Best Method)",
    "Why Won't AVG Activate and How Can I Fix It? (Complete Diagnostic + Fix Framework)",
    "How Do I Activate Apple TV When Stuck on Setup Screen?",
    "How Do I Activate Norton Software Using Product Key Step by Step?",
    "How Do I Set Up and Activate Webroot for Beginners?",
    "How Long Does Avast Software Stay Activated? (2026 Complete Guide)",
    "How Do I Activate Avast Software with a License Key? (Complete Activation Guide for 2026)",
    "What Are the Steps to Activate AVG Professional Edition?",
    "How Do I Activate ESET on My PC?",
    "How Do I Activate FaceTime on iPhone or Mac Without Errors?",
    "How to Activate Malwarebytes After Purchase (Step-by-Step Guide for 2026)",
    "Recuva Purchased? Here's How to Activate It (2026 Complete Guide)",
    "How Do You Download, Install, and Activate Norton You've Already Purchased? (2026 Guide)",
    "Where and How Do I Enter My Norton Product Key to Activate Software? (Complete Activation System Guide)",
    "How to Install and Activate Trend Micro After Purchase (2026 Complete Setup Guide)",
    "How Do I Activate Trend Micro Using Website?",
    "How Do You Install and Activate ESET Antivirus Without Errors?",
    "How to Install and Activate Kaspersky After Purchase (Step-by-Step Guide 2026)",
    "How Do You Install and Activate Panda Antivirus? (Step-by-Step Guide)",
    "How Do I Use a License Key to Activate ESET Securely?",
    "Can I Activate Malwarebytes Without Website?",
    "How Do You Activate McAfee Setup with Your Product Key and Start Protection?",
    "How Do I Activate AVG License Step by Step for Beginners?",
    "How Do I Activate ESET Software Offline Step by Step?",
    "How Do I Activate Norton on Windows 10 After Install?",
    "How Do You Activate Malwarebytes Setup and Unlock Full Protection? (2026 Guide)",
    "How Do I Activate Trend Micro After Installing It on Windows 10? (Complete 2026 Setup & Activation Guide)",
    "How Do I Activate Webroot After Installing It on Windows 10? (Complete Step-by-Step Guide)",
    "Do I Need Internet to Activate CCleaner?",
    "How to Redeem and Activate Trend Micro After Purchase (2026 Complete Guide)",
    "How Do You Install and Activate Your McAfee Subscription? (2026 Guide)",
    "How Do You Install and Activate Your AVG Subscription on Any Device?",
    "How Do You Activate Your Webroot License Key? (2026 Guide)",
    "How Do I Log In & Activate Webroot Pro License?",
    "How to Activate CleanMyMac After Purchase (Step-by-Step Guide for 2026)",
    "How Do I Activate PC Matic License the Right Way Easily?",
    "What Is the Correct Site to Activate Avast Pro?",
    "How Do You Activate and Install Bitdefender Antivirus the Right Way? (2026 Guide)",
    "How Do You Activate Your Kaspersky License Key and Unlock Full Protection? (2026 Guide)",
    "How Do I Activate PC Matic Software with a Product Key?",
    "Why Won't Norton Activate and How Can I Fix It?",
    "How Do I Activate CCleaner After Buying It? (2026's Best Method)",
    "How Do I Activate CCleaner with Product Key?",
    "How Long Does AVG Software Stay Activated? (Subscription Timeline + Activation Logic Explained)",
    "Why Is Bitdefender Not Activated? How Do I Fix License Errors & Enable Protection Fast?",
    "How to Install and Activate Surfshark After Purchase (2026-27 Guide)",
    "How Do I Activate nProtect After Buying It (2026's Best Method)",
    "Can I Activate Trend Micro on Multiple Devices?",
    "How Do I Activate Avast Without Internet? (Offline Activation Truth + Workarounds)",
    "What Is the Correct Site to Activate Kaspersky Pro?",
    "Avast Purchased? Here's How to Activate It (Step-by-Step Guide)",
    "AVG Purchased? Here's How to Activate It (Step-by-Step Guide)",
    "Why Is Webroot Asking to Activate Again After Update?",
    "Why Is Avast Antivirus Not Activated & How Do I Fix It Fast?",
    "Why Is Panda Antivirus Not Activated & How Can I Fix It Fast?",
    "Webroot Says Trial After Purchase? 14 Easy Fixes to Activate Your Paid Subscription",
    "What Happens If I Don't Activate ESET Software on My PC?",
    "What Happens If I Don't Activate Webroot?",
    "What Happens If I Never Activate McAfee?",
    "Webroot Retail Activation Help: Complete Guide to Activate Your Retail Key Successfully",
    "How to Install Malwarebytes on a New Laptop and Activate Your Existing Subscription",
    "How to Activate Malwarebytes After Purchase (Step-by-Step)",
    "Trend Micro Purchased? Here's How to Activate It",
    "How to Redeem and Activate Avast After Purchase",
    "How to Activate AVG After Purchase (Step-by-Step)",
    "How to Activate Fortect After Purchase (Step-by-Step)",
    "McAfee Activation Code Not Accepted? 15 Proven Fixes to Activate Your Subscription Successfully",
    "Do I Need to Activate Free Version of Kaspersky?",
    "What Happens If You Never Activate Avast Software?",
    "How Do I Activate McAfee Software with a License Key? (Complete Activation Workflow + Error-Free Setup)",
    "Norton Purchased? Here's How to Activate It (Fast Setup Guide for All Devices)",
    "How to Activate 360 Total Security After Purchase (Step-by-Step)",
    "How Do I Activate ESET Software Offline Without Internet?",
    "How to Activate Intego After Purchase (Step-by-Step Guide)",
    "How Do I Activate Malwarebytes Offline Without Internet?",
    "How to Activate McAfee After Purchase (Step-by-Step Guide)",
    "How to Activate nProtect After Buying It: A Clear 2026 Setup Guide",
    "How Do I Activate Webroot Software Manually or Automatically? Complete Activation Guide (2026)",
    "Can I Activate Webroot Without Using the Activation Website? (Direct Methods That Work)",
    "How to Install and Activate Advanced SystemCare After Purchase (2026 Step-by-Step Guide)",
    "How to Install and Activate BleachBit After Purchase (2026 Guide)",
    "How to Install and Activate Comodo After Purchase (Complete Step-by-Step Guide)",
    "How to Install and Activate MacPaw After Purchase (CleanMyMac & Setapp Guide 2026)",
    "How to Install and Activate nProtect After Purchase (Step-by-Step Guide)",
    "How to Install and Activate Surfshark After Purchase (Complete Setup Guide for All Devices)",
    "How Do I Log In and Activate an ESET Pro License? Complete Step-by-Step Guide (2026)",
    "Can I Activate McAfee Without Website?",
    "How Do I Activate CCleaner Software Offline? (Complete No-Internet Activation Guide)",
    "How Do I Check If Norton Is Activated?",
    "How Do I Know If My PC Matic Software Is Successfully Activated? (Clear Signs + Verification Guide)",
    "How Do I Activate Norton After Buying It? (2026's Best Method)",
    "How to Activate FixMeStick After Purchase (Step-by-Step)",
    "How to Redeem and Activate Driver Booster After Purchase",
    "How Do You Download, Install, and Activate PC Matic Antivirus?",
    "Why Is Activate Windows Watermark Showing & How Can I Fix It?",
    "Do I Need to Activate Free Version of CCleaner?",
    "How Do You Install AVG You've Already Purchased and Activate It? (2026 Guide)",
    "How Do I Activate CCleaner Trial Versions Without Errors? (Clean Activation Strategy Guide)",
    "How Do I Activate Avira Using Product Key via Setup Page?",
    "How Do I Activate CCleaner via Website?",
    "How Do I Activate Malwarebytes After Buying It (2026's Best Method)",
    "How Do I Activate Malwarebytes Using Website Easily?",
    "How Do I Activate Malwarebytes Using Product Key via Setup Page?",
    "How Do I Activate McAfee via Setup Page Using Product Key Easily?",
    "How Do I Activate McAfee Offline Without Internet Access?",
    "How Do I Activate Microsoft Office Using Product Key Step by Step?",
    "How Do I Activate Total Defense After Buying It (2026's Best Method)",
    "How Do I Activate Trend Micro with License Key?",
    "How Do I Activate My Bitdefender Product License the Right Way? (Zero-Error Setup Guide for 2026)",
    "How Do I Enter Office Product Code and Activate It Without Errors?",
    "How Do I Download, Install & Activate McAfee via Setup Page?",
    "How Do I Activate PC Matic Without Internet?",
    "Why Won't Webroot Activate & How Can I Fix It Fast?",
    "Can I Activate AVG Without Using the Activation Website? (Complete Alternative Activation Guide)",
    "Can I Activate TotalAV Purchased from Third Party?",
    "Can I Activate Norton Software Purchased from a Third Party? (Full Verification & Activation Guide)",
    "iObit Purchased? Here's How to Activate It (2026 Complete Activation Guide)",
    "How to Activate Trend Micro After Purchase (Step-by-Step 2026 Guide)",
    "How to Activate Webroot After Purchase (Step-by-Step Guide for Instant Protection)",
    "How Many Times Can I Activate the Same Avast License?",
    "How to Redeem and Activate Intego After Purchase (2026 Complete License Activation Guide)",
    "How Long Does Bitdefender Software Stay Activated Exactly?",
    "Why Won't Bitdefender Activate and How Can I Fix It? (Complete 2026 Troubleshooting Guide)",
    "Why Won't Avast Activate and How Can You Fix It Fast?",
    "Fortect Purchased? Here's How to Activate It (Complete 2026 Activation Guide)",
    "How to Install and Activate Fortect After Purchase (Complete 2026 Setup Guide)",
    "Malwarebytes Purchased? Here's How to Activate It (Step-by-Step)",
    "How Long Does ESET Stay Activated?",
    "How Do You Activate and Set Up McAfee You've Already Purchased? (Step-by-Step Guide)",
    "How Many Times Can I Activate the Same CCleaner License?",
    "How Do I Activate Emsisoft After Buying It (2026's Best Method)",
    "How Do I Log In & Activate CCleaner Pro License?",
    "How to Activate VBA32 After Purchase (Step-by-Step Guide for 2026)",
    "How to Redeem and Activate CleanMyMac After Purchase (Complete 2026 License Activation Guide)",
    "How Do I Activate Webroot License Properly?",
    "How Do I Activate PC Matic Offline Without Internet Access? (Complete Offline Activation Guide)",
    "How Do I Activate Bitdefender Software Offline Without Internet Access? (Complete 2026 Guide)",
    "What Happens If I Don't Activate Bitdefender Software? (2026 Full Explanation)",
    "Why Do I Need to Activate ESET?",
    "How Do You Activate Norton Setup with Your Product Key? (Step-by-Step Guide)",
    "Do I Need Internet to Activate PC Matic?",
    "What Are the Steps to Activate PC Matic Professional Edition?",
    "What Are the Steps to Activate Webroot Professional Edition?",
    "How Do You Activate Webroot Setup with Your Keycode? (Step-by-Step Guide)",
    "How Do I Activate ESET After Installing on Windows 10?",
    "How Do I Use License Key to Activate McAfee Securely?",
    "How Do I Log In and Activate a Norton Pro License? (Complete Setup & Activation Guide)",
    "How Do I Log In and Activate AVG Pro?",
    "How Do I Activate PC Matic Using Website?",
    "Where and How Do I Enter My PC Matic Product Key to Activate Software? (2026 Guide)",
    "How Do I Log In and Activate an ESET Pro License? (Complete Setup & Activation Guide)",
    "What Is the Official Site to Activate Webroot Pro Safely?",
    "How Do I Activate Malwarebytes After a Trial Expires? (2026 Complete Guide)",
    "Norton Product Key Already Used? 12 Proven Fixes to Activate Your Subscription",
    "Norton Subscription Not Activated? 12 Proven Fixes to Activate Your Norton Subscription",
    "How Long Does Kaspersky Software Stay Activated? (Complete 2026 Guide)",
    "How Long Does Kaspersky Software Stay Activated? (Subscription Duration + Renewal Logic 2026)",
    "How Do You Download, Install, and Activate Norton Antivirus?",
    "How Do I Activate AVG Software Offline Without Internet Access?",
    "How to Install and Activate Sophos After Purchase (Complete 2026 Setup Guide)",
    "How Do I Activate McAfee Without Internet Connection?",
    "What Are the Steps to Activate Norton Professional Edition? (2026 Guide)",
    "How Many Times Can I Activate ESET License?",
    "How Do I Activate Bitdefender License Step by Step for New Users?",
    "Intego Purchased? Here's How to Activate It (Step-by-Step Guide)",
    "How to Redeem and Activate Total Defense After Purchase",
    "Do You Need Internet to Activate Webroot? (Offline Limits + Smart Activation Tips)",
    "Do I Need to Activate Free Version of Webroot Software?",
    "How Do You Install and Activate TotalAV the Right Way? (2026 Guide)",
    "How to Redeem and Activate BleachBit After Purchase (2026-27 Guide)",
    "Can I Activate AVG Bought from Third Party Safely?",
    "How Do I Activate Kaspersky Using Digital License Easily?",
    "How to Install and Activate F-Secure SAFE After Purchase (Complete 2026 Setup Guide)",
    "How Long Does CCleaner Stay Activated Before Expiry?",
    "AVG Already Activated on Another Device? How to Transfer and Fix Activation Errors",
    "Why Is Trend Micro Not Activated & How Do I Fix License Errors?",
    "Avast Activation Code Not Found? 13 Easy Fixes to Locate and Activate Your Subscription",
    "How Do You Activate Your Norton License Key? (Updated Guide)",
    "How to Activate MacPaw After Purchase (Step-by-Step)",
    "How Do I Activate ZoneAlarm After Buying It (2026's Best Method)",
    "How to Activate Avast Offline (No Internet Activation Guide Explained Clearly)"
]

# Unique titles preserve order
seen = set()
UNIQUE_TITLES = []
for t in TITLES:
    if t not in seen:
        seen.add(t)
        UNIQUE_TITLES.append(t)

OUTPUT_FILE = "user_uploaded_links.txt"

async def main():
    print("\n" + "="*75, flush=True)
    print("🚀 [PROBOARDS USER BATCH PUBLISHER - YOUTUBE TV FORUM]", flush=True)
    print(f"📌 Unique Titles in Queue: {len(UNIQUE_TITLES)}", flush=True)
    print(f"🔑 Login URL : {DEFAULT_LOGIN_URL}", flush=True)
    print(f"📝 Target URL: {URL}", flush=True)
    print("="*75 + "\n", flush=True)

    completed_titles = set()
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split(" | ")
                if len(parts) >= 2:
                    completed_titles.add(parts[0])

    queue = [t for t in UNIQUE_TITLES if t not in completed_titles]
    print(f"[*] Remaining titles to publish: {len(queue)} (Already completed: {len(completed_titles)})", flush=True)

    for idx, title in enumerate(queue, start=1):
        print(f"\n[{idx}/{len(queue)}] 📌 Processing: {title}", flush=True)
        print("[*] Generating unique AI technical content...", flush=True)
        content = generate_proboards_content(title=title, groq_api_key=DEFAULT_GROQ_KEY)
        print(f"[✓] Content ready ({len(content)} chars)!", flush=True)

        print("[*] Launching browser and posting thread...", flush=True)
        res = await create_proboards_thread(
            guest_name="Tech Support Agent",
            subject=title,
            content=content,
            login_url=DEFAULT_LOGIN_URL,
            username=DEFAULT_USERNAME,
            password=DEFAULT_PASSWORD,
            target_url=URL,
            timeout_sec=300,
            groq_api_key=DEFAULT_GROQ_KEY
        )

        if res.get("success") and res.get("url"):
            new_url = res["url"]
            print(f"[🎉 SUCCESS] Live Thread Link: {new_url}\n", flush=True)
            with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
                f.write(f"{title} | {new_url}\n")
            await asyncio.sleep(4)
        else:
            print(f"[❌ FAILED / TIMEOUT] Error: {res.get('error')}\n", flush=True)

    print("\n" + "="*75, flush=True)
    print("🏁 BATCH CREATION COMPLETED!")
    print(f"Saved all results to: {OUTPUT_FILE}")
    print("="*75 + "\n", flush=True)

if __name__ == "__main__":
    asyncio.run(main())
