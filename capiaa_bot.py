"""
CAPIAA Certificate PDF Upload Bot
Automates uploading single or bulk PDF files to https://capiaa.ca.gov/certificate/
Extracts the encoded public link (wp-content%2Fuploads...) for easy copy-pasting.
Includes 120s wait for manual browser VPN extension activation.
"""

import asyncio
import json
import os
import zipfile
import tempfile
import argparse
from typing import Dict, Any, List
import requests
from playwright.async_api import async_playwright

CAPIAA_URL = "https://capiaa.ca.gov/certificate/"
CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

def format_encoded_url(raw_url: str) -> str:
    """
    Encodes path slashes (%2F) to construct direct downloadable link.
    """
    if not raw_url:
        return ""
    return raw_url.replace(
        "wp-content/uploads/sites/16/wpforms/tmp/",
        "wp-content%2Fuploads%2Fsites%2F16%2Fwpforms%2Ftmp/"
    )

async def handle_cloudflare_challenge(page, timeout_sec: int = 120) -> bool:
    """
    Waits up to 120 seconds for the user to turn on their VPN extension
    or complete Cloudflare verification until the CAPIAA certificate form appears.
    """
    print("[*] Waiting for CAPIAA certificate form to load (Connect Chrome VPN extension if needed)...")
    for step in range(timeout_sec):
        try:
            file_input_count = await page.locator("input.dz-hidden-input, input[type='file'], #wpforms-7095-field_38").count()
            if file_input_count > 0:
                print("[+] CAPIAA certificate form detected & ready!")
                return True

            page_title = await page.title()
            page_content = await page.content()

            if "403 Forbidden" in page_title or "403 Forbidden" in page_content or "Access Denied" in page_content:
                if step % 5 == 0:
                    print(f"[*] Page showing 403 Forbidden ({step}s/120s). Please turn ON your Chrome VPN extension in the open browser window...")

            if "Just a moment" in page_title or "Verifying you are human" in page_content or "cf-challenge" in page_content:
                if step % 5 == 0:
                    print(f"[*] Cloudflare verification active ({step}s/120s)...")
            
            await page.wait_for_timeout(1000)
        except Exception:
            await page.wait_for_timeout(1000)

    return False

async def upload_single_pdf(page, abs_pdf_path: str) -> Dict[str, Any]:
    """Uploads a single PDF using an existing Playwright page context."""
    file_basename = os.path.basename(abs_pdf_path)
    captured_upload_data = {}

    async def handle_response(response):
        if "admin-ajax.php" in response.url:
            try:
                text = await response.text()
                if '"success":true' in text and '"file"' in text:
                    data = json.loads(text)
                    if data.get("success") and "data" in data:
                        captured_upload_data.update(data["data"])
            except Exception:
                pass

    response_listener = page.on("response", handle_response)

    try:
        print(f"[*] Navigating to {CAPIAA_URL} for file: '{file_basename}'...")
        try:
            await page.goto(CAPIAA_URL, wait_until="domcontentloaded", timeout=45000)
        except Exception:
            pass

        # Wait up to 120s for user to toggle VPN extension if needed
        form_ready = await handle_cloudflare_challenge(page, timeout_sec=120)

        if not form_ready:
            # Final check before failing
            file_input_count = await page.locator("input.dz-hidden-input, input[type='file']").count()
            if file_input_count == 0:
                return {
                    "success": False,
                    "file_name": file_basename,
                    "encoded_url": None,
                    "error": "Form not loaded. Ensure VPN extension is connected to US location."
                }

        file_input = page.locator("input.dz-hidden-input, input[type='file']").first
        await file_input.wait_for(state="attached", timeout=30000)
        await file_input.set_input_files(abs_pdf_path)
        print(f"[*] File '{file_basename}' sent to dropzone, waiting for AJAX upload completion...")

        for _ in range(40):
            await page.wait_for_timeout(500)
            if captured_upload_data.get("url"):
                break

        dz_field_val = await page.evaluate("""() => {
            const el = document.getElementById('wpforms-7095-field_38');
            return el ? el.value : '';
        }""")

        raw_url = captured_upload_data.get("url")
        if not raw_url and dz_field_val:
            try:
                parsed = json.loads(dz_field_val)
                if isinstance(parsed, list) and len(parsed) > 0:
                    raw_url = parsed[0].get("url")
            except Exception:
                pass

        if raw_url:
            encoded_url = format_encoded_url(raw_url)
            print(f"[+] UPLOAD SUCCESS FOR '{file_basename}': {encoded_url}")
            return {
                "success": True,
                "file_name": file_basename,
                "encoded_url": encoded_url,
                "error": None
            }
        else:
            return {
                "success": False,
                "file_name": file_basename,
                "encoded_url": None,
                "error": "No URL returned from server"
            }
    except Exception as e:
        return {
            "success": False,
            "file_name": file_basename,
            "encoded_url": None,
            "error": str(e)
        }

async def upload_pdf_to_capiaa(pdf_file_path: str, headless: bool = False, proxy_url: str = None) -> Dict[str, Any]:
    """Single file upload helper with stealth browser launch."""
    async with async_playwright() as p:
        launch_kwargs = {
            "headless": headless,
            "executable_path": CHROME_PATH if os.path.exists(CHROME_PATH) else None,
            "channel": "chrome" if not os.path.exists(CHROME_PATH) else None,
            "args": [
                "--disable-blink-features=AutomationControlled",
                "--start-maximized"
            ]
        }
        if proxy_url and proxy_url.strip():
            launch_kwargs["proxy"] = {"server": proxy_url.strip()}

        browser = await p.chromium.launch(**launch_kwargs)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport=None
        )
        await context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        page = await context.new_page()
        res = await upload_single_pdf(page, pdf_file_path)
        await browser.close()
        return res

async def upload_bulk_pdfs(pdf_file_paths: List[str], headless: bool = False, proxy_url: str = None) -> List[Dict[str, Any]]:
    """Uploads multiple PDF files sequentially with stealth browser configuration."""
    results = []
    async with async_playwright() as p:
        launch_kwargs = {
            "headless": headless,
            "executable_path": CHROME_PATH if os.path.exists(CHROME_PATH) else None,
            "channel": "chrome" if not os.path.exists(CHROME_PATH) else None,
            "args": [
                "--disable-blink-features=AutomationControlled",
                "--start-maximized"
            ]
        }
        if proxy_url and proxy_url.strip():
            launch_kwargs["proxy"] = {"server": proxy_url.strip()}

        browser = await p.chromium.launch(**launch_kwargs)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport=None
        )
        await context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        page = await context.new_page()
        for pdf_path in pdf_file_paths:
            res = await upload_single_pdf(page, pdf_path)
            results.append(res)
        await browser.close()
    return results

def process_uploaded_files(uploaded_files) -> List[str]:
    """Processes uploaded PDF or ZIP files and returns a list of local PDF file paths."""
    extracted_pdf_paths = []
    temp_dir = tempfile.mkdtemp()

    for file_obj in uploaded_files:
        name = file_obj.name.lower()
        if name.endswith(".pdf"):
            path = os.path.join(temp_dir, file_obj.name)
            with open(path, "wb") as f:
                f.write(file_obj.getbuffer())
            extracted_pdf_paths.append(path)
        elif name.endswith(".zip"):
            zip_path = os.path.join(temp_dir, file_obj.name)
            with open(zip_path, "wb") as f:
                f.write(file_obj.getbuffer())
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                for member in zip_ref.namelist():
                    if member.lower().endswith(".pdf") and not member.startswith("__MACOSX"):
                        extracted_path = zip_ref.extract(member, temp_dir)
                        extracted_pdf_paths.append(extracted_path)

    return extracted_pdf_paths

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Upload PDF to CAPIAA Certificate form & get public URL")
    parser.add_argument("--file", type=str, required=True, help="Path to PDF file")
    parser.add_argument("--headful", action="store_true", help="Run browser in headful mode")
    parser.add_argument("--proxy", type=str, default="", help="Proxy URL (e.g. http://ip:port)")
    args = parser.parse_args()

    async def main():
        print(f"Uploading {args.file} to {CAPIAA_URL}...")
        res = await upload_pdf_to_capiaa(args.file, headless=not args.headful, proxy_url=args.proxy)
        print("\n--- UPLOAD RESULT ---")
        print(json.dumps(res, indent=2))

    asyncio.run(main())
