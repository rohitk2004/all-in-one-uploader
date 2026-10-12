"""
USP (Instituto de Química - Universidade de São Paulo) File Uploader
=====================================================================
Target Form Page: https://www.iq.usp.br/farmdna/abstracts-form.html
Target Endpoint:  https://www.iq.usp.br/farmdna/abstracts-to-email.php

Public Link Format (Reference):
  https://www.iq.usp.br/portaliqusp/sites/default/files/webform/anexos/<filename>

Reference Links:
  https://www.iq.usp.br/portaliqusp/sites/default/files/webform/anexos/grow2.pdf
  https://www.iq.usp.br/portaliqusp/sites/default/files/webform/anexos/aeromexicopromote.pdf
"""

import os
import time
import requests
import urllib3
from typing import Optional

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

SITE_URL = "https://www.iq.usp.br"
FORM_PAGE_URL = f"{SITE_URL}/farmdna/abstracts-form.html"
UPLOAD_ENDPOINT = f"{SITE_URL}/farmdna/abstracts-to-email.php"
PUBLIC_LINK_BASE = f"{SITE_URL}/portaliqusp/sites/default/files/webform/anexos"

MIME_TYPES = {
    ".pdf": "application/pdf",
    ".zip": "application/zip",
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    ),
    "Referer": FORM_PAGE_URL,
    "Origin": SITE_URL,
}

def _get_mime(filename: str) -> str:
    ext = os.path.splitext(filename)[1].lower()
    return MIME_TYPES.get(ext, "application/octet-stream")


def upload_file(file_path: str, session: Optional[requests.Session] = None) -> dict:
    """
    Upload a single PDF/ZIP file to USP abstracts form.
    Returns result dict: { success, file_name, public_url, error }
    """
    own_session = session is None
    if own_session:
        session = requests.Session()
        session.verify = False

    try:
        file_name = os.path.basename(file_path)
        mime_type = _get_mime(file_name)
        public_url = f"{PUBLIC_LINK_BASE}/{file_name}"

        print(f"[*] Uploading '{file_name}' [{mime_type}] to USP...")

        with open(file_path, "rb") as f:
            file_bytes = f.read()

        files = [
            ("uploaded_file[]", (file_name, file_bytes, mime_type)),
            ("uploaded_file[]", (f"proof_{file_name}", file_bytes, mime_type))
        ]

        data = {
            "firstname": "Academic",
            "surname": "Researcher",
            "email": "researcher.abstracts@usp.br"
        }

        resp = session.post(
            UPLOAD_ENDPOINT,
            data=data,
            files=files,
            headers=HEADERS,
            timeout=45
        )

        if resp.status_code in (200, 201, 302):
            print(f"[+] SUCCESS: {public_url}")
            return {
                "success": True,
                "file_name": file_name,
                "public_url": public_url,
                "error": None
            }
        else:
            print(f"[-] FAILED with HTTP {resp.status_code}")
            return {
                "success": False,
                "file_name": file_name,
                "public_url": None,
                "error": f"HTTP {resp.status_code}"
            }

    except Exception as e:
        file_name = os.path.basename(file_path)
        err_msg = f"Connection Timeout / Server Unreachable: {e}"
        print(f"[-] Upload failed ({file_name}): {err_msg}")
        return {
            "success": False,
            "file_name": file_name,
            "public_url": None,
            "error": err_msg
        }
    finally:
        if own_session:
            session.close()


def batch_upload_files(file_paths: list, start_index: int = 1):
    """
    Upload multiple PDF/ZIP files to USP form sharing one session.
    GENERATOR: yields each result immediately as each file finishes uploading.
    """
    start_idx = max(1, start_index) - 1
    files_to_process = file_paths[start_idx:]

    with requests.Session() as session:
        session.verify = False

        for idx_offset, fp in enumerate(files_to_process):
            file_name = os.path.basename(fp)
            mime_type = _get_mime(file_name)
            public_url = f"{PUBLIC_LINK_BASE}/{file_name}"
            current_num = start_idx + idx_offset + 1

            print(f"\n[*] Uploading USP file ({current_num}/{len(file_paths)}): '{file_name}'...")

            uploaded = False
            last_err = None

            for attempt in range(1, 3):
                try:
                    with open(fp, "rb") as f:
                        file_bytes = f.read()

                    files = [
                        ("uploaded_file[]", (file_name, file_bytes, mime_type)),
                        ("uploaded_file[]", (f"proof_{file_name}", file_bytes, mime_type))
                    ]

                    data = {
                        "firstname": "Academic",
                        "surname": "Researcher",
                        "email": "abstracts.submission@usp.br"
                    }

                    resp = session.post(
                        UPLOAD_ENDPOINT,
                        data=data,
                        files=files,
                        headers=HEADERS,
                        timeout=15
                    )

                    if resp.status_code in (200, 201, 302):
                        print(f"[+] SUCCESS: {public_url}")
                        yield {
                            "success": True,
                            "file_name": file_name,
                            "public_url": public_url,
                            "error": None
                        }
                        uploaded = True
                        break
                    else:
                        last_err = f"HTTP {resp.status_code}"
                        time.sleep(1)

                except Exception as e:
                    last_err = str(e)
                    time.sleep(1)

            if not uploaded:
                yield {
                    "success": False,
                    "file_name": file_name,
                    "public_url": None,
                    "error": f"Server Unreachable / Timeout ({last_err})"
                }
