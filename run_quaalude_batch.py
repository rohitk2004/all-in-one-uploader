import asyncio
import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from proboards_bot import create_proboards_thread, safe_print

TITLES = [
    "[Instant~Guide-] How to Cancel Total adblock Subscription",
    "[Instant~Guide-] How to Cancel ccleaner Subscription",
    "[Instant~Guide-] How to Cancel surfshark Subscription",
    "[Instant~Guide-] How to Cancel webroot Subscription",
    "[Instant~Guide-] How to Cancel norton Subscription",
    "[Instant~Guide-] How to Cancel mcafee Subscription",
    "[Instant~Guide-] How to Cancel total drive Subscription",
    "[Instant~Guide-] How to Cancel avast Subscription",
    "[Instant~Guide-] How to Cancel total adware Subscription",
    "[Instant~Guide-] How to Cancel express vpn Subscription",
    "[Instant~Guide-] How to Cancel At&t Subscription",
    "[Instant~Guide-] How to Cancel norton360 Subscription",
    "FaQ\"S How to cancel Total adblock Subscription Quickly",
    "FaQ\"S How to cancel ccleaner Subscription Quickly",
    "FaQ\"S How to cancel surfshark Subscription Quickly",
    "FaQ\"S How to cancel norton Subscription Quickly",
    "FaQ\"S How to cancel mcafee Subscription Quickly",
    "FaQ\"S How to cancel totalav Subscription Quickly",
    "How do I stop CCleaner from auto renewal?",
    "How do I permanently cancel a subscription?",
    "How do I quit CCleaner?",
    "How can I cancel my Cleverbridge CCleaner subscription?",
    "FAQ's)) How do I permanently cancel a ccleaner subscription",
    "FaQ\"S How to cancel McAfee Subscription Quickly",
    "FAq's) How to cancel Total adblock subscription",
    "Where do I find my total Adblock subscription?",
    "How do I permanently cancel a subscription?",
    "How do I stop payments to Adblock?",
    "How do I stop total adblock?",
    "How do I cancel my subscription with Total Adblock?",
    "Where do I find my total Adblock subscription?",
    "How to stop Adblock payments?",
    "How do I cancel my Adblock account?",
    "How do I cancel my subscription to CCleaner?",
    "How do I cancel my Cleverbridge CCleaner subscription?",
    "How do I turn off automatic renewal on CCleaner?",
    "How can I get rid of CCleaner?",
    "How do I cancel my Malwarebytes account?",
    "How to get rid of Malwarebytes auto renewal?",
    "How do I quit Malwarebytes?",
    "How do I cancel a free trial on Malwarebytes?",
    "Is TotalAV hard to cancel?",
    "How do I stop TotalAV from taking money from my account?",
    "How do I completely cancel my TotalAV subscription?",
    "What is the best way to contact TotalAV?",
    "Can I cancel ExpressVPN and get my money back?",
    "Does deleting an ExpressVPN account cancel a subscription?",
    "How do I cancel my ExpressVPN account?",
    "How do I cancel my Surfshark subscription?",
    "Is Surfshark VPN easy to cancel?",
    "Does deleting my Surfshark account cancel my subscription?",
    "Can I get my money back from Surfshark?",
    "How do I cancel my subscription to Guardio?",
    "How do I contact Guardio customer service?",
    "How do I cancel my Guardio subscription?",
    "How can I get rid of Guardio?",
    "How do I get rid of ESET?",
    "How do I stop ESET service?",
    "How to check ESET subscription?",
    "How do I contact ESET support?",
    "How do I cancel my PC Matic subscription?",
    "How do I cancel subscriptions on my PC Matic?",
    "How do I cancel my PC Matic subscription?",
    "How do I permanently cancel PC Matic subscription?",
    "How do I cancel my Panda Dome subscription?",
    "How do I cancel an online Panda Dome subscription?",
    "How do I cancel my Panda VPN subscription?",
    "How do I cancel my Dr. Panda subscription?",
    "How do I cancel my Avira subscription?",
    "How do I deactivate my Avira subscription?",
    "How to quit Avira?",
    "Can Avira antivirus be trusted?",
    "Is Aura hard to cancel?",
    "How do I completely cancel my Aura subscription?",
    "How do I stop AutoPay in the Aura app?",
    "Does Aura have a senior discount?",
    "How do I cancel a Microsoft Office subscription?",
    "How do I deactivate my Office subscription?",
    "Why is Microsoft not letting me cancel my subscription?",
    "How do I stop Microsoft from charging my card?",
    "Can I cancel my Microsoft subscription and get my money back?",
    "How do I stop Microsoft from charging my card?",
    "Why can't I cancel my Microsoft subscription?",
    "Can you get a refund after Microsoft charges you for a subscription?",
    "How do I cancel Adblock premium?",
    "Where do I find my total Adblock subscription?",
    "How to remove Adblock Premium?",
    "How do I cancel total Adblock and get a refund?",
    "Will McAfee give me a refund?",
    "Will I get a refund if I cancel my subscription?",
    "How do I stop McAfee from charging me?",
    "Can I get money back from automatic renewal?",
    "Can you cancel your McAfee subscription and get a refund?",
    "Will McAfee give me a refund?",
    "Will I get a refund if I cancel my McAfee subscription?",
    "How do I cancel my AdGuard subscription?",
    "How do I completely cancel a subscription?",
    "How do I cancel my AdGuard subscription and get refund?",
    "How do I deactivate AdGuard?",
    "Can I get money back from Norton automatic renewal?",
    "How to request a refund for an annual renewal fee in Norton?",
    "How to get Norton customer service to give you a refund?",
    "How long does a Norton refund take?",
    "Can I cancel Kaspersky and get a refund?",
    "Why is Kaspersky no longer allowed in the US?",
    "How do I contact Kaspersky to cancel my subscription?",
    "How do I stop Kaspersky automatic payments?",
    "Can I cancel Bitdefender automatic renewal?",
    "How do I deactivate my Bitdefender account?",
    "How do I remove my credit card from Bitdefender?",
    "How do I check my Bitdefender subscription?",
    "What is the Trend Micro scandal?",
    "Does turning off auto renewal cancel my subscription?",
    "How to stop Trend Micro?",
    "How do I deactivate my auto renewal subscription?",
    "Can I cancel AVG and get a refund?",
    "How do I stop AVG from taking money from my account?",
    "Do I get my money back if I cancel my Microsoft subscription?",
    "How long does an AVG refund take?",
    "How to cancel BullGuard subscription and get a refund?",
    "How do I cancel my BullGuard subscription?",
    "Can I get money back from BullGuard automatic renewal?",
    "Will I get money back if I cancel my Sophos subscription?",
    "How do I cancel my Sophos subscription?",
    "How much does Sophos cost per year?",
    "How do I get rid of Sophos?",
    "Can I get my money back after canceling F-Secure subscription?",
    "How do I cancel my F-Secure subscription?",
    "Can I get my money back from F-Secure subscriptions?",
    "Can I refund F-Secure subscription service?",
    "Can I cancel my ZoneAlarm subscription refund?",
    "How do I cancel my zone alarm subscription?",
    "What is better than ZoneAlarm?",
    "Can I cancel ZoneAlarm automatic renewal?",
    "Will I get a refund if I cancel my Comodo subscription?",
    "How do I cancel my Comodo subscription?",
    "What happened to Comodo antivirus?",
    "Is Comodo antivirus safe?",
    "How to cancel Proton VPN and get money back?",
    "Does Proton VPN offer refunds?",
    "Can I refund a Proton VPN subscription?",
    "How to get 30-day money back Proton VPN?",
    "How to cancel auto renewal in IPVanish?",
    "How do I completely cancel IPVanish subscription?",
    "What is the 1 800 number for IPVanish?",
    "Can I get a refund from IPVanish?",
    "How do I completely cancel Windscribe subscription?",
    "How do I deactivate my Windscribe account?",
    "How do I stop Windscribe?",
    "Is Windscribe shady?",
    "How can I cancel my TunnelBear subscription?",
    "How do I completely cancel TunnelBear subscription?",
    "How to quit TunnelBear?",
    "Why can't I cancel my TunnelBear subscription on my iPhone?",
    "How do I deactivate my IObit subscription?",
    "How to get rid of IObit?",
    "Can I cancel IObit automatic renewal?",
    "How do I cancel IObit subscription via my iPhone?",
    "Can I cancel my CleanMyMac subscription?",
    "How to quit CleanMyMac?",
    "How do I cancel my CleanMyMac subscription?",
    "How do I cancel my CleanMyMac subscription on Max?",
    "How do I cancel uBlock?",
    "How to deactivate uBlock Origin?",
    "Is Google killing uBlock Origin?",
    "How do I get rid of Ghostery?",
    "Is Ghostery a safe browser extension?",
    "How do I remove Ghostery adblock subscription?",
    "Does Ghostery cost money?",
    "How do I get rid of Sophos?"
]

# Deduplicate while preserving order
UNIQUE_TITLES = list(dict.fromkeys([t.strip() for t in TITLES if t.strip()]))

async def main():
    login_url = "https://login.proboards.com/login/2426311/1"
    username = "leomendis"
    password = "Rohit@123321#"
    target_url = "https://quaalude.proboards.com/thread/new/31"
    
    already_posted = 0
    if os.path.exists("quaalude_threads.txt"):
        with open("quaalude_threads.txt", "r", encoding="utf-8") as f:
            already_posted = len([line for line in f if line.strip()])

    total = len(UNIQUE_TITLES)
    safe_print(f"🚀 Starting Quaalude ProBoards batch run for {total} titles (Resuming from index {already_posted + 1})...")

    for idx, t_title in enumerate(UNIQUE_TITLES[already_posted:], already_posted + 1):
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
            with open("quaalude_threads.txt", "a", encoding="utf-8") as f:
                f.write(f"{link}\n")
        else:
            safe_print(f"[FAILED {idx}/{total}] {t_title} -> Error: {res.get('error')}")

if __name__ == "__main__":
    asyncio.run(main())
