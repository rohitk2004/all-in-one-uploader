import urllib.request
import re
from html import unescape

def extract_proboards_post(url):
    req = urllib.request.Request(
        url, 
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    )
    try:
        with urllib.request.urlopen(req) as response:
            html = response.read().decode('utf-8', errors='ignore')
            
            # Extract Subject title
            title_match = re.search(r'<title>(.*?)</title>', html, re.DOTALL | re.IGNORECASE)
            raw_title = title_match.group(1).strip() if title_match else ""
            clean_title = unescape(raw_title).split('|')[0].strip()
            
            # Extract message content div
            message_match = re.search(r'<article[^>]*class="[^"]*message[^"]*"[^>]*>(.*?)</article>', html, re.DOTALL | re.IGNORECASE)
            if not message_match:
                message_match = re.search(r'<div[^>]*class="[^"]*message[^"]*"[^>]*>(.*?)</div>', html, re.DOTALL | re.IGNORECASE)
                
            if message_match:
                content_html = message_match.group(1)
                # Replace <br> and <p> with newlines
                content_html = re.sub(r'<br\s*/?>', '\n', content_html, flags=re.IGNORECASE)
                content_html = re.sub(r'</p>', '\n\n', content_html, flags=re.IGNORECASE)
                content_text = re.sub(r'<[^>]+>', '', content_html)
                clean_content = unescape(content_text).strip()
            else:
                clean_content = ""

            return clean_title, clean_content
    except Exception as e:
        return "", f"Error: {e}"

if __name__ == "__main__":
    urls = [
        "https://adminus.freeforums.net/thread/49/faqs-explained-install-after-purchase",
        "https://adminus.freeforums.net/thread/50/validate-mcafee-license-key-errors"
    ]
    for url in urls:
        t, c = extract_proboards_post(url)
        print("="*70)
        print(f"URL: {url}")
        print(f"TITLE: {t}")
        print("-" * 70)
        print(f"CONTENT:\n{c}")
        print("="*70 + "\n")
