"""
UFL Invasion Science Institute - Affiliate PDF Uploader Bot
============================================================
Target Form URL: https://invasionscience.ufl.edu/affiliation/become-an-affiliate/
AJAX Endpoint:  https://invasionscience.ufl.edu/wp-admin/admin-ajax.php
Plugin / Engine: Forminator Custom Forms (Module ID: 1239)
"""

import os
import sys
import time
import re
import random
import requests
from bs4 import BeautifulSoup
import urllib3
from typing import List, Dict, Union, BinaryIO, Optional

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

FORM_PAGE_URL = "https://invasionscience.ufl.edu/affiliation/become-an-affiliate/"
AJAX_ENDPOINT = "https://invasionscience.ufl.edu/wp-admin/admin-ajax.php"
OUTPUT_LINKS_FILE = "ufl_uploaded_submissions.txt"

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/125.0.0.0 Safari/537.36"
)


def safe_print(*args, **kwargs):
    """Safe printer preventing Windows console character encoding crashes."""
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


def upload_pdf_to_ufl(
    file_source: Union[str, bytes, BinaryIO],
    filename: Optional[str] = None,
    name: str = "Dr. Alex Johnson",
    email: str = "affiliate.applicant@ufl.edu",
    title: str = "Assistant Professor of Invasion Ecology",
    institution: str = "University of Florida",
    research_notes: str = "Affiliation application with attached CV document.",
    session: Optional[requests.Session] = None,
) -> Dict:
    """
    Uploads a CV / Resume PDF file to University of Florida (UFL) Invasion Science Affiliate Form.
    Returns result dictionary with success status, submission details, and server response.
    
    Supports file path (str), raw bytes (bytes), or file-like object.
    """
    own_session = session is None
    if own_session:
        session = requests.Session()
        session.verify = False

    try:
        # Determine filename and binary content
        if isinstance(file_source, str):
            if not filename:
                filename = os.path.basename(file_source)
            with open(file_source, "rb") as f:
                pdf_bytes = f.read()
        elif isinstance(file_source, bytes):
            if not filename:
                filename = f"ufl_affiliate_cv_{int(time.time())}.pdf"
            pdf_bytes = file_source
        else:
            # File-like object (Streamlit UploadedFile or BytesIO)
            if hasattr(file_source, "name") and not filename:
                filename = file_source.name
            if not filename:
                filename = f"ufl_affiliate_cv_{int(time.time())}.pdf"
            if hasattr(file_source, "getvalue"):
                pdf_bytes = file_source.getvalue()
            else:
                pdf_bytes = file_source.read()

        # Sanitize filename
        clean_filename = re.sub(r'[\\/*?:"<>|\s]+', '_', filename)
        if not clean_filename.lower().endswith((".pdf", ".doc", ".docx")):
            clean_filename += ".pdf"

        headers = {
            "User-Agent": USER_AGENT,
            "Referer": FORM_PAGE_URL,
            "Origin": "https://invasionscience.ufl.edu"
        }

        # Step 1: GET form page to fetch page_id and fallback nonce
        res = session.get(FORM_PAGE_URL, headers=headers, timeout=30)
        if res.status_code != 200:
            return {
                "success": False,
                "error": f"Failed to load form page (HTTP {res.status_code})",
                "filename": clean_filename
            }

        soup = BeautifulSoup(res.text, "html.parser")
        form = soup.find("form", id=re.compile(r"forminator-module"))
        if not form:
            return {
                "success": False,
                "error": "Could not find Forminator form on UFL page",
                "filename": clean_filename
            }

        form_id_elem = form.find("input", {"name": "form_id"})
        page_id_elem = form.find("input", {"name": "page_id"})
        form_id = form_id_elem["value"] if form_id_elem else "1239"
        page_id = page_id_elem["value"] if page_id_elem else "532"

        # Step 2: Fetch fresh Forminator nonce
        nonce = None
        try:
            nonce_resp = session.post(
                AJAX_ENDPOINT,
                headers=headers,
                data={"action": "forminator_get_nonce", "form_id": form_id},
                timeout=15
            )
            if nonce_resp.status_code == 200:
                njson = nonce_resp.json()
                if njson.get("success"):
                    nonce = njson.get("data")
        except Exception:
            pass

        if not nonce:
            nonce_inp = form.find("input", {"name": "forminator_nonce"})
            nonce = nonce_inp["value"] if nonce_inp else ""

        # Step 3: Post file to Forminator multiple file upload action
        mime_type = "application/pdf"
        if clean_filename.lower().endswith(".docx"):
            mime_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        elif clean_filename.lower().endswith(".doc"):
            mime_type = "application/msword"

        files = {
            "file": (clean_filename, pdf_bytes, mime_type),
            "upload-1": (clean_filename, pdf_bytes, mime_type)
        }

        data = {
            "action": "forminator_multiple_file_upload",
            "form_id": form_id,
            "page_id": page_id,
            "element_id": "upload-1",
            "nonce": nonce,
            "forminator_nonce": nonce
        }

        submit_resp = session.post(AJAX_ENDPOINT, headers=headers, data=data, files=files, timeout=45)
        if submit_resp.status_code != 200:
            return {
                "success": False,
                "error": f"Submission failed with HTTP {submit_resp.status_code}",
                "filename": clean_filename
            }

        try:
            resp_json = submit_resp.json()
            data_obj = resp_json.get("data", {})
            file_url = data_obj.get("file_url") if isinstance(data_obj, dict) else None
            msg = data_obj.get("message") if isinstance(data_obj, dict) else str(data_obj)
            
            if resp_json.get("success") is True or (isinstance(data_obj, dict) and data_obj.get("success") is True):
                ref_link = file_url or f"https://invasionscience.ufl.edu/wp-content/uploads/forminator/{form_id}/{clean_filename}"
                try:
                    with open(OUTPUT_LINKS_FILE, "a", encoding="utf-8") as lf:
                        lf.write(f"{ref_link}\n")
                except Exception:
                    pass

                return {
                    "success": True,
                    "url": ref_link,
                    "message": msg or "File uploaded successfully!",
                    "filename": clean_filename,
                    "size": len(pdf_bytes),
                    "name": name,
                    "email": email,
                    "form_id": form_id,
                    "error": None
                }
            else:
                err_msg = msg or "Forminator returned error response"
                return {
                    "success": False,
                    "error": err_msg,
                    "filename": clean_filename,
                    "form_id": form_id,
                    "raw_response": resp_json
                }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to parse server response: {e}",
                "filename": clean_filename
            }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "filename": filename or "unknown.pdf"
        }
    finally:
        if own_session:
            session.close()


def batch_upload_pdfs(
    files_list: List[Union[str, bytes, BinaryIO]],
    filenames: Optional[List[str]] = None,
    names: Optional[List[str]] = None,
    email: str = "affiliate.applicant@ufl.edu"
) -> List[Dict]:
    """
    Uploads multiple CV / Resume PDFs sequentially to UFL Invasion Science Affiliate Form.
    Returns list of result dictionaries.
    """
    results = []
    total = len(files_list)
    print(f"[*] Starting UFL Invasion Science Affiliate batch upload for {total} file(s)...")

    with requests.Session() as session:
        session.verify = False

        for idx, item in enumerate(files_list, 1):
            fname = filenames[idx - 1] if filenames and idx - 1 < len(filenames) else None
            pname = names[idx - 1] if names and idx - 1 < len(names) else f"Dr. Applicant {idx}"
            
            print(f"[*] Submitting affiliate CV ({idx}/{total}): {fname or 'CV PDF'} [{pname}]...")
            
            res = upload_pdf_to_ufl(
                item,
                filename=fname,
                name=pname,
                email=email,
                session=session
            )
            results.append(res)

            if res.get("success"):
                print(f"[+] SUCCESS: {res.get('message')}")
            else:
                print(f"[-] RESPONSE: {res.get('error')}")

            if idx < total:
                time.sleep(1)

    return results


if __name__ == "__main__":
    test_pdf = "doc1.pdf"
    if not os.path.exists(test_pdf):
        with open(test_pdf, "wb") as f:
            f.write(b"%PDF-1.4 sample CV for UFL invasion science affiliate application")

    print(f"[*] Running test upload for {test_pdf} to UFL Invasion Science...")
    result = upload_pdf_to_ufl(test_pdf, filename="ufl_affiliate_resume.pdf")
    print("\nResult:")
    print(result)
