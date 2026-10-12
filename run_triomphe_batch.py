"""
Triomphe de l'Art Resume Batch Uploader script for files 369 to 749
Saves all generated public URLs in real-time to triomphe_urls_369_to_749.txt
"""

import os
import sys
import time
from triomphe_uploader import batch_upload_files

FOLDER = r"C:\Users\Admin\Downloads\converted_docs_to_pdfs (1)"
OUTPUT_FILE = r"c:\Users\Admin\Documents\edu\triomphe_urls_369_to_749.txt"
START_INDEX = 369

def main():
    if not os.path.exists(FOLDER):
        print(f"[-] Folder not found: {FOLDER}")
        return

    all_files = sorted([os.path.join(FOLDER, f) for f in os.listdir(FOLDER) if f.endswith(".pdf") or f.endswith(".zip")])
    total_files = len(all_files)
    print(f"[*] Found total {total_files} files in {FOLDER}")
    print(f"[*] TRIOMPHE DE L'ART: Resuming from file #{START_INDEX} up to #{total_files}...")

    with open(OUTPUT_FILE, "a", encoding="utf-8") as out:
        out.write(f"\n--- TRIOMPHE DE L'ART BATCH RESUME STARTED AT {time.strftime('%Y-%m-%d %H:%M:%S')} (Files {START_INDEX} to {total_files}) ---\n")

    ok_count = 0
    fail_count = 0

    for i, res in enumerate(batch_upload_files(all_files, start_index=START_INDEX), START_INDEX):
        status_str = "SUCCESS" if res["success"] else "FAILED"
        url_str = res.get("public_url") or res.get("error", "No URL")
        
        log_line = f"({i}/{total_files}) [{status_str}] {res['file_name']} -> {url_str}"
        print(log_line)

        with open(OUTPUT_FILE, "a", encoding="utf-8") as out:
            if res["success"] and res.get("public_url"):
                out.write(res["public_url"] + "\n")
                out.flush()
                ok_count += 1
            else:
                out.write(f"# FAILED: {res['file_name']} - {res.get('error')}\n")
                out.flush()
                fail_count += 1

    print("\n" + "="*60)
    print(f"[+] TRIOMPHE BATCH COMPLETE!")
    print(f"    Successful: {ok_count}")
    print(f"    Failed:     {fail_count}")
    print(f"    Output URL file: {OUTPUT_FILE}")
    print("="*60)

if __name__ == "__main__":
    main()
