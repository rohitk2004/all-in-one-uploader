"""
USAL Digitalstack Matricula PDF Uploader Bot
==============================================
Target Form URL: https://digitalstack.usal.es/matricula
Target AJAX Endpoint: https://digitalstack.usal.es/file/ajax/field_justificante_del_pago/und/0/<form_build_id>
Public Link Format: https://digitalstack.usal.es/sites/default/files/matriculas/<filename>
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

# Disable SSL verification warnings for USAL certificate issue
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

FORM_URL = "https://digitalstack.usal.es/matricula"
PUBLIC_BASE_URL = "https://digitalstack.usal.es/sites/default/files/matriculas"
OUTPUT_LINKS_FILE = "usal_uploaded_links.txt"

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/125.0.0.0 Safari/537.36"
)


def safe_print(*args, **kwargs):
    """Safe stdout printer that prevents UnicodeEncodeError on Windows terminals."""
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


def upload_pdf_to_usal(
    file_source: Union[str, bytes, BinaryIO],
    filename: Optional[str] = None,
    email: str = "estudiante@usal.es",
    nombre: str = "Estudiante",
    apellidos: str = "Universidad",
    direccion: str = "Campus Unamuno, Salamanca",
    submit_form: bool = True,
    session: Optional[requests.Session] = None,
) -> Dict:
    """
    Uploads a PDF to digitalstack.usal.es/matricula Drupal form.
    Returns a dictionary with success status, live public URL, file ID, and details.
    
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
                filename = f"matricula_doc_{int(time.time())}.pdf"
            pdf_bytes = file_source
        else:
            # File-like object (Streamlit UploadedFile or BytesIO)
            if hasattr(file_source, "name") and not filename:
                filename = file_source.name
            if not filename:
                filename = f"matricula_doc_{int(time.time())}.pdf"
            if hasattr(file_source, "getvalue"):
                pdf_bytes = file_source.getvalue()
            else:
                pdf_bytes = file_source.read()

        # Sanitize filename
        clean_filename = re.sub(r'[\\/*?:"<>|\s]+', '_', filename)
        if not clean_filename.lower().endswith(".pdf"):
            clean_filename += ".pdf"

        headers = {
            "User-Agent": USER_AGENT,
            "Referer": FORM_URL,
            "Origin": "https://digitalstack.usal.es"
        }

        # Step 1: GET form page to obtain fresh form_build_id and ajax endpoint
        res = session.get(FORM_URL, headers=headers, timeout=30)
        if res.status_code != 200:
            return {
                "success": False,
                "error": f"Failed to fetch form page (HTTP {res.status_code})",
                "filename": clean_filename
            }

        soup = BeautifulSoup(res.text, "html.parser")
        form = soup.find("form", id="matriculas-node-form")
        if not form:
            return {
                "success": False,
                "error": "Could not find matricula form on page",
                "filename": clean_filename
            }

        form_build_id_elem = form.find("input", {"name": "form_build_id"})
        form_id_elem = form.find("input", {"name": "form_id"})

        if not form_build_id_elem or not form_id_elem:
            return {
                "success": False,
                "error": "Missing form_build_id or form_id hidden parameters",
                "filename": clean_filename
            }

        form_build_id = form_build_id_elem["value"]
        form_id = form_id_elem["value"]

        # Extract or construct AJAX URL
        ajax_urls = re.findall(r'/file/ajax/[^\s"\']+', res.text.replace('\\/', '/'))
        if ajax_urls:
            ajax_path = ajax_urls[0]
        else:
            ajax_path = f"/file/ajax/field_justificante_del_pago/und/0/{form_build_id}"

        ajax_url = f"https://digitalstack.usal.es{ajax_path}"

        # Step 2: Upload file via Drupal AJAX endpoint
        files = {
            "files[field_justificante_del_pago_und_0]": (clean_filename, pdf_bytes, "application/pdf")
        }
        data = {
            "form_build_id": form_build_id,
            "form_id": form_id,
            "_triggering_element_name": "field_justificante_del_pago_und_0_upload_button",
            "_triggering_element_value": "Upload",
            "_drupal_ajax": "1"
        }

        ajax_resp = session.post(ajax_url, headers=headers, data=data, files=files, timeout=45)
        if ajax_resp.status_code != 200:
            return {
                "success": False,
                "error": f"AJAX upload failed with HTTP {ajax_resp.status_code}",
                "filename": clean_filename
            }

        uploaded_url = None
        fid = None
        fid_token = None

        try:
            ajax_json = ajax_resp.json()
            for cmd in ajax_json:
                if cmd.get("command") == "insert":
                    data_html = cmd.get("data", "")
                    soup_data = BeautifulSoup(data_html, "html.parser")
                    a_tag = soup_data.find("a")
                    if a_tag and a_tag.get("href"):
                        uploaded_url = a_tag["href"]
                    fid_input = soup_data.find("input", {"name": "field_justificante_del_pago[und][0][fid]"})
                    if fid_input:
                        fid = fid_input.get("value")
                    fid_token_input = soup_data.find("input", {"name": "field_justificante_del_pago[und][0][fid_token]"})
                    if fid_token_input:
                        fid_token = fid_token_input.get("value")
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to parse Drupal AJAX response: {e}",
                "filename": clean_filename
            }

        if not uploaded_url:
            # Fallback URL construction if link tag not returned explicitly
            uploaded_url = f"{PUBLIC_BASE_URL}/{clean_filename}"

        form_submitted = False
        # Step 3: Complete form submission if requested
        if submit_form:
            title_str = f"Matricula_{clean_filename.rsplit('.', 1)[0]}_{random.randint(100, 999)}"
            save_data = {
                "title": title_str,
                "field_nombre[und][0][value]": nombre,
                "field_apellidos[und][0][value]": apellidos,
                "field_correo_electr_nico[und][0][value]": email,
                "field_direcci_n_postal[und][0][value]": direccion,
                "field_justificante_del_pago[und][0][fid]": fid if fid else "0",
                "field_justificante_del_pago[und][0][fid_token]": fid_token if fid_token else "",
                "field_justificante_del_pago[und][0][display]": "1",
                "changed": "",
                "form_build_id": form_build_id,
                "form_id": form_id,
                "additional_settings__active_tab": "",
                "op": "Save"
            }
            save_resp = session.post(FORM_URL, headers=headers, data=save_data, timeout=30)
            if save_resp.status_code == 200:
                form_submitted = True

        # Append link to local log file
        try:
            with open(OUTPUT_LINKS_FILE, "a", encoding="utf-8") as lf:
                lf.write(f"{uploaded_url}\n")
        except Exception:
            pass

        return {
            "success": True,
            "url": uploaded_url,
            "filename": clean_filename,
            "size": len(pdf_bytes),
            "fid": fid,
            "fid_token": fid_token,
            "form_submitted": form_submitted,
            "error": None
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
    email: str = "estudiante@usal.es",
    submit_form: bool = True
) -> List[Dict]:
    """
    Uploads multiple PDFs sequentially to USAL matricula form.
    Returns list of result dictionaries.
    """
    results = []
    total = len(files_list)
    print(f"[*] Starting USAL Matricula batch upload for {total} file(s)...")

    with requests.Session() as session:
        session.verify = False

        for idx, item in enumerate(files_list, 1):
            fname = filenames[idx - 1] if filenames and idx - 1 < len(filenames) else None
            print(f"[*] Uploading file ({idx}/{total}): {fname or 'PDF'}...")
            
            res = upload_pdf_to_usal(
                item,
                filename=fname,
                email=email,
                submit_form=submit_form,
                session=session
            )
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
            f.write(b"%PDF-1.4 sample pdf content for USAL matricula verification")

    print(f"[*] Running test upload for {test_pdf} to USAL Matricula...")
    result = upload_pdf_to_usal(test_pdf, filename="usal_matricula_doc.pdf")
    print("\nResult:")
    print(result)
