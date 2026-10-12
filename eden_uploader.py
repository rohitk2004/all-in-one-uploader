import requests
import os
import sys
import time
import re
import random
from typing import List, Dict, Union, BinaryIO

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

DEFAULT_JOB_URL = "https://edenhospitality.com/job/dishwashers/"
UPLOAD_ENDPOINT = "https://edenhospitality.com/wp-admin/admin-ajax.php"
OUTPUT_LINKS_FILE = "eden_uploaded_links.txt"

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"

def upload_pdf_to_eden(
    file_source: Union[str, bytes, BinaryIO],
    filename: str = None,
    job_url: str = DEFAULT_JOB_URL,
    session: requests.Session = None
) -> Dict:
    """
    Uploads a PDF to Eden Hospitality WPJobBoard uploader and returns the live public URL.
    Supports file path (str), raw bytes (bytes), or file-like object.
    Generates a unique transient session ID for every upload to guarantee zero 'File upload limit reached' errors.
    """
    if session is None:
        session = requests.Session()

    headers = {
        "User-Agent": USER_AGENT,
        "Referer": job_url,
        "X-Requested-With": "XMLHttpRequest",
        "Accept": "application/json, text/javascript, */*; q=0.01"
    }

    try:
        # Determine filename and binary content
        if isinstance(file_source, str):
            if not filename:
                filename = os.path.basename(file_source)
            with open(file_source, "rb") as f:
                pdf_bytes = f.read()
        elif isinstance(file_source, bytes):
            if not filename:
                filename = f"document_{int(time.time())}.pdf"
            pdf_bytes = file_source
        else:
            # File-like object (e.g. Streamlit UploadedFile or BytesIO)
            if hasattr(file_source, "name") and not filename:
                filename = file_source.name
            if not filename:
                filename = f"document_{int(time.time())}.pdf"
            if hasattr(file_source, "getvalue"):
                pdf_bytes = file_source.getvalue()
            else:
                pdf_bytes = file_source.read()

        # Sanitize filename
        clean_filename = re.sub(r'[\\/*?:"<>|\s]+', '_', filename)
        if not clean_filename.lower().endswith(".pdf"):
            clean_filename += ".pdf"

        # Assign a fresh unique transient token for EVERY file to bypass WPJobBoard limit
        custom_tid = f"{int(time.time())}-{random.randint(1000, 9999)}"
        session.cookies.set("wpjb_transient_id", custom_tid, domain="edenhospitality.com", path="/")
        session.cookies.set("wpjb-apply-ref", "https%3A%2F%2Fedenhospitality.com%2Fjob%2Fdishwashers%2F", domain="edenhospitality.com", path="/")

        # Step 2: Post file to WPJobBoard AJAX upload endpoint
        payload = {
            "action": "wpjb_main_upload",
            "form": "Wpjb_Form_Apply",
            "form_code": "default",
            "object": "Wpjb_Model_Application",
            "field": "file",
            "id": "null",
            "name": clean_filename
        }

        files = {
            "file": (clean_filename, pdf_bytes, "application/pdf")
        }

        upload_resp = session.post(
            UPLOAD_ENDPOINT,
            headers=headers,
            data=payload,
            files=files,
            timeout=35
        )

        if upload_resp.status_code != 200:
            return {
                "success": False,
                "error": f"Upload HTTP status {upload_resp.status_code}",
                "filename": clean_filename
            }

        data = upload_resp.json()
        if data.get("result") == 1:
            live_url = data.get("url")
            file_size = data.get("size", len(pdf_bytes))
            
            # Save link to output file
            try:
                with open(OUTPUT_LINKS_FILE, "a", encoding="utf-8") as lf:
                    lf.write(f"{live_url}\n")
            except Exception:
                pass

            return {
                "success": True,
                "url": live_url,
                "filename": clean_filename,
                "size": file_size,
                "path": data.get("path", "")
            }
        else:
            return {
                "success": False,
                "error": data.get("msg", "Unknown upload error"),
                "filename": clean_filename
            }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "filename": filename or "unknown.pdf"
        }

def batch_upload_pdfs(
    files_list: List[Union[str, bytes, BinaryIO]],
    filenames: List[str] = None,
    job_url: str = DEFAULT_JOB_URL
) -> List[Dict]:
    """Uploads multiple PDFs sequentially and returns list of result dictionaries."""
    results = []
    total = len(files_list)
    print(f"[*] Starting Eden Hospitality batch upload for {total} file(s)...")

    for idx, item in enumerate(files_list, 1):
        fname = filenames[idx - 1] if filenames and idx - 1 < len(filenames) else None
        print(f"[*] Uploading file ({idx}/{total}): {fname or 'PDF'}...")
        res = upload_pdf_to_eden(item, filename=fname, job_url=job_url)
        results.append(res)
        if res.get("success"):
            print(f"[+] SUCCESS: {res.get('url')}")
        else:
            print(f"[-] FAILED: {res.get('error')}")

        if idx < total:
            time.sleep(1)

    return results

if __name__ == "__main__":
    test_pdf = "doc1.pdf"
    if not os.path.exists(test_pdf):
        with open(test_pdf, "wb") as f:
            f.write(b"%PDF-1.4 sample pdf content for verification")
            
    print(f"[*] Running test upload for {test_pdf}...")
    result = upload_pdf_to_eden(test_pdf, filename="dishwasher_applicant_resume.pdf")
    print("\nResult:")
    print(result)
