import asyncio
import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from huggingface_bot import run_huggingface_multi_account_batch

ALL_TITLES = [
    "[Instant~Guide-] How to Cancel Total adblock Subscription", # 1 (skipped)
    "[Instant~Guide-] How to Cancel ccleaner Subscription",      # 2 (skipped)
    "[Instant~Guide-] How to Cancel surfshark Subscription",     # 3 (skipped)
    "[Instant~Guide-] How to Cancel webroot Subscription",       # 4 (skipped)
    "[Instant~Guide-] How to Cancel norton Subscription",       # 5 (START HERE)
    "[Instant~Guide-] How to Cancel mcafee Subscription",       # 6
    "[Instant~Guide-] How to Cancel total drive Subscription",   # 7
    "[Instant~Guide-] How to Cancel avast Subscription",         # 8
    "[Instant~Guide-] How to Cancel total adware Subscription",   # 9
    "[Instant~Guide-] How to Cancel express vpn Subscription",   # 10
    "[Instant~Guide-] How to Cancel At&t Subscription",          # 11
    "[Instant~Guide-] How to Cancel norton360 Subscription",     # 12
    'FaQ"S How to cancel Total adblock Subscription Quickly',    # 13
    'FaQ"S How to cancel ccleaner Subscription Quickly',        # 14
    'FaQ"S How to cancel surfshark Subscription Quickly',       # 15
    'FaQ"S How to cancel norton Subscription Quickly',          # 16
    'FaQ"S How to cancel mcafee Subscription Quickly',          # 17
    'FaQ"S How to cancel totalav Subscription Quickly'          # 18
]

# Skip starting 4 titles as requested by user
TARGET_TITLES = ALL_TITLES[4:]

ACCOUNTS = [
    {"email": "ZenithWolf@purelymail.com", "pass": "JameswarnertoUsa@321#321$321"},
    {"email": "GhostReign@purelymail.com", "pass": "JameswarnertoUsa@321#321$321"},
    {"email": "QuantumBlade@purelymail.com", "pass": "JameswarnertoUsa@321#321$321"}
]

async def main():
    await run_huggingface_multi_account_batch(
        titles=TARGET_TITLES,
        accounts=ACCOUNTS,
        max_posts_per_account=2,
        output_file="huggingface_batch_links.txt"
    )

if __name__ == "__main__":
    asyncio.run(main())
