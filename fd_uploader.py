"""
FD.org PDF Uploader Bot
======================
Target URL: https://www.fd.org/employment/post-a-vacancy#no-back

Description:
  Automates PDF file uploads to the FD.org vacancy submission webform,
  extracting and verifying live public attachment URLs:
  https://www.fd.org/sites/default/files/public/webform/post_a_vacancy/_sid_/<filename>.pdf
"""

import asyncio
import os
import sys
import re
import argparse
import urllib3
import requests
from typing import Dict, Any, Optional
from playwright.async_api import async_playwright

urllib3.disable_warnings()

SITE_URL = "https://www.fd.org"
FORM_URL = f"{SITE_URL}/employment/post-a-vacancy#no-back"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/126.0.0.0 Safari/537.36"
    )
}

async def upload_pdf_to_fd(pdf_path: str, timeout_sec: int = 60) -> Dict[str, Any]:
    """
    Uploads a PDF file to fd.org vacancy webform via Playwright browser automation.
    Returns a dictionary with status, live public URL, and metadata.
    """
    abs_pdf_path = os.path.abspath(pdf_path)
    if not os.path.exists(abs_pdf_path):
        return {
            "success": False,
            "error": f"File not found: {abs_pdf_path}",
            "public_url": None
        }

    filename = os.path.basename(abs_pdf_path)
    print(f"[*] Starting upload for: '{filename}'")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent=HEADERS["User-Agent"])
        page = await context.new_page()

        try:
            print(f"[*] Navigating to {FORM_URL}...")
            await page.goto(FORM_URL, wait_until="networkidle", timeout=timeout_sec * 1000)

            # Locate file input element
            file_input = page.locator("input[name='files[attachment]']")
            await file_input.wait_for(state="attached", timeout=15000)

            print(f"[*] Selecting file: {filename}")
            await file_input.set_input_files(abs_pdf_path)

            print("[*] Triggering upload process...")
            await page.evaluate("() => { const btn = document.querySelector('#edit-attachment-upload-button'); if (btn) btn.click(); }")

            # Wait for AJAX response and link rendering
            print("[*] Waiting for server response...")
            await page.wait_for_timeout(7000)

            # Extract uploaded link from #edit-attachment
            file_link_loc = page.locator("#edit-attachment a, .messages--status a, div[role='contentinfo'] a")
            public_url = None

            if await file_link_loc.count() > 0:
                href = await file_link_loc.first.get_attribute("href")
                if href:
                    if href.startswith("http"):
                        public_url = href
                    else:
                        public_url = f"{SITE_URL}{href}"

            # Fallback: scan page HTML content for PDF URLs matching webform path pattern
            if not public_url:
                html = await page.content()
                matches = re.findall(r'/sites/default/files/public/webform/post_a_vacancy/_sid_/[^\s"\'<>]+\.pdf', html)
                if matches:
                    public_url = f"{SITE_URL}{matches[0]}"

            await browser.close()

            if not public_url:
                return {
                    "success": False,
                    "error": "Upload failed or link not returned by server",
                    "public_url": None
                }

            # Verify public accessibility
            print(f"[*] Verifying live URL accessibility: {public_url}")
            ver_resp = requests.get(public_url, headers=HEADERS, timeout=15)
            if ver_resp.status_code == 200:
                print(f"[+] SUCCESS! Verified Live URL: {public_url}")
                return {
                    "success": True,
                    "filename": filename,
                    "public_url": public_url,
                    "status_code": ver_resp.status_code,
                    "size_bytes": len(ver_resp.content),
                    "error": None
                }
            else:
                return {
                    "success": False,
                    "filename": filename,
                    "public_url": public_url,
                    "error": f"Verification failed with HTTP status {ver_resp.status_code}"
                }

        except Exception as e:
            await browser.close()
            return {
                "success": False,
                "filename": filename,
                "public_url": None,
                "error": str(e)
            }

def main():
    parser = argparse.ArgumentParser(description="FD.org PDF Uploader Bot")
    parser.add_argument("--file", "-f", default="real_valid_document.pdf", help="Path to PDF file to upload")
    args = parser.parse_args()

    result = asyncio.run(upload_pdf_to_fd(args.file))
    print("\n" + "="*50)
    if result.get("success"):
        print(f"[SUCCESS] Upload completed successfully!")
        print(f"File Name: {result.get('filename')}")
        print(f"Public Link: {result.get('public_url')}")
        print(f"File Size: {result.get('size_bytes')} bytes")
    else:
        print(f"[ERROR] Upload failed: {result.get('error')}")
    print("="*50)

if __name__ == "__main__":
    main()
