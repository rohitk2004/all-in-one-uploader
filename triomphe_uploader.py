"""
Triomphe de l'Art - Competition Application PDF/ZIP Uploader
=============================================================
Uploads files to:
  https://triomphedelart.org/language/en/international-music-competition/
  xi-international-music-competition-triomphe-de-lart-string-instruments-chamber-music/apply-2026/

Uses Drag-and-Drop CF7 AJAX endpoint:
  POST https://triomphedelart.org/wp-admin/admin-ajax.php
  action=dnd_codedropz_upload (with nonce as security token)

Returns public file URL:
  https://triomphedelart.org/wp-content/uploads/wp_dndcf7_uploads/wpcf7-files/<filename>

Reference URL: https://triomphedelart.org/wp-content/uploads/wp_dndcf7_uploads/wpcf7-files/usa16.pdf
"""

import uuid
import re
import os
import requests
from typing import Optional

SITE_URL  = "https://triomphedelart.org"
PAGE_URL  = (
    f"{SITE_URL}/language/en/international-music-competition/"
    "xi-international-music-competition-triomphe-de-lart-string-instruments-chamber-music/apply-2026/"
)
AJAX_URL     = f"{SITE_URL}/wp-admin/admin-ajax.php"
UPLOAD_BASE  = f"{SITE_URL}/wp-content/uploads/wp_dndcf7_uploads/wpcf7-files"

FORM_ID      = "7868"
UPLOAD_ACTION = "dnd_codedropz_upload"

MIME_TYPES = {
    ".pdf": "application/pdf",
    ".zip": "application/zip",
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
    ),
    "Referer": PAGE_URL,
    "Origin":  SITE_URL,
}


def _get_mime(filename: str) -> str:
    ext = os.path.splitext(filename)[1].lower()
    return MIME_TYPES.get(ext, "application/octet-stream")


def _get_fresh_nonce(session: requests.Session) -> str:
    """Fetch live nonce from the apply-2026 page."""
    try:
        r = session.get(PAGE_URL, headers=HEADERS, timeout=25)
        r.raise_for_status()
        # The nonce is the ajax_nonce inside dnd_cf7_uploader object
        m = re.search(r'"ajax_nonce"\s*:\s*"([^"]+)"', r.text)
        if m:
            return m.group(1)
    except Exception as e:
        print(f"[!] Could not fetch nonce: {e}")
    return ""


def _build_url(data: dict, filename: str) -> str:
    """
    Build the correct public URL from the server response.
    The server returns path='wpcf7-files' (already in UPLOAD_BASE), so we skip it.
    Final URL: UPLOAD_BASE/<filename>
    """
    path = data.get("path", "")
    fname = data.get("file", filename)
    # If path is 'wpcf7-files', it's already in UPLOAD_BASE — don't duplicate
    if path and path not in ("wpcf7-files", "wpcf7-files/"):
        return f"{UPLOAD_BASE}/{path}/{fname}"
    return f"{UPLOAD_BASE}/{fname}"


def upload_file(file_path: str, session: Optional[requests.Session] = None) -> dict:
    """
    Upload a single PDF/ZIP file to Triomphe de l'Art.
    Returns: { success, file_name, public_url, error }
    """
    own_session = session is None
    if own_session:
        session = requests.Session()

    try:
        nonce = _get_fresh_nonce(session)
        token = str(uuid.uuid4())
        file_name = os.path.basename(file_path)
        mime_type = _get_mime(file_name)

        print(f"[*] Uploading '{file_name}' [{mime_type}]...")
        with open(file_path, "rb") as f:
            file_data = f.read()

        form_data = {
            "action":        (None, UPLOAD_ACTION),
            "type":          (None, "click"),
            "security":      (None, nonce),
            "form_id":       (None, FORM_ID),
            "upload_folder": (None, str(uuid.uuid4())),
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
            public_url = _build_url(data["data"], file_name)
            print(f"[+] SUCCESS: {public_url}")
            return {"success": True,  "file_name": file_name, "public_url": public_url, "error": None}
        else:
            msg = data.get("data", "Unknown error")
            if isinstance(msg, dict):
                msg = str(msg)
            print(f"[-] FAILED: {msg}")
            return {"success": False, "file_name": file_name, "public_url": None, "error": msg}

    except Exception as e:
        print(f"[-] Exception: {e}")
        return {"success": False, "file_name": os.path.basename(file_path),
                "public_url": None, "error": str(e)}
    finally:
        if own_session:
            session.close()


def batch_upload_files(file_paths: list, start_index: int = 1):
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
            mime_type = _get_mime(file_name)
            token = str(uuid.uuid4())

            # Refresh nonce every 30 files
            if idx_offset > 0 and idx_offset % 30 == 0:
                fresh = _get_fresh_nonce(session)
                if fresh:
                    nonce = fresh
                    print(f"[*] Refreshing nonce for file #{start_idx + idx_offset + 1}: {nonce}")

            print(f"\n[*] Uploading '{file_name}' ({start_idx + idx_offset + 1}/{len(file_paths)})...")

            uploaded = False
            last_err = None

            for attempt in range(1, 4):
                try:
                    with open(fp, "rb") as f:
                        file_data = f.read()

                    form_data = {
                        "action":        (None, UPLOAD_ACTION),
                        "type":          (None, "click"),
                        "security":      (None, nonce),
                        "form_id":       (None, FORM_ID),
                        "upload_folder": (None, str(uuid.uuid4())),
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
                        public_url = _build_url(data["data"], file_name)
                        print(f"[+] SUCCESS: {public_url}")
                        yield {"success": True, "file_name": file_name,
                               "public_url": public_url, "error": None}
                        uploaded = True
                        break
                    else:
                        msg = data.get("data", "Unknown error")
                        if isinstance(msg, dict):
                            msg = str(msg)
                        last_err = msg
                        print(f"[!] Attempt {attempt} failed: {msg}")

                        if "nonce" in msg.lower() or "security" in msg.lower() or "expired" in msg.lower():
                            fresh = _get_fresh_nonce(session)
                            if fresh:
                                nonce = fresh

                        time.sleep(1.5)

                except Exception as e:
                    last_err = str(e)
                    print(f"[!] Attempt {attempt} exception: {e}")
                    fresh = _get_fresh_nonce(session)
                    if fresh:
                        nonce = fresh
                    time.sleep(2)

            if not uploaded:
                yield {"success": False, "file_name": file_name,
                       "public_url": None, "error": last_err or "Failed after 3 attempts"}
