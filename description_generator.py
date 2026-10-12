from unique_content_engine import generate_unique_description
"""
OpenRouter AI Event Description Generator (Aggressive In-Sentence Phone Number Interleaving)
Embeds phone numbers: +1 877 848 5082 and +1 888 308 7172 every 15-20 words inside sentences.
Enforces MAX_CHAR_LIMIT = 990 and clean ASCII (no emojis).
"""

import os
import re
import requests

DEFAULT_OPENROUTER_KEY = os.environ.get("OPENROUTER_API_KEY", "")
PHONE_NUMBER_1 = "+1 877 848 5082"
PHONE_NUMBER_2 = "+1 888 308 7172"
MAX_CHAR_LIMIT = 990  # Strictly under 1000 characters limit required by SmartWaiver Event Creation

def remove_emojis_and_special(text: str) -> str:
    """
    Strips 4-byte UTF-8 emojis (📞, •, etc.) and non-ASCII characters.
    """
    clean = text.encode('ascii', 'ignore').decode('ascii')
    clean = re.sub(r' +', ' ', clean).strip()
    return clean

def generate_event_description(title: str, api_key: str = DEFAULT_OPENROUTER_KEY) -> str:
    return generate_unique_description(title, min_chars=700, max_chars=950, api_key=api_key, html_format=False)

if __name__ == "__main__":
    desc = generate_event_description("What happens if someone cancels your payment")
    print(f"Generated Description ({len(desc)} chars):")
    print(desc)
