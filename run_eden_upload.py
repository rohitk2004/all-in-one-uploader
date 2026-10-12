import sys
import os
from eden_uploader import upload_pdf_to_eden, batch_upload_pdfs, DEFAULT_JOB_URL, safe_print

print = safe_print

def main():
    print("=" * 60)
    print("🏨 [EDEN HOSPITALITY PDF UPLOADER BOT]")
    print(f"🎯 Target Form: {DEFAULT_JOB_URL}")
    print("=" * 60)

    if len(sys.argv) > 1:
        targets = sys.argv[1:]
        print(f"[*] Uploading provided file(s): {targets}")
        results = batch_upload_pdfs(targets)
    else:
        # Default test upload
        sample_file = "doc1.pdf"
        if not os.path.exists(sample_file):
            with open(sample_file, "wb") as f:
                f.write(b"%PDF-1.4 sample resume document for eden hospitality")
        print(f"[*] No file argument passed. Uploading sample file: {sample_file}...")
        res = upload_pdf_to_eden(sample_file, filename="dishwasher_application_resume.pdf")
        results = [res]

    print("\n" + "=" * 60)
    print("📋 [UPLOAD SUMMARY & LIVE URLS]")
    print("=" * 60)
    for r in results:
        if r.get("success"):
            print(f"✅ {r.get('filename')}: {r.get('url')}")
        else:
            print(f"❌ {r.get('filename')}: Error -> {r.get('error')}")

    print(f"\n[+] Saved to: eden_uploaded_links.txt")

if __name__ == "__main__":
    main()
