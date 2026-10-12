"""
HSSET Job Application File Uploader
=====================================
Uploads PDF and ZIP files to:
  https://humanesocietyofsoutheasttexas.org/job-application/

Uses the Drag-and-Drop CF7 plugin's AJAX endpoint:
  POST https://humanesocietyofsoutheasttexas.org/wp-admin/admin-ajax.php
  action=dnd_codedropz_upload

Returns the public file URL:
  https://humanesocietyofsoutheasttexas.org/wp-content/uploads/
  wp_dndcf7_uploads/wpcf7-files/<uuid>/<filename>

No form submission required.
"""

import uuid
import re
import os
import requests
from typing import Optional

SITE_URL = "https://humanesocietyofsoutheasttexas.org"
PAGE_URL = f"{SITE_URL}/job-application/"
AJAX_URL = f"{SITE_URL}/wp-admin/admin-ajax.php"
UPLOAD_BASE = f"{SITE_URL}/wp-content/uploads/wp_dndcf7_uploads/wpcf7-files"

FORM_ID = "1759"
UPLOAD_NAME = "UploadYourResume"

MIME_TYPES = {
    ".pdf": "application/pdf",
    ".zip": "application/zip",
}

def _get_mime(filename: str) -> str:
    ext = os.path.splitext(filename)[1].lower()
    return MIME_TYPES.get(ext, "application/octet-stream")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    ),
    "Referer": PAGE_URL,
    "Origin": SITE_URL,
}

def _get_fresh_nonce(session: requests.Session) -> str:
    """
    Load the job-application page and extract the latest ajax_nonce
    from the dnd_cf7_uploader JS variable.
    """
    try:
        r = session.get(PAGE_URL, headers=HEADERS, timeout=20)
        r.raise_for_status()
        m = re.search(r'"ajax_nonce"\s*:\s*"([a-f0-9]+)"', r.text)
        if m:
            return m.group(1)
        m = re.search(r"ajax_nonce['\"]?\s*:\s*['\"]([a-f0-9]+)['\"]", r.text)
        if m:
            return m.group(1)
    except Exception as e:
        print(f"[!] Warning: could not fetch fresh nonce ({e})")
    return ""


def upload_pdf(file_path: str, session: Optional[requests.Session] = None) -> dict:
    """
    Upload a single PDF file. Returns:
      { success, file_name, upload_folder, public_url, error }
    """
    own_session = session is None
    if own_session:
        session = requests.Session()

    try:
        nonce = _get_fresh_nonce(session)
        upload_folder = str(uuid.uuid4())
        token = str(uuid.uuid4())
        file_name = os.path.basename(file_path)
        mime_type = _get_mime(file_name)

        print(f"[*] Uploading '{file_name}' [{mime_type}] (folder={upload_folder[:8]}...)...")
        with open(file_path, "rb") as f:
            file_data = f.read()

        form_data = {
            "action":        (None, "dnd_codedropz_upload"),
            "type":          (None, "click"),
            "security":      (None, nonce),
            "form_id":       (None, FORM_ID),
            "upload_name":   (None, UPLOAD_NAME),
            "upload_folder": (None, upload_folder),
            "token":         (None, token),
            "upload-file":   (file_name, file_data, mime_type),
        }

        resp = session.post(
            AJAX_URL,
            files=form_data,
            headers={k: v for k, v in HEADERS.items() if k != "Content-Type"},
            timeout=60,
        )
        resp.raise_for_status()
        data = resp.json()

        if data.get("success"):
            path = data["data"].get("path", upload_folder)
            fname = data["data"].get("file", file_name)
            public_url = f"{UPLOAD_BASE}/{path}/{fname}"
            print(f"[+] SUCCESS: {public_url}")
            return {"success": True,  "file_name": file_name, "upload_folder": path,
                    "public_url": public_url, "error": None}
        else:
            err = data.get("data", {})
            msg = err if isinstance(err, str) else str(err)
            return {"success": False, "file_name": file_name, "upload_folder": upload_folder,
                    "public_url": None, "error": msg}

    except Exception as e:
        return {"success": False, "file_name": os.path.basename(file_path),
                "upload_folder": "", "public_url": None, "error": str(e)}
    finally:
        if own_session:
            session.close()


def batch_upload_pdfs(file_paths: list, start_index: int = 1):
    """
    Upload multiple PDF/ZIP files sharing one session with automatic nonce refresh & retry.
    GENERATOR: yields each result immediately as each file finishes uploading.
    """
    import time

    start_idx = max(1, start_index) - 1
    files_to_process = file_paths[start_idx:]

    with requests.Session() as session:
        nonce = _get_fresh_nonce(session)
        print(f"[*] Batch nonce: {nonce or '(empty)'}")

        for idx_offset, fp in enumerate(files_to_process):
            file_name = os.path.basename(fp)
            upload_folder = str(uuid.uuid4())
            token = str(uuid.uuid4())
            mime_type = _get_mime(file_name)

            # Refresh nonce every 30 files to prevent expiration during large batches
            if idx_offset > 0 and idx_offset % 30 == 0:
                fresh = _get_fresh_nonce(session)
                if fresh:
                    nonce = fresh
                    print(f"[*] Refreshing nonce for file #{start_idx + idx_offset + 1}: {nonce}")

            print(f"\n[*] Uploading '{file_name}' ({start_idx + idx_offset + 1}/{len(file_paths)})...")

            uploaded = False
            last_err = None

            # Retry up to 3 times per file
            for attempt in range(1, 4):
                try:
                    with open(fp, "rb") as f:
                        file_data = f.read()

                    form_data = {
                        "action":        (None, "dnd_codedropz_upload"),
                        "type":          (None, "click"),
                        "security":      (None, nonce),
                        "form_id":       (None, FORM_ID),
                        "upload_name":   (None, UPLOAD_NAME),
                        "upload_folder": (None, upload_folder),
                        "token":         (None, token),
                        "upload-file":   (file_name, file_data, mime_type),
                    }

                    resp = session.post(
                        AJAX_URL,
                        files=form_data,
                        headers={k: v for k, v in HEADERS.items() if k != "Content-Type"},
                        timeout=60,
                    )
                    resp.raise_for_status()
                    data = resp.json()

                    if data.get("success"):
                        path = data["data"].get("path", upload_folder)
                        fname = data["data"].get("file", file_name)
                        public_url = f"{UPLOAD_BASE}/{path}/{fname}"
                        print(f"[+] SUCCESS: {public_url}")
                        yield {"success": True, "file_name": file_name,
                               "upload_folder": path, "public_url": public_url, "error": None}
                        uploaded = True
                        break
                    else:
                        err_msg = str(data.get("data", ""))
                        last_err = err_msg
                        print(f"[!] Attempt {attempt} failed: {err_msg}")

                        # If nonce error, immediately refresh nonce for retry
                        if "nonce" in err_msg.lower() or "security" in err_msg.lower() or "expired" in err_msg.lower():
                            fresh = _get_fresh_nonce(session)
                            if fresh:
                                nonce = fresh

                        time.sleep(1.5)

                except Exception as e:
                    last_err = str(e)
                    print(f"[!] Attempt {attempt} exception: {e}")
                    # Fetch fresh nonce on network exception
                    fresh = _get_fresh_nonce(session)
                    if fresh:
                        nonce = fresh
                    time.sleep(2)

            if not uploaded:
                yield {"success": False, "file_name": file_name,
                       "upload_folder": upload_folder, "public_url": None, "error": last_err or "Failed after 3 attempts"}
